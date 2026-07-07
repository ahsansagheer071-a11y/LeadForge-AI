/**
 * Axios client — JWT Bearer interceptor + silent refresh support.
 *
 * - Single instance exposed as `apiClient`.
 * - Base URL is `/api/v1` (proxied to backend in dev via vite.config.ts).
 * - 401s trigger a one-time attempt to refresh using `/auth/refresh`.
 *   Concurrent 401s are queued and resolved once the refresh finishes.
 * - All errors are normalised through `extractApiError()`.
 */

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';
import { getErrorMessage } from '@/utils';
import type { APIErrorShape } from '@/types';

const RAW_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://leadforge-ai-production-eff1.up.railway.app';
// Strip any trailing slash, then ensure exactly one trailing `/api/v1`
const NORMALIZED_BASE = RAW_BASE_URL.replace(/\/+$/, '').replace(/\/api\/v1$/i, '');
const BASE_URL = `${NORMALIZED_BASE}/api/v1`;
console.log('API Base URL:', BASE_URL);
const ACCESS_KEY = 'lf_access_token';
const REFRESH_KEY = 'lf_refresh_token';

export const tokenStorage = {
  getAccess: () => (typeof localStorage !== 'undefined' ? localStorage.getItem(ACCESS_KEY) : null),
  getRefresh: () => (typeof localStorage !== 'undefined' ? localStorage.getItem(REFRESH_KEY) : null),
  setTokens: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Normalised API error — never throws raw AxiosError to callers.
 *
 * Backend error shape: { success: false, error: { code, message, detail } }
 * Validation errors:   { success: false, error: { code, message, detail: [...] } }
 */
export function extractApiError(err: unknown): APIErrorShape {
  const ax = err as AxiosError<Record<string, unknown>>;
  if (ax?.isAxiosError) {
    const status = ax.response?.status ?? 0;
    const data = ax.response?.data;
    const errBlock =
      data && typeof data === 'object' && 'error' in data
        ? (data.error as Record<string, unknown>)
        : null;
    const message =
      (errBlock && typeof errBlock.message === 'string' && errBlock.message) ||
      (data && typeof data.message === 'string' && (data.message as string)) ||
      (data && typeof data.detail === 'string' && (data.detail as string)) ||
      ax.message ||
      'Request failed';
    const code =
      (errBlock && typeof errBlock.code === 'string' ? (errBlock.code as string) : null) ||
      (data && typeof data.code === 'string' ? (data.code as string) : null) ||
      (status === 401 ? 'unauthorized' : status === 403 ? 'forbidden' : status === 404 ? 'not_found' : null);
    return { status, code, message, details: data ?? null };
  }
  return { status: 0, code: 'network', message: getErrorMessage(err) };
}

/** Global error sink — wired up by providers; safe to call from anywhere. */
type ErrorSink = (e: APIErrorShape) => void;
let _sink: ErrorSink | null = null;
export const setGlobalErrorSink = (fn: ErrorSink | null) => {
  _sink = fn;
};

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  timeout: 30_000,
  withCredentials: false,
});

// ─── Request interceptor — attach Bearer token ────────────────
apiClient.interceptors.request.use((cfg: InternalAxiosRequestConfig) => {
  const tok = tokenStorage.getAccess();
  if (tok) cfg.headers.Authorization = `Bearer ${tok}`;
  return cfg;
});

// ─── Response interceptor — silent refresh + error normalisation
let refreshing: Promise<string> | null = null;

async function performRefresh(): Promise<string> {
  if (refreshing) return refreshing;
  refreshing = (async () => {
    const refresh = tokenStorage.getRefresh();
    if (!refresh) throw new Error('no_refresh_token');
    // bare axios.post avoids recursive interceptor
    const resp = await axios.post(
      `${BASE_URL}/auth/refresh`,
      { refresh_token: refresh },
      { headers: { 'Content-Type': 'application/json' }, timeout: 15_000 },
    );
    const access = (resp.data as { access_token?: string }).access_token;
    const newRefresh = (resp.data as { refresh_token?: string }).refresh_token ?? refresh;
    if (!access) throw new Error('refresh_returned_no_token');
    tokenStorage.setTokens(access, newRefresh);
    apiClient.defaults.headers.common.Authorization = `Bearer ${access}`;
    return access;
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

declare module 'axios' {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean;
    _silent?: boolean;
  }
}

apiClient.interceptors.response.use(
  (resp: AxiosResponse) => resp,
  async (error: AxiosError) => {
    const cfg = (error.config ?? {}) as InternalAxiosRequestConfig;
    const isAuthEndpoint = cfg.url?.includes('/auth/');
    const shouldTryRefresh =
      error.response?.status === 401 && !cfg._retry && !cfg._silent && !isAuthEndpoint;

    if (shouldTryRefresh) {
      cfg._retry = true;
      try {
        const newToken = await performRefresh();
        if (cfg.headers) cfg.headers.Authorization = `Bearer ${newToken}`;
        return apiClient(cfg);
      } catch (refreshErr) {
        tokenStorage.clear();
        const apiErr = extractApiError(refreshErr);
        if (_sink) _sink(apiErr);
        if (typeof window !== 'undefined' && window.location?.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(apiErr);
      }
    }

    const apiErr = extractApiError(error);
    return Promise.reject(apiErr);
  },
);

export default apiClient;
