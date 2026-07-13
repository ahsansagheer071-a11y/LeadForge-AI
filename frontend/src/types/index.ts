/**
 * Domain & generic Types for LeadForge AI frontend shell.
 * Everything here is UI / type-level only — no actual API calls live here.
 */

export type UUID = string;
export type ISODate = string;

/* ─── Auth ──────────────────────────────────────────────────── */
export interface User {
  id: UUID;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  role?: 'owner' | 'admin' | 'member' | null;
  created_at?: ISODate;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type?: string;
  expires_in?: number;
}

/* ─── Project ──────────────────────────────────────────────── */
export type ProjectStatus =
  | 'draft'
  | 'queued'
  | 'generating'
  | 'previewing'
  | 'deployed'
  | 'failed'
  | 'archived';

export interface Project {
  id: UUID;
  name: string;
  domain?: string | null;
  description?: string | null;
  status: ProjectStatus;
  thumbnail_url?: string | null;
  created_at: ISODate;
  updated_at: ISODate;
  owner?: User | null;
  tags?: string[];
  lead_score?: number | null;
}

/* ─── Preview ──────────────────────────────────────────────── */
export interface PreviewInfo {
  url: string;
  port?: number;
  pid?: number | null;
  status: 'starting' | 'ready' | 'reloading' | 'stopped' | 'error';
  health_check?: 'good' | 'degraded' | 'slow' | 'unknown';
  startup_time?: number;
}

/* ─── Deployment ───────────────────────────────────────────── */
export type DeploymentProvider = 'vercel' | 'netlify' | 'aws' | 'gcp' | 'azure' | 'self-hosted';

export interface DeploymentInfo {
  id: UUID;
  project_id: UUID;
  provider: DeploymentProvider;
  status: 'pending' | 'building' | 'live' | 'failed' | 'rolled-back';
  url?: string | null;
  created_at: ISODate;
}

export interface DashboardSummaryResponse {
  total_leads: number;
  new_leads: number;
  audited_leads: number;
  outreach_generated: number;
  average_lead_score: number;
  high_priority_leads: number;
}

export interface DistributionItem {
  label: string;
  count: number;
}

export interface DistributionResponse {
  total: number;
  distribution: DistributionItem[];
}

export interface RecentLeadsResponse {
  total: number;
  limit: number;
  offset: number;
  leads: Array<{
    id: UUID;
    name: string;
    industry: string;
    city: string;
    country: string;
    status: string;
    rating?: number | null;
    created_at: ISODate;
  }>;
}

/* ─── Notifications ────────────────────────────────────────── */
export type NotificationKind = 'info' | 'success' | 'warning' | 'error';
export interface AppNotification {
  id: UUID;
  kind: NotificationKind;
  title: string;
  message?: string;
  created_at: ISODate;
  read: boolean;
}

/* ─── Generic API errors ────────────────────────────────────── */
export interface APIErrorShape {
  status: number;
  code?: string | null;
  category?: 'validation' | 'authentication' | 'authorization' | 'network' | 'timeout' | 'backend' | 'provider' | 'unknown';
  message: string;
  details?: Record<string, unknown> | null;
}

/* ─── UI primitives ────────────────────────────────────────── */
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type Tone = 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted';

/* ─── Pagination ──────────────────────────────────────────── */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/* ─── Leads / Projects ────────────────────────────────────── */
export interface LeadResponse {
  id: UUID;
  user_id: UUID;
  name: string;
  website?: string | null;
  phone?: string | null;
  address?: string | null;
  rating?: number | null;
  reviews_count?: number | null;
  maps_url?: string | null;
  city: string;
  country: string;
  industry: string;
  status: string;
  created_at: ISODate;
  updated_at: ISODate;
}

export interface LeadScoreResponse {
  id: UUID;
  lead_id: UUID;
  overall_score: number;
  seo_score: number;
  ux_score: number;
  branding_score: number;
  trust_score: number;
  conversion_score: number;
  category: string;
  explanation?: string | null;
  created_at: ISODate;
  updated_at: ISODate;
}

export interface AuditResponse {
  id: UUID;
  lead_id: UUID;
  executive_summary?: string | null;
  verdict?: string | null;
  website_title?: string | null;
  meta_description?: string | null;
  emails?: string[];
  phone_numbers?: string[];
  contact_form_present?: boolean;
  social_links?: string[];
  technologies?: string[];
  ssl_status?: boolean;
  weaknesses?: string[] | null;
  created_at: ISODate;
  updated_at: ISODate;
}

export interface ScreenshotResponse {
  id: UUID;
  lead_id: UUID;
  desktop_cloudinary_url?: string | null;
  mobile_cloudinary_url?: string | null;
  full_page_cloudinary_url?: string | null;
  created_at: ISODate;
}

export interface OutreachResponse {
  id: UUID;
  lead_id: UUID;
  email_subject?: string | null;
  cold_email?: string | null;
  followup_email?: string | null;
  linkedin_message?: string | null;
  whatsapp_message?: string | null;
  short_cta?: string | null;
  created_at: ISODate;
  updated_at?: ISODate;
}

export interface GenerateOutreachRequest {
  lead_id: UUID;
  provider?: string;
}

export interface LeadDetailResponse extends LeadResponse {
  score?: LeadScoreResponse | null;
  audit?: AuditResponse | null;
  screenshot?: ScreenshotResponse | null;
  outreach?: OutreachResponse | null;
}

/* ─── Lead Discovery ──────────────────────────────────────── */
export interface LeadDiscoveryRequest {
  business_type: string;
  city: string;
  country: string;
}

export interface LeadDiscoveryResponse {
  total_found: number;
  created: number;
  skipped_duplicates: number;
  leads: LeadResponse[];
}

/* ─── Screenshot Capture ───────────────────────────────────── */
export interface CaptureScreenshotRequest {
  lead_id: UUID;
}

export interface CaptureScreenshotResponse {
  lead_id: UUID;
  desktop_url?: string | null;
  mobile_url?: string | null;
  full_page_url?: string | null;
}

/* ─── Website Analysis ─────────────────────────────────────── */
export interface WebsiteAnalysisRequest {
  lead_id: UUID;
}

export interface WebsiteAnalysisResponse {
  lead_id: UUID;
  website_url: string;

  page_title?: string | null;
  meta_description?: string | null;
  website_language?: string | null;
  https_enabled: boolean;
  http_status_code?: number | null;

  h1_count: number;
  h2_count: number;
  total_paragraphs: number;
  total_images: number;
  total_forms: number;

  emails: string[];
  phone_numbers: string[];

  contact_page_exists: boolean;
  about_page_exists: boolean;

  social_facebook?: string | null;
  social_instagram?: string | null;
  social_linkedin?: string | null;
  social_twitter?: string | null;
  social_youtube?: string | null;

  missing_meta_description: boolean;
  missing_h1: boolean;
  missing_title: boolean;

  html_size_kb?: number | null;
  response_time_ms?: number | null;
}

/* ─── Generated Website ───────────────────────────────────── */
export interface GeneratedWebsiteResponse {
  id: UUID;
  lead_id: UUID;
  generation_id: string;
  project_name?: string | null;
  framework: string;
  status: string;
  html: string;
  preview_path: string;
  package_id?: string | null;
  package_metadata: Record<string, unknown>;
  build_metadata: Record<string, unknown>;
  created_at: ISODate;
  updated_at: ISODate;
}

/* ─── Audit ─────────────────────────────────────────────────── */
export interface AuditRequest {
  lead_id: UUID;
  provider?: string;
}

export interface AuditAndScoreResult {
  lead_id: UUID;
  audit: Record<string, unknown>;
  score: LeadScoreResponse;
}

