/**
 * Auth store (Zustand).
 *
 * Replaces Phase 6.1 stubs with real async actions that hit the
 * backend API.  Tokens are stored to / read from tokenStorage
 * (localStorage keys lf_access_token / lf_refresh_token) so the
 * Axios interceptor can attach them automatically.
 *
 * The persist middleware saves { user, isAuthenticated } to
 * localStorage under "lf_auth_v1" so checkAuth() can skip /me
 * on rehydrate for instant route-gate rendering.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AuthTokens, User } from '@/types';
import { tokenStorage } from '@/services/apiClient';
import {
  loginUser,
  registerUser,
  logoutUser,
  fetchMe,
} from '@/services/services';
import { getErrorMessage } from '@/utils';

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  initialised: boolean;           // true after checkAuth() completes at startup

  setUser: (u: User | null) => void;
  setTokens: (t: AuthTokens | null) => void;

  /** Real async login — calls /auth/login then /auth/me */
  login: (email: string, password: string) => Promise<void>;
  /** Real async register — calls /auth/register (no auto-login) */
  register: (email: string, password: string, full_name: string) => Promise<void>;
  /** Real async logout — calls /auth/logout then clears state */
  logout: () => Promise<void>;
  /** Called once at app startup — verifies stored token via /me */
  checkAuth: () => Promise<boolean>;
  /** Reset loading / error */
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      /* ── State ─────────────────────────────────────────── */
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      initialised: false,

      /* ── Setters (used internally) ──────────────────────── */
      setUser: (u) => set({ user: u, isAuthenticated: !!u }),
      setTokens: (t) => {
        if (t) tokenStorage.setTokens(t.access_token, t.refresh_token);
        else tokenStorage.clear();
        set({ tokens: t });
      },

      /* ── Login ──────────────────────────────────────────── */
      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const tokens = await loginUser(email, password);
          tokenStorage.setTokens(tokens.access_token, tokens.refresh_token);
          set({ tokens, isAuthenticated: true });

          // Fetch full user profile from /me
          const user = await fetchMe();
          set({ user, isLoading: false, error: null });
        } catch (err) {
          tokenStorage.clear();
          set({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: getErrorMessage(err),
          });
          throw err;
        }
      },

      /* ── Register ─────────────────────────────────────────
       * Backend returns { success, message, data: UserResponse }
       * with NO tokens — so we do NOT auto-login. Redirect to
       * /login after successful registration.                    */
      register: async (email, password, full_name) => {
        set({ isLoading: true, error: null });
        try {
          await registerUser(email, password, full_name);
          set({ isLoading: false, error: null });
        } catch (err) {
          set({ isLoading: false, error: getErrorMessage(err) });
          throw err;
        }
      },

      /* ── Logout ─────────────────────────────────────────── */
      logout: async () => {
        try {
          await logoutUser();
        } catch {
          // Even if the revoke call fails, clear local state
        }
        tokenStorage.clear();
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      },

      /* ── checkAuth ────────────────────────────────────────
       * Called once on app mount. If a token exists in storage,
       * validates it by calling /me. Updates isAuthenticated.  */
      checkAuth: async () => {
        const access = tokenStorage.getAccess();
        if (!access) {
          set({ initialised: true, isAuthenticated: false, user: null });
          return false;
        }
        try {
          const user = await fetchMe();
          set({ user, isAuthenticated: true, initialised: true });
          return true;
        } catch {
          tokenStorage.clear();
          set({ user: null, tokens: null, isAuthenticated: false, initialised: true });
          return false;
        }
      },

      /* ── Clear error ────────────────────────────────────── */
      clearError: () => set({ error: null }),
    }),
    {
      name: 'lf_auth_v1',
      storage: createJSONStorage(() => localStorage),
      // Only persist user + isAuthenticated (tokens are in tokenStorage)
      partialize: (s) => ({ user: s.user, isAuthenticated: s.isAuthenticated }),
      // On rehydrate, mark initialised = true so routes aren't stuck
      onRehydrateStorage: () => (state) => {
        if (state) state.initialised = true;
      },
    },
  ),
);
