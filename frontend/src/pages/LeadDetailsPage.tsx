import { useState, useEffect, useCallback, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  Globe,
  Phone,
  MapPin,
  Star,
  ExternalLink,
  Camera,
  Bot,
  MessageSquare,
  Loader,
  RefreshCw,
  Trash2,
  Copy,
  Check,
  Building2,
  Mail,
  Shield,
  Gauge,
  Zap,
  Users,
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Target,
  Lightbulb,
  FileText,
  Clock,
  Search,
  ImageIcon,
  X,
  Share2,
} from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { analysisApi, screenshotsApi, auditsApi, outreachApi } from '@/services/apiServices'
import { queryKeys, formatDate, formatDateRelative, scoreColour, getErrorMessage, type ToastState } from '@/utils'
import PremiumCard from '@/components/PremiumCard'
import { statusPillClass, ScoreBadge } from '@/components/LeadPreviewDrawer'
import type { AuditResponse, LeadDetailResponse, LeadScoreResponse, WeaknessItem } from '@/types'
import '@/styles/dashboard.css'
import '@/styles/leads.css'
import '@/styles/lead-details.css'

type Tab = 'overview' | 'analysis' | 'screenshots' | 'audit' | 'outreach' | 'timeline'

const TABS: { id: Tab; label: string }[] = [
  { id: 'overview', label: 'Overview' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'screenshots', label: 'Screenshots' },
  { id: 'audit', label: 'Audit' },
  { id: 'outreach', label: 'Outreach' },
  { id: 'timeline', label: 'Timeline' },
]

function faviconUrl(website: string | null): string | null {
  if (!website) return null
  try {
    const host = new URL(website.startsWith('http') ? website : `https://${website}`).hostname
    return `https://www.google.com/s2/favicons?domain=${host}&sz=64`
  } catch {
    return null
  }
}

function deriveStrengths(audit: AuditResponse | null, score: LeadScoreResponse | null): string[] {
  const items: string[] = []
  if (!audit && !score) return items
  if (audit?.https_enabled) items.push('Secure HTTPS connection enabled')
  if (audit?.ssl_status) items.push('Valid SSL certificate detected')
  if (audit?.contact_page_exists) items.push('Dedicated contact page found')
  if (audit?.about_page_exists) items.push('About page supports brand credibility')
  if (audit?.testimonials_present) items.push('Customer testimonials present on site')
  if (audit?.faq_present) items.push('FAQ section addresses common buyer questions')
  if (audit?.contact_form_present) items.push('Contact form available for lead capture')
  if (audit && !audit.missing_meta_description && audit.meta_description) {
    items.push('Meta description configured for search visibility')
  }
  if (audit && audit.h1_count > 0 && !audit.missing_h1) items.push('Proper H1 heading structure in place')
  if (score) {
    const dims: [string, number][] = [
      ['SEO', score.seo_score],
      ['UX', score.ux_score],
      ['Branding', score.branding_score],
      ['Trust', score.trust_score],
      ['Conversion', score.conversion_score],
    ]
    dims.filter(([, v]) => v >= 75).forEach(([label, v]) => {
      items.push(`Strong ${label} performance (score: ${Math.round(v)})`)
    })
  }
  return items
}

function deriveOpportunities(weaknesses: WeaknessItem[] | null | undefined, verdict: string | null): string[] {
  const items = weaknesses?.map((w) => w.recommendation).filter(Boolean) ?? []
  if (verdict && items.length === 0) return [verdict]
  return items.slice(0, 8)
}

function deriveThreats(weaknesses: WeaknessItem[] | null | undefined): string[] {
  return (
    weaknesses?.map((w) => (w.impact ? `${w.title}: ${w.impact}` : w.title)).filter(Boolean).slice(0, 6) ?? []
  )
}

function deriveRecommendations(
  weaknesses: WeaknessItem[] | null | undefined,
  score: LeadScoreResponse | null,
): string[] {
  const fromWeakness = weaknesses?.map((w) => w.recommendation).filter(Boolean) ?? []
  if (fromWeakness.length > 0) return [...new Set(fromWeakness)].slice(0, 6)
  if (score?.explanation) return [score.explanation]
  return []
}

function perfLabel(ms: number | null | undefined): { label: string; pct: number; status: 'good' | 'warn' | 'bad' } {
  if (ms == null) return { label: 'Unknown', pct: 0, status: 'warn' }
  if (ms < 1500) return { label: 'Fast', pct: 90, status: 'good' }
  if (ms < 3000) return { label: 'Moderate', pct: 55, status: 'warn' }
  return { label: 'Slow', pct: 25, status: 'bad' }
}

function seoLabel(audit: AuditResponse | null, score: LeadScoreResponse | null): { label: string; pct: number; status: 'good' | 'warn' | 'bad' } {
  if (score) {
    const s = score.seo_score
    if (s >= 75) return { label: 'Strong', pct: s, status: 'good' }
    if (s >= 50) return { label: 'Fair', pct: s, status: 'warn' }
    return { label: 'Needs work', pct: s, status: 'bad' }
  }
  if (!audit) return { label: 'Not analyzed', pct: 0, status: 'warn' }
  const issues = [audit.missing_title, audit.missing_h1, audit.missing_meta_description].filter(Boolean).length
  if (issues === 0) return { label: 'Healthy', pct: 80, status: 'good' }
  if (issues === 1) return { label: 'Fair', pct: 50, status: 'warn' }
  return { label: 'Critical gaps', pct: 25, status: 'bad' }
}

function websiteStatus(audit: AuditResponse | null): { label: string; pct: number; status: 'good' | 'warn' | 'bad' } {
  if (!audit?.http_status_code) return { label: 'Not scanned', pct: 0, status: 'warn' }
  const code = audit.http_status_code
  if (code >= 200 && code < 300 && audit.https_enabled) {
    return { label: 'Live & secure', pct: 100, status: 'good' }
  }
  if (code >= 200 && code < 400) return { label: `HTTP ${code}`, pct: 70, status: 'warn' }
  return { label: `HTTP ${code}`, pct: 20, status: 'bad' }
}

function contactAvailability(audit: AuditResponse | null, lead: LeadDetailResponse): { label: string; pct: number; status: 'good' | 'warn' | 'bad' } {
  let score = 0
  if (lead.phone) score += 25
  if (audit?.emails?.length) score += 25
  if (audit?.phone_numbers?.length) score += 15
  if (audit?.contact_page_exists) score += 20
  if (audit?.contact_form_present) score += 15
  if (score >= 75) return { label: 'Excellent', pct: score, status: 'good' }
  if (score >= 40) return { label: 'Partial', pct: score, status: 'warn' }
  return { label: 'Limited', pct: Math.max(score, 10), status: 'bad' }
}

function HealthRing({
  label,
  value,
  display,
  status,
}: {
  label: string
  value: number
  display: string
  status: 'good' | 'warn' | 'bad'
}) {
  const r = 30
  const circ = 2 * Math.PI * r
  const offset = circ - (value / 100) * circ
  const stroke =
    status === 'good' ? '#22c55e' : status === 'warn' ? '#f59e0b' : '#ef4444'

  return (
    <div className="ld-health-ring">
      <svg className="ld-health-ring__svg" viewBox="0 0 72 72">
        <circle className="ld-health-ring__track" cx="36" cy="36" r={r} />
        <circle
          className="ld-health-ring__fill"
          cx="36"
          cy="36"
          r={r}
          stroke={stroke}
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ld-health-ring__value" style={{ color: stroke }}>
        {display}
      </div>
      <div className="ld-health-ring__label">{label}</div>
    </div>
  )
}

function CopyButton({ text, onCopied }: { text: string; onCopied: () => void }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    onCopied()
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button type="button" className="ld-copy-btn" onClick={handleCopy}>
      {copied ? <Check size={11} /> : <Copy size={11} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="ld-score-bar">
      <div className="ld-score-bar__head">
        <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
        <span style={{ fontWeight: 600, color: scoreColour(value) }}>{Math.round(value)}</span>
      </div>
      <div className="ld-score-bar__track">
        <div
          className="ld-score-bar__fill"
          style={{ width: `${value}%`, background: scoreColour(value) }}
        />
      </div>
    </div>
  )
}

function PageSkeleton() {
  return (
    <div className="ld-root">
      <div className="ld-skeleton-hero">
        <div className="ld-skeleton ld-skeleton--avatar" />
        <div style={{ flex: 1 }}>
          <div className="ld-skeleton ld-skeleton--title" />
          <div className="ld-skeleton ld-skeleton--line" />
        </div>
      </div>
      <div className="ld-layout">
        <div><div className="ld-skeleton ld-skeleton-card" /></div>
        <div><div className="ld-skeleton ld-skeleton-card" style={{ height: 320 }} /></div>
        <div><div className="ld-skeleton ld-skeleton-card" style={{ height: 280 }} /></div>
      </div>
      <p style={{ textAlign: 'center', color: 'var(--color-text-muted)', fontSize: 13, marginTop: 24 }}>
        Loading lead intelligence…
      </p>
    </div>
  )
}

function EmptyBlock({
  icon: Icon,
  title,
  desc,
  action,
}: {
  icon: React.ElementType
  title: string
  desc: string
  action?: React.ReactNode
}) {
  return (
    <div className="ld-empty">
      <div className="ld-empty__icon">
        <Icon size={24} />
      </div>
      <div className="ld-empty__title">{title}</div>
      <div className="ld-empty__desc">{desc}</div>
      {action}
    </div>
  )
}

function IntelCard({
  icon: Icon,
  iconClass,
  title,
  children,
}: {
  icon: React.ElementType
  iconClass: string
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="ld-intel-card">
      <div className="ld-intel-card__head">
        <div className={`ld-intel-card__icon ${iconClass}`}>
          <Icon size={18} />
        </div>
        <h3 className="ld-intel-card__title">{title}</h3>
      </div>
      {children}
    </div>
  )
}

export default function LeadDetailsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [toast, setToast] = useState<ToastState | null>(null)
  const [lightboxUrl, setLightboxUrl] = useState<string | null>(null)

  const showToast = useCallback((msg: string, type: ToastState['type'] = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }, [])

  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.leads.detail(id!),
    queryFn: () => leadsApi.get(id!),
    enabled: !!id,
  })

  const lead = data?.data

  const invalidate = () => qc.invalidateQueries({ queryKey: queryKeys.leads.detail(id!) })

  const analysisMut = useMutation({
    mutationFn: () => analysisApi.analyze(id!),
    onSuccess: () => { invalidate(); showToast('Website analysis complete') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const screenshotMut = useMutation({
    mutationFn: () => screenshotsApi.capture(id!),
    onSuccess: () => { invalidate(); showToast('Screenshots captured') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const auditMut = useMutation({
    mutationFn: () => auditsApi.run(id!),
    onSuccess: () => { invalidate(); showToast('AI audit complete') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const outreachMut = useMutation({
    mutationFn: () => outreachApi.generate(id!),
    onSuccess: () => { invalidate(); showToast('Outreach generated') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const deleteMut = useMutation({
    mutationFn: () => leadsApi.delete(id!),
    onSuccess: () => navigate('/leads'),
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })

  useEffect(() => {
    if (!lightboxUrl) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setLightboxUrl(null) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [lightboxUrl])

  const intel = useMemo(() => {
    if (!lead) return null
    const audit = lead.audit
    const score = lead.score
    return {
      strengths: deriveStrengths(audit, score),
      opportunities: deriveOpportunities(audit?.weaknesses, audit?.verdict ?? null),
      threats: deriveThreats(audit?.weaknesses),
      recommendations: deriveRecommendations(audit?.weaknesses, score),
    }
  }, [lead])

  const timelineEvents = useMemo(() => {
    if (!lead) return []
    return [
      {
        id: 'created',
        title: 'Lead Created',
        date: lead.created_at,
        done: true,
        icon: Users,
        desc: `${lead.name} added to your pipeline from ${lead.city}, ${lead.country}.`,
      },
      {
        id: 'analyzed',
        title: 'Website Analyzed',
        date: lead.audit?.http_status_code ? lead.audit.created_at : null,
        done: !!lead.audit?.http_status_code,
        icon: Search,
        desc: lead.audit?.http_status_code
          ? `HTTP ${lead.audit.http_status_code} · ${lead.audit.response_time_ms ? `${Math.round(lead.audit.response_time_ms)}ms load` : 'Response captured'}`
          : 'Run website analysis to crawl SEO, content, and performance data.',
      },
      {
        id: 'screenshot',
        title: 'Screenshot Captured',
        date: lead.screenshot?.created_at ?? null,
        done: !!lead.screenshot?.desktop_cloudinary_url,
        icon: Camera,
        desc: lead.screenshot?.desktop_cloudinary_url
          ? 'Desktop, mobile, and full-page captures stored.'
          : 'Capture visual snapshots for AI audit and outreach personalization.',
      },
      {
        id: 'audit',
        title: 'Audit Completed',
        date: lead.audit?.executive_summary ? lead.audit.updated_at : null,
        done: !!lead.audit?.executive_summary,
        icon: Bot,
        desc: lead.audit?.executive_summary
          ? 'AI executive summary, weaknesses, and lead score generated.'
          : 'Run AI audit to unlock intelligence and scoring.',
      },
      {
        id: 'outreach',
        title: 'Outreach Generated',
        date: lead.outreach?.created_at ?? null,
        done: !!lead.outreach?.cold_email,
        icon: MessageSquare,
        desc: lead.outreach?.cold_email
          ? 'Personalized cold email, follow-up, and CTA ready to send.'
          : 'Generate AI-powered outreach copy based on audit findings.',
      },
    ]
  }, [lead])

  if (isLoading) return <PageSkeleton />

  if (error || !lead) {
    return (
      <div className="ld-root">
        <button type="button" className="ld-back" onClick={() => navigate('/leads')}>
          <ArrowLeft size={14} /> Back to Leads
        </button>
        <EmptyBlock
          icon={AlertTriangle}
          title="Lead not found"
          desc={getErrorMessage(error) || 'This lead may have been deleted or you lack access.'}
          action={
            <button type="button" className="btn btn-primary" onClick={() => navigate('/leads')}>
              Return to Lead Management
            </button>
          }
        />
      </div>
    )
  }

  const audit = lead.audit
  const score = lead.score
  const favicon = faviconUrl(lead.website)
  const ws = websiteStatus(audit)
  const seo = seoLabel(audit, score)
  const perf = perfLabel(audit?.response_time_ms)
  const contact = contactAvailability(audit, lead)

  const emails = [
    ...(audit?.emails ?? []),
  ].filter(Boolean)
  const phones = [
    lead.phone,
    ...(audit?.phone_numbers ?? []),
  ].filter(Boolean) as string[]
  const uniquePhones = [...new Set(phones)]

  const socials = [
    { label: 'Facebook', url: audit?.social_facebook },
    { label: 'Instagram', url: audit?.social_instagram },
    { label: 'LinkedIn', url: audit?.social_linkedin },
    { label: 'Twitter', url: audit?.social_twitter },
    { label: 'YouTube', url: audit?.social_youtube },
    ...(audit?.social_links?.map((url, i) => ({ label: `Link ${i + 1}`, url })) ?? []),
  ].filter((s) => s.url)

  const renderQuickActions = () => (
    <div className="ld-card">
      <h2 className="ld-card__title">
        <Zap size={14} className="ld-card__title-icon" />
        Quick Actions
      </h2>
      <div className="ld-actions">
        <button
          type="button"
          className={`ld-action-btn ${audit?.http_status_code ? 'ld-action-btn--done' : ''}`}
          onClick={() => analysisMut.mutate()}
          disabled={analysisMut.isPending}
        >
          <span className="ld-action-btn__icon ld-action-btn__icon--analyze">
            {analysisMut.isPending ? <Loader size={16} className="animate-spin" /> : <Globe size={16} />}
          </span>
          {analysisMut.isPending ? 'Analyzing…' : audit?.http_status_code ? 'Re-analyze Website' : 'Analyze Website'}
        </button>
        <button
          type="button"
          className={`ld-action-btn ${lead.screenshot?.desktop_cloudinary_url ? 'ld-action-btn--done' : ''}`}
          onClick={() => screenshotMut.mutate()}
          disabled={screenshotMut.isPending}
        >
          <span className="ld-action-btn__icon ld-action-btn__icon--screenshot">
            {screenshotMut.isPending ? <Loader size={16} className="animate-spin" /> : <Camera size={16} />}
          </span>
          {screenshotMut.isPending ? 'Capturing…' : lead.screenshot?.desktop_cloudinary_url ? 'Recapture Screenshots' : 'Capture Screenshot'}
        </button>
        <button
          type="button"
          className={`ld-action-btn ${audit?.executive_summary ? 'ld-action-btn--done' : ''}`}
          onClick={() => auditMut.mutate()}
          disabled={auditMut.isPending}
        >
          <span className="ld-action-btn__icon ld-action-btn__icon--audit">
            {auditMut.isPending ? <Loader size={16} className="animate-spin" /> : <Bot size={16} />}
          </span>
          {auditMut.isPending ? 'Auditing…' : audit?.executive_summary ? 'Re-run AI Audit' : 'Run AI Audit'}
        </button>
        <button
          type="button"
          className={`ld-action-btn ${lead.outreach?.cold_email ? 'ld-action-btn--done' : ''}`}
          onClick={() => outreachMut.mutate()}
          disabled={outreachMut.isPending}
        >
          <span className="ld-action-btn__icon ld-action-btn__icon--outreach">
            {outreachMut.isPending ? <Loader size={16} className="animate-spin" /> : <MessageSquare size={16} />}
          </span>
          {outreachMut.isPending ? 'Generating…' : lead.outreach?.cold_email ? 'Regenerate Outreach' : 'Generate Outreach'}
        </button>
        <button
          type="button"
          className="ld-action-btn ld-action-btn--danger"
          onClick={() => confirm('Delete this lead permanently?') && deleteMut.mutate()}
          disabled={deleteMut.isPending}
        >
          <span className="ld-action-btn__icon ld-action-btn__icon--delete">
            <Trash2 size={16} />
          </span>
          Delete Lead
        </button>
      </div>
    </div>
  )

  const renderProfileColumn = () => (
    <div className="ld-stack">
      <div className="ld-card">
        <h2 className="ld-card__title">
          <Building2 size={14} className="ld-card__title-icon" />
          Business Profile
        </h2>
        <div className="ld-contact-row">
          <Building2 size={14} className="ld-contact-row__icon" />
          <div>
            <div className="ld-contact-row__label">Industry</div>
            <div className="ld-contact-row__value">{lead.industry}</div>
          </div>
        </div>
        {lead.rating != null && (
          <div className="ld-contact-row">
            <Star size={14} className="ld-contact-row__icon" style={{ color: '#fbbf24' }} />
            <div>
              <div className="ld-contact-row__label">Google Rating</div>
              <div className="ld-contact-row__value">
                {lead.rating.toFixed(1)}
                {lead.reviews_count != null && (
                  <span style={{ color: 'var(--color-text-muted)', marginLeft: 6 }}>
                    ({lead.reviews_count} reviews)
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
        {lead.address && (
          <div className="ld-contact-row">
            <MapPin size={14} className="ld-contact-row__icon" />
            <div>
              <div className="ld-contact-row__label">Address</div>
              <div className="ld-contact-row__value">{lead.address}</div>
            </div>
          </div>
        )}
        <div className="ld-contact-row">
          <MapPin size={14} className="ld-contact-row__icon" />
          <div>
            <div className="ld-contact-row__label">Location</div>
            <div className="ld-contact-row__value">{lead.city}, {lead.country}</div>
          </div>
        </div>
      </div>

      <div className="ld-card">
        <h2 className="ld-card__title">
          <Phone size={14} className="ld-card__title-icon" />
          Contact Information
        </h2>
        {lead.website && (
          <div className="ld-contact-row">
            <Globe size={14} className="ld-contact-row__icon" />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="ld-contact-row__label">Website</div>
              <a
                href={lead.website}
                target="_blank"
                rel="noreferrer"
                className="ld-contact-row__value"
                style={{ color: 'var(--ld-blue)', display: 'inline-flex', alignItems: 'center', gap: 4 }}
              >
                {lead.website.replace(/^https?:\/\//, '')}
                <ExternalLink size={11} />
              </a>
              <CopyButton text={lead.website} onCopied={() => showToast('Website copied')} />
            </div>
          </div>
        )}
        {uniquePhones.map((phone) => (
          <div key={phone} className="ld-contact-row">
            <Phone size={14} className="ld-contact-row__icon" />
            <div>
              <div className="ld-contact-row__label">Phone</div>
              <div className="ld-contact-row__value">{phone}</div>
              <CopyButton text={phone} onCopied={() => showToast('Phone copied')} />
            </div>
          </div>
        ))}
        {emails.map((email) => (
          <div key={email} className="ld-contact-row">
            <Mail size={14} className="ld-contact-row__icon" />
            <div>
              <div className="ld-contact-row__label">Email</div>
              <div className="ld-contact-row__value">{email}</div>
              <CopyButton text={email} onCopied={() => showToast('Email copied')} />
            </div>
          </div>
        ))}
        {socials.length > 0 && (
          <div className="ld-contact-row">
            <Share2 size={14} className="ld-contact-row__icon" />
            <div>
              <div className="ld-contact-row__label">Social Links</div>
              <div className="ld-socials">
                {socials.map(({ label, url }) => (
                  <a key={url!} href={url!} target="_blank" rel="noreferrer" className="ld-social-link">
                    {label} <ExternalLink size={10} />
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}
        {!lead.website && uniquePhones.length === 0 && emails.length === 0 && (
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.6 }}>
            Run website analysis to discover emails, phone numbers, and social profiles.
          </p>
        )}
      </div>

      {score && (
        <div className="ld-card">
          <h2 className="ld-card__title">
            <Gauge size={14} className="ld-card__title-icon" />
            Score Breakdown
          </h2>
          <ScoreBar label="SEO" value={score.seo_score} />
          <ScoreBar label="UX" value={score.ux_score} />
          <ScoreBar label="Branding" value={score.branding_score} />
          <ScoreBar label="Trust" value={score.trust_score} />
          <ScoreBar label="Conversion" value={score.conversion_score} />
        </div>
      )}
    </div>
  )

  const renderOverviewTab = () => (
    <div className="ld-stack">
      <PremiumCard>
        <div className="ld-card__title" style={{ marginBottom: 20 }}>
          <Shield size={14} className="ld-card__title-icon" />
          Company Health
        </div>
        <div className="ld-health-grid">
          <HealthRing
            label="AI Score"
            value={score?.overall_score ?? 0}
            display={score ? String(Math.round(score.overall_score)) : '—'}
            status={score ? (score.overall_score >= 75 ? 'good' : score.overall_score >= 50 ? 'warn' : 'bad') : 'warn'}
          />
          <HealthRing label="Website" value={ws.pct} display={ws.label} status={ws.status} />
          <HealthRing label="SEO" value={seo.pct} display={seo.label} status={seo.status} />
          <HealthRing label="Performance" value={perf.pct} display={perf.label} status={perf.status} />
          <HealthRing label="Contact" value={contact.pct} display={contact.label} status={contact.status} />
        </div>
      </PremiumCard>

      {!audit?.executive_summary && !score ? (
        <EmptyBlock
          icon={Sparkles}
          title="Unlock AI Intelligence"
          desc="Analyze this website and run an AI audit to generate executive summaries, scoring, and actionable insights."
          action={
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-secondary" onClick={() => analysisMut.mutate()} disabled={analysisMut.isPending}>
                Analyze Website
              </button>
              <button type="button" className="btn btn-primary" onClick={() => auditMut.mutate()} disabled={auditMut.isPending}>
                Run AI Audit
              </button>
            </div>
          }
        />
      ) : (
        <div className="ld-intel-grid">
          {audit?.executive_summary && (
            <IntelCard icon={Sparkles} iconClass="ld-intel-card__icon--summary" title="Executive Summary">
              <p className="ld-intel-card__body">{audit.executive_summary}</p>
            </IntelCard>
          )}
          {(audit?.meta_description || audit?.website_title) && (
            <IntelCard icon={FileText} iconClass="ld-intel-card__icon--overview" title="Business Overview">
              <p className="ld-intel-card__body">
                {audit.website_title && <strong>{audit.website_title}. </strong>}
                {audit.meta_description ?? score?.explanation ?? 'Website metadata captured from latest analysis.'}
              </p>
            </IntelCard>
          )}
          {intel && intel.strengths.length > 0 && (
            <IntelCard icon={TrendingUp} iconClass="ld-intel-card__icon--strength" title="Strengths">
              <ul className="ld-intel-list ld-intel-list--strength">
                {intel.strengths.map((s) => <li key={s}>{s}</li>)}
              </ul>
            </IntelCard>
          )}
          {audit?.weaknesses && audit.weaknesses.length > 0 && (
            <IntelCard icon={AlertTriangle} iconClass="ld-intel-card__icon--weakness" title="Weaknesses">
              {audit.weaknesses.map((w, i) => (
                <div key={i} className="ld-weakness-item">
                  <div className="ld-weakness-item__title">{w.title}</div>
                  {w.evidence && <div className="ld-weakness-item__text">{w.evidence}</div>}
                  {w.impact && (
                    <div className="ld-weakness-item__text" style={{ marginTop: 4, color: 'var(--color-warning)' }}>
                      Impact: {w.impact}
                    </div>
                  )}
                </div>
              ))}
            </IntelCard>
          )}
          {intel && intel.opportunities.length > 0 && (
            <IntelCard icon={Target} iconClass="ld-intel-card__icon--opportunity" title="Opportunities">
              <ul className="ld-intel-list ld-intel-list--opportunity">
                {intel.opportunities.map((o, i) => <li key={i}>{o}</li>)}
              </ul>
            </IntelCard>
          )}
          {intel && intel.threats.length > 0 && (
            <IntelCard icon={AlertTriangle} iconClass="ld-intel-card__icon--threat" title="Threats">
              <ul className="ld-intel-list ld-intel-list--threat">
                {intel.threats.map((t, i) => <li key={i}>{t}</li>)}
              </ul>
            </IntelCard>
          )}
          {intel && intel.recommendations.length > 0 && (
            <IntelCard icon={Lightbulb} iconClass="ld-intel-card__icon--recommend" title="Recommendations">
              <ul className="ld-intel-list">
                {intel.recommendations.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </IntelCard>
          )}
          {audit?.verdict && (
            <IntelCard icon={Bot} iconClass="ld-intel-card__icon--summary" title="Overall Verdict">
              <p className="ld-intel-card__body">{audit.verdict}</p>
            </IntelCard>
          )}
        </div>
      )}
    </div>
  )

  const renderAnalysisTab = () => (
    <div className="ld-tab-panel">
      {!audit?.http_status_code ? (
        <EmptyBlock
          icon={Globe}
          title="No website analysis yet"
          desc="Crawl this lead's website to extract SEO signals, content structure, contact data, and performance metrics."
          action={
            <button type="button" className="btn btn-primary" onClick={() => analysisMut.mutate()} disabled={analysisMut.isPending}>
              {analysisMut.isPending ? <Loader size={14} className="animate-spin" /> : <Globe size={14} />}
              Analyze Website
            </button>
          }
        />
      ) : (
        <div className="ld-stack">
          <div className="ld-card">
            <h2 className="ld-card__title">
              <Search size={14} className="ld-card__title-icon" />
              Page Overview
            </h2>
            <div className="ld-analysis-grid">
              {[
                { label: 'Title', value: audit.website_title ?? '—' },
                { label: 'Language', value: audit.website_language ?? '—' },
                { label: 'HTTP Status', value: audit.http_status_code ?? '—' },
                { label: 'Load Time', value: audit.response_time_ms ? `${Math.round(audit.response_time_ms)}ms` : '—' },
                { label: 'HTTPS', value: audit.https_enabled ? 'Yes' : 'No' },
                { label: 'HTML Size', value: audit.html_size_kb ? `${audit.html_size_kb.toFixed(1)} KB` : '—' },
              ].map(({ label, value }) => (
                <div key={label} className="ld-analysis-cell">
                  <div className="ld-analysis-cell__label">{label}</div>
                  <div className="ld-analysis-cell__value">{value}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="ld-card">
            <h2 className="ld-card__title">
              <FileText size={14} className="ld-card__title-icon" />
              Content Structure
            </h2>
            <div className="ld-analysis-grid">
              {[
                { label: 'H1 Tags', value: audit.h1_count },
                { label: 'H2 Tags', value: audit.h2_count },
                { label: 'Paragraphs', value: audit.total_paragraphs },
                { label: 'Images', value: audit.total_images },
                { label: 'Forms', value: audit.total_forms },
                { label: 'Contact Page', value: audit.contact_page_exists ? 'Yes' : 'No' },
                { label: 'About Page', value: audit.about_page_exists ? 'Yes' : 'No' },
                { label: 'Testimonials', value: audit.testimonials_present ? 'Yes' : 'No' },
              ].map(({ label, value }) => (
                <div key={label} className="ld-analysis-cell">
                  <div className="ld-analysis-cell__label">{label}</div>
                  <div className="ld-analysis-cell__value">{value}</div>
                </div>
              ))}
            </div>
          </div>
          {audit.technologies && audit.technologies.length > 0 && (
            <div className="ld-card">
              <h2 className="ld-card__title">Technologies Detected</h2>
              <div className="ld-socials">
                {audit.technologies.map((t) => (
                  <span key={t} className="ld-social-link">{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )

  const renderScreenshotsTab = () => {
    const shots = [
      { label: 'Desktop', url: lead.screenshot?.desktop_cloudinary_url },
      { label: 'Mobile', url: lead.screenshot?.mobile_cloudinary_url },
      { label: 'Full Page', url: lead.screenshot?.full_page_cloudinary_url },
    ]
    const hasAny = shots.some((s) => s.url)

    return (
      <div className="ld-tab-panel">
        {!hasAny ? (
          <EmptyBlock
            icon={Camera}
            title="No screenshots captured"
            desc="Capture desktop, mobile, and full-page screenshots for visual AI audit and outreach personalization."
            action={
              <button type="button" className="btn btn-primary" onClick={() => screenshotMut.mutate()} disabled={screenshotMut.isPending}>
                {screenshotMut.isPending ? <Loader size={14} className="animate-spin" /> : <Camera size={14} />}
                Capture Screenshots
              </button>
            }
          />
        ) : (
          <>
            <div className="ld-gallery">
              {shots.map(({ label, url }) => (
                <div key={label} className="ld-gallery__item">
                  <div className="ld-gallery__label">{label}</div>
                  <div
                    className="ld-gallery__img-wrap"
                    onClick={() => url && setLightboxUrl(url)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && url && setLightboxUrl(url)}
                    aria-label={`View ${label} screenshot`}
                  >
                    {url ? (
                      <img src={url} alt={`${label} screenshot of ${lead.name}`} loading="lazy" />
                    ) : (
                      <div className="ld-gallery__placeholder">
                        <ImageIcon size={24} />
                        Not captured
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ marginTop: 20 }}
              onClick={() => screenshotMut.mutate()}
              disabled={screenshotMut.isPending}
            >
              <RefreshCw size={14} /> Recapture All
            </button>
          </>
        )}
      </div>
    )
  }

  const renderAuditTab = () => (
    <div className="ld-tab-panel">
      {!audit?.executive_summary ? (
        <EmptyBlock
          icon={Bot}
          title="No AI audit generated"
          desc="Run a multi-modal AI audit using website data and screenshots to produce executive summaries, weaknesses, and lead scoring."
          action={
            <button type="button" className="btn btn-primary" onClick={() => auditMut.mutate()} disabled={auditMut.isPending}>
              {auditMut.isPending ? <Loader size={14} className="animate-spin" /> : <Bot size={14} />}
              Run AI Audit
            </button>
          }
        />
      ) : (
        renderOverviewTab()
      )}
    </div>
  )

  const renderOutreachTab = () => {
    const blocks = [
      { label: 'Email Subject', value: lead.outreach?.email_subject, icon: Mail },
      { label: 'Cold Email', value: lead.outreach?.cold_email, icon: MessageSquare },
      { label: 'Follow-up Email', value: lead.outreach?.followup_email, icon: RefreshCw },
      { label: 'LinkedIn Message', value: lead.outreach?.linkedin_message, icon: Share2 },
      { label: 'Call-to-Action', value: lead.outreach?.short_cta, icon: Target },
    ].filter((b) => b.value)

    return (
      <div className="ld-tab-panel">
        {blocks.length === 0 ? (
          <EmptyBlock
            icon={MessageSquare}
            title="No outreach generated yet"
            desc="Generate personalized cold emails, follow-ups, and CTAs powered by AI audit findings and lead score."
            action={
              <button type="button" className="btn btn-primary" onClick={() => outreachMut.mutate()} disabled={outreachMut.isPending}>
                {outreachMut.isPending ? <Loader size={14} className="animate-spin" /> : <MessageSquare size={14} />}
                Generate Outreach
              </button>
            }
          />
        ) : (
          <>
            {blocks.map(({ label, value, icon: Icon }) => (
              <div key={label} className="ld-outreach-block">
                <div className="ld-outreach-block__head">
                  <span className="ld-outreach-block__label">
                    <Icon size={14} /> {label}
                  </span>
                  <CopyButton text={value!} onCopied={() => showToast(`${label} copied`)} />
                </div>
                <div className="ld-outreach-block__body">{value}</div>
              </div>
            ))}
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => outreachMut.mutate()}
              disabled={outreachMut.isPending}
            >
              <RefreshCw size={14} /> Regenerate All
            </button>
          </>
        )}
      </div>
    )
  }

  const renderTimelineTab = () => (
    <div className="ld-tab-panel">
      <div className="ld-card">
        <h2 className="ld-card__title">
          <Clock size={14} className="ld-card__title-icon" />
          Activity Timeline
        </h2>
        <div className="ld-timeline">
          {timelineEvents.map((ev) => {
            const Icon = ev.icon
            return (
              <div
                key={ev.id}
                className={`ld-timeline__item ${ev.done ? 'ld-timeline__item--done' : 'ld-timeline__item--pending'}`}
              >
                <div className="ld-timeline__dot">
                  <Icon size={12} />
                </div>
                <div className="ld-timeline__title">{ev.title}</div>
                <div className="ld-timeline__date">
                  {ev.date ? `${formatDate(ev.date)} · ${formatDateRelative(ev.date)}` : 'Pending'}
                </div>
                <div className="ld-timeline__desc">{ev.desc}</div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )

  const renderCenterContent = () => {
    switch (activeTab) {
      case 'overview': return renderOverviewTab()
      case 'analysis': return renderAnalysisTab()
      case 'screenshots': return renderScreenshotsTab()
      case 'audit': return renderAuditTab()
      case 'outreach': return renderOutreachTab()
      case 'timeline': return renderTimelineTab()
    }
  }

  return (
    <div className="ld-root animate-fade-in">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <button type="button" className="ld-back" onClick={() => navigate('/leads')}>
        <ArrowLeft size={14} /> Back to Leads
      </button>

      <header className="ld-hero">
        <div className="ld-hero__brand">
          <div className="ld-hero__favicon">
            {favicon ? (
              <img src={favicon} alt="" onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
            ) : (
              <Building2 size={24} color="var(--color-text-muted)" />
            )}
          </div>
          <div style={{ minWidth: 0 }}>
            <h1 className="ld-hero__name">{lead.name}</h1>
            <div className="ld-hero__meta">
              {lead.website && (
                <span className="ld-hero__meta-item">
                  <Globe size={13} />
                  <a href={lead.website} target="_blank" rel="noreferrer">
                    {lead.website.replace(/^https?:\/\//, '')}
                  </a>
                </span>
              )}
              <span className="ld-hero__meta-item">
                <Building2 size={13} /> {lead.industry}
              </span>
              <span className="ld-hero__meta-item">
                <MapPin size={13} /> {lead.city}, {lead.country}
              </span>
            </div>
          </div>
        </div>
        <div className="ld-hero__badges">
          <span className={statusPillClass(lead.status)}>{lead.status.replace(/_/g, ' ')}</span>
          <ScoreBadge score={score?.overall_score} />
          <span className="ld-hero__updated">
            Updated {formatDateRelative(lead.updated_at)}
          </span>
        </div>
      </header>

      <nav className="ld-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={activeTab === t.id}
            className={`ld-tab ${activeTab === t.id ? 'ld-tab--active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="ld-layout">
        <aside className="ld-col ld-col--left">{renderProfileColumn()}</aside>
        <main className="ld-col ld-col--center">{renderCenterContent()}</main>
        <aside className="ld-col ld-col--right">{renderQuickActions()}</aside>
      </div>

      {lightboxUrl && (
        <div
          className="ld-lightbox"
          onClick={() => setLightboxUrl(null)}
          role="dialog"
          aria-label="Screenshot preview"
        >
          <button
            type="button"
            className="ld-lightbox__close"
            onClick={() => setLightboxUrl(null)}
            aria-label="Close preview"
          >
            <X size={18} />
          </button>
          <img
            className="ld-lightbox__img"
            src={lightboxUrl}
            alt="Screenshot preview"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}
