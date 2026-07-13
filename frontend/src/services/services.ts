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
  DashboardSummaryResponse,
  DistributionResponse,
  RecentLeadsResponse,
  GeneratedWebsiteResponse,
} from '@/types';

/* ─── Auth helpers ────────────────────────────────────────── */
function unwrap<T>(resp: { data: { success: boolean; data?: T | null; message?: string; error?: { message?: string; code?: string } } }): T {
  if (!resp.data.success || resp.data.data == null) {
    throw {
      status: 0,
      code: resp.data.error?.code ?? 'api_unsuccessful_response',
      category: 'backend',
      message: resp.data.error?.message ?? resp.data.message ?? 'The backend did not return a usable result.',
      details: resp.data as Record<string, unknown>,
    };
  }
  return resp.data.data;
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
      params: { page, limit: pageSize },
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
    const resp = await apiClient.post<{ success: boolean; data: LeadResponse }>('/leads', {
      company_name: input.name,
      url: input.website,
      phone: input.phone,
      address: input.address,
      city: input.city,
      country: input.country,
      industry: input.industry,
    });
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
      { timeout: 120_000 },
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
    const resp = await apiClient.post<{ success: boolean; data: AuditAndScoreResult }>('/audits/run', payload, {
      timeout: 300_000,
    });
    return unwrap(resp);
  },
};

/* ─── Outreach service ────────────────────────────────────────── */
export const outreachService = {
  async generate(payload: GenerateOutreachRequest): Promise<OutreachResponse> {
    const resp = await apiClient.post<{ success: boolean; data: OutreachResponse }>(
      '/outreach/generate',
      payload,
      { timeout: 180_000 },
    );
    return unwrap(resp);
  },
};

/* ─── Dashboard service ───────────────────────────────────── */
export const dashboardService = {
  async summary(): Promise<DashboardSummaryResponse> {
    const resp = await apiClient.get<{ success: boolean; data: DashboardSummaryResponse }>('/dashboard/summary');
    return unwrap(resp);
  },
  async recentLeads(limit = 10, offset = 0): Promise<RecentLeadsResponse> {
    const resp = await apiClient.get<{ success: boolean; data: RecentLeadsResponse }>('/dashboard/recent-leads', {
      params: { limit, offset },
    });
    return unwrap(resp);
  },
  async statusDistribution(): Promise<DistributionResponse> {
    const resp = await apiClient.get<{ success: boolean; data: DistributionResponse }>('/dashboard/status-distribution');
    return unwrap(resp);
  },
};

/* ─── Generation service ────────────────────────────────────── */
export type JobStatus = 'pending' | 'running' | 'succeeded' | 'failed';

export interface GenerationJobResult {
  job_id: string;
  lead_id: string;
  status: JobStatus;
  progress: string;
  website_id?: string | null;
  generation_id?: string | null;
  html?: string | null;
  preview_path?: string | null;
  package_id?: string | null;
  project_name?: string | null;
  generation_time: number;
  error?: string | null;
}

/** Submit an async generation job. Returns immediately with a job_id. */
export async function createGenerationJob(leadId: string): Promise<{ job_id: string; status: JobStatus }> {
  const resp = await apiClient.post<{ success: boolean; data: { job_id: string; status: JobStatus } }>(
    '/generation/jobs',
    { lead_id: leadId },
    { timeout: 15_000 },
  );
  return unwrap(resp);
}

/** Poll a generation job for its current status and result. */
export async function pollGenerationJob(jobId: string): Promise<GenerationJobResult> {
  const resp = await apiClient.get<{ success: boolean; data: GenerationJobResult }>(
    `/generation/jobs/${jobId}`,
    { timeout: 10_000 },
  );
  return unwrap(resp);
}

export const generationService = {
  async getById(websiteId: string): Promise<GeneratedWebsiteResponse> {
    const resp = await apiClient.get<{ success: boolean; data: GeneratedWebsiteResponse }>(
      `/generation/websites/${websiteId}`,
    );
    return unwrap(resp);
  },
  async getLatestByLeadId(leadId: string): Promise<GeneratedWebsiteResponse> {
    const resp = await apiClient.get<{ success: boolean; data: GeneratedWebsiteResponse }>(
      `/generation/leads/${leadId}/latest`,
    );
    return unwrap(resp);
  },
  async downloadPackage(websiteId: string): Promise<void> {
    const resp = await apiClient.get<Blob>(
      `/generation/websites/${websiteId}/download`,
      { responseType: 'blob' },
    );
    const contentDisposition = resp.headers?.['content-disposition'] as string | undefined;
    const match = contentDisposition?.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] ?? `leadforge-website-${websiteId}.zip`;
    const blob = new Blob([resp.data]);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
