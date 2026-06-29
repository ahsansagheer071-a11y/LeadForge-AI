// ─────────────────────────────────────────────────────────
// All TypeScript types derived directly from backend schemas
// Backend: app/schemas/ → Frontend: src/types/index.ts
// ─────────────────────────────────────────────────────────

// ── Generic wrappers ────────────────────────────────────
export interface StandardResponse<T> {
  success: boolean
  message: string
  data: T | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

// ── Auth / User ──────────────────────────────────────────
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string | null
  company_name: string | null
  phone: string | null
  avatar_url: string | null
  timezone: string | null
  country: string | null
  is_active: boolean
  is_superuser: boolean
  role: string
  created_at: string
  updated_at: string
}

export interface UserProfileUpdate {
  full_name?: string
  company_name?: string
  phone?: string
  avatar_url?: string
  timezone?: string
  country?: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

// ── Lead ─────────────────────────────────────────────────
export type LeadStatus =
  | 'NEW'
  | 'SCRAPED'
  | 'ANALYZED'
  | 'OUTREACH_READY'
  | 'CONTACTED'
  | 'CLOSED'

export interface LeadResponse {
  id: string
  name: string
  website: string | null
  phone: string | null
  address: string | null
  rating: number | null
  reviews_count: number | null
  maps_url: string | null
  city: string
  country: string
  industry: string
  status: LeadStatus
  user_id: string
  created_at: string
  updated_at: string
}

export interface LeadDetailResponse extends LeadResponse {
  score: LeadScoreResponse | null
  audit: AuditResponse | null
  screenshot: ScreenshotResponse | null
  outreach: OutreachResponse | null
}

export interface LeadUpdate {
  name?: string
  website?: string
  phone?: string
  address?: string
  rating?: number
  reviews_count?: number
  maps_url?: string
  city?: string
  country?: string
  industry?: string
  status?: LeadStatus
}

export interface LeadDiscoveryRequest {
  business_type: string
  city: string
  country: string
}

export interface LeadDiscoveryResponse {
  total_found: number
  created: number
  skipped_duplicates: number
  leads: LeadResponse[]
}

export interface BulkDeleteRequest {
  lead_ids: string[]
}

export interface BulkStatusUpdateRequest {
  lead_ids: string[]
  status: LeadStatus
}

export interface BulkActionResponse {
  processed: number
  not_found: number
  lead_ids: string[]
}

// ── Lead Score ────────────────────────────────────────────
export interface LeadScoreResponse {
  id: string
  lead_id: string
  overall_score: number
  seo_score: number
  ux_score: number
  branding_score: number
  trust_score: number
  conversion_score: number
  category: string
  explanation: string | null
  created_at: string
  updated_at: string
}

export interface WeaknessItem {
  title: string
  evidence: string
  impact: string
  recommendation: string
}

// ── Screenshot ───────────────────────────────────────────
export interface ScreenshotResponse {
  id: string
  lead_id: string
  desktop_cloudinary_url: string | null
  mobile_cloudinary_url: string | null
  full_page_cloudinary_url: string | null
  created_at: string
  updated_at: string
}

// ── Audit ─────────────────────────────────────────────────
export interface AuditResponse {
  id: string
  lead_id: string
  executive_summary: string | null
  weaknesses: WeaknessItem[] | null
  verdict: string | null
  website_title: string | null
  meta_description: string | null
  emails: string[] | null
  phone_numbers: string[] | null
  contact_form_present: boolean
  social_links: string[] | null
  technologies: string[] | null
  ssl_status: boolean
  testimonials_present: boolean
  faq_present: boolean
  website_language: string | null
  https_enabled: boolean
  http_status_code: number | null
  h1_count: number
  h2_count: number
  total_paragraphs: number
  total_images: number
  total_forms: number
  contact_page_exists: boolean
  about_page_exists: boolean
  social_facebook: string | null
  social_instagram: string | null
  social_linkedin: string | null
  social_twitter: string | null
  social_youtube: string | null
  missing_meta_description: boolean
  missing_h1: boolean
  missing_title: boolean
  html_size_kb: number | null
  response_time_ms: number | null
  created_at: string
  updated_at: string
}

// ── Outreach ──────────────────────────────────────────────
export interface OutreachResponse {
  id: string
  lead_id: string
  email_subject: string | null
  cold_email: string | null
  linkedin_message: string | null
  followup_email: string | null
  short_cta: string | null
  created_at: string
  updated_at: string
}

// ── Website Analysis ──────────────────────────────────────
export interface WebsiteAnalysisResponse {
  lead_id: string
  website_url: string
  page_title: string | null
  meta_description: string | null
  website_language: string | null
  https_enabled: boolean
  http_status_code: number | null
  h1_count: number
  h2_count: number
  total_paragraphs: number
  total_images: number
  total_forms: number
  emails: string[]
  phone_numbers: string[]
  contact_page_exists: boolean
  about_page_exists: boolean
  missing_meta_description: boolean
  missing_h1: boolean
  missing_title: boolean
  response_time_ms: number | null
  html_size_kb: number | null
}

export interface AuditRunResponse {
  lead_id: string
  audit: Record<string, unknown>
  score: LeadScoreResponse
}

// ── Dashboard ─────────────────────────────────────────────
export interface DashboardSummaryResponse {
  total_leads: number
  new_leads: number
  audited_leads: number
  outreach_generated: number
  average_lead_score: number
  high_priority_leads: number
}

export interface DistributionItem {
  label: string
  count: number
}

export interface DistributionResponse {
  total: number
  distribution: DistributionItem[]
}

export interface RecentLeadItem {
  id: string
  name: string
  industry: string
  city: string
  country: string
  status: LeadStatus
  rating: number | null
  created_at: string
}

export interface RecentLeadsResponse {
  total: number
  limit: number
  offset: number
  leads: RecentLeadItem[]
}

// ── Settings / Preferences ────────────────────────────────
export interface UserSettingsResponse {
  id: string
  user_id: string
  cloudinary_cloud_name: string | null
  cloudinary_api_key: string | null
  gemini_api_key_set: boolean
  serpapi_key_set: boolean
  cloudinary_api_secret_set: boolean
  theme: string
  email_notifications: boolean
  default_page_size: number
  default_sorting: string
  language: string
  created_at: string
  updated_at: string
}

export interface UserPreferencesUpdate {
  theme?: string
  email_notifications?: boolean
  default_page_size?: number
  default_sorting?: string
  language?: string
}

export interface AccountSummaryResponse {
  user_info: UserResponse
  total_leads: number
  total_audits: number
  total_outreach: number
  account_created_at: string
}

// ── Lead Filters (frontend state shape) ──────────────────
export interface LeadFilters {
  page: number
  limit: number
  name?: string
  city?: string
  country?: string
  status?: string
  category?: string
  min_score?: number
  max_score?: number
  sort_by: string
  sort_order: 'asc' | 'desc'
}
