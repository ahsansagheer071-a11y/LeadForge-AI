import apiClient from './apiClient';
import type {
  AuthTokens,
  User,
  LeadResponse,
  LeadDetailResponse,
  LeadDiscoveryRequest,
  LeadDiscoveryResponse,
  PaginatedResponse,
  AuditRequest,
  AuditAndScoreResult,
  WebsiteAnalysisResponse,
  CaptureScreenshotRequest,
  CaptureScreenshotResponse,
  GenerateOutreachRequest,
  OutreachResponse,
} from '@/types';

/* ─── Auth helpers ────────────────────────────────────────── */
function unwrap<T>(resp: { data: { success: boolean; data?: T } }): T {
  return resp.data.data as T;
}

/* ─── Auth service ──────────────────────────────────────────── */
export async function loginUser(email: string, password: string): Promise<AuthTokens> {
  const params = new URLSearchParams({ username: email, password });
  const resp = await apiClient.post<AuthTokens>('/auth/login', params.toString(), {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return resp.data;
}

export async function registerUser(email: string, password: string, full_name: string): Promise<User> {
  const resp = await apiClient.post<{ success: boolean; data: User }>('/auth/register', { email, password, full_name });
  return unwrap(resp);
}

export async function refreshTokens(refresh_token: string): Promise<AuthTokens> {
  const resp = await apiClient.post<AuthTokens>('/auth/refresh', { refresh_token });
  return resp.data;
}

export async function logoutUser(): Promise<void> {
  await apiClient.post('/auth/logout');
}

export async function fetchMe(): Promise<User> {
  const resp = await apiClient.get<{ success: boolean; data: User }>('/auth/me');
  return unwrap(resp);
}

/* ─── Projects / Leads service ──────────────────────────────── */
export const projectsService = {
  async list(page = 1, pageSize = 20): Promise<PaginatedResponse<LeadResponse>> {
    const resp = await apiClient.get<{ success: boolean; data: PaginatedResponse<LeadResponse> }>('/leads', {
      params: { page, page_size: pageSize },
    });
    return unwrap(resp);
  },
  async getById(id: string): Promise<LeadDetailResponse | null> {
    try {
      const resp = await apiClient.get<{ success: boolean; data: LeadDetailResponse }>(`/leads/${id}`);
      return unwrap(resp);
    } catch (err) {
      const ax = err as { status?: number };
      if (ax.status === 404) return null;
      throw err;
    }
  },
  async create(input: {
    name: string; website?: string; phone?: string;
    address?: string; city: string; country: string; industry: string;
  }): Promise<LeadResponse> {
    const resp = await apiClient.post<{ success: boolean; data: LeadResponse }>('/leads', input);
    return unwrap(resp);
  },
  async delete(id: string): Promise<void> {
    await apiClient.delete(`/leads/${id}`);
  },
};

/* ─── Lead Discovery service ────────────────────────────────── */
export const leadDiscoveryService = {
  async discover(payload: LeadDiscoveryRequest): Promise<LeadDiscoveryResponse> {
    const resp = await apiClient.post<{ success: boolean; data: LeadDiscoveryResponse }>('/leads/discover', payload);
    return unwrap(resp);
  },
};

/* ─── Screenshot service ──────────────────────────────────────── */
export const screenshotService = {
  async capture(payload: CaptureScreenshotRequest): Promise<CaptureScreenshotResponse> {
    const resp = await apiClient.post<{ success: boolean; data: CaptureScreenshotResponse }>(
      '/screenshots/capture',
      payload,
    );
    return unwrap(resp);
  },
};

/* ─── Website Analysis service ───────────────────────────────── */
export const analysisService = {
  async analyzeWebsite(leadId: string): Promise<WebsiteAnalysisResponse> {
    const resp = await apiClient.post<{ success: boolean; data: WebsiteAnalysisResponse }>(
      '/analysis/website',
      { lead_id: leadId },
    );
    return unwrap(resp);
  },
};

/* ─── Audit service ──────────────────────────────────────────── */
export const auditService = {
  async run(payload: AuditRequest): Promise<AuditAndScoreResult> {
    const resp = await apiClient.post<{ success: boolean; data: AuditAndScoreResult }>('/audits/run', payload);
    return unwrap(resp);
  },
};

/* ─── Outreach service ────────────────────────────────────────── */
export const outreachService = {
  async generate(payload: GenerateOutreachRequest): Promise<OutreachResponse> {
    const resp = await apiClient.post<{ success: boolean; data: OutreachResponse }>(
      '/outreach/generate',
      payload,
    );
    return unwrap(resp);
  },
};

/* ─── Deployment service (stub — future phase) ─────────────── */
import type { DeploymentInfo } from '@/types';

export const deploymentsService = {
  async list(): Promise<DeploymentInfo[]> {
    return [];
  },
};

/* ─── Generation service ────────────────────────────────────── */
export async function generateWebsite(leadId: string): Promise<string> {
  const resp = await apiClient.post<{ success: boolean; data: { html: string } }>(
    '/generation/generate',
    { lead_id: leadId },
  );
  return unwrap(resp).html;
}


