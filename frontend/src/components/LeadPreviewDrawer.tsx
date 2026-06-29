import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  X,
  ExternalLink,
  MapPin,
  Phone,
  Globe,
  Star,
  Bot,
  ArrowRight,
  Loader,
} from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { queryKeys, formatDate, scoreColour } from '@/utils'
import type { LeadResponse, LeadStatus } from '@/types'

function statusPillClass(status: LeadStatus): string {
  const map: Record<LeadStatus, string> = {
    NEW: 'lm-status--new',
    SCRAPED: 'lm-status--scraped',
    ANALYZED: 'lm-status--analyzed',
    OUTREACH_READY: 'lm-status--outreach',
    CONTACTED: 'lm-status--contacted',
    CLOSED: 'lm-status--closed',
  }
  return `lm-status ${map[status] ?? ''}`
}

function scoreTier(score: number): 'hot' | 'warm' | 'cold' {
  if (score >= 80) return 'hot'
  if (score >= 60) return 'warm'
  return 'cold'
}

interface LeadPreviewDrawerProps {
  lead: LeadResponse | null
  open: boolean
  onClose: () => void
  onOpenFull: (id: string) => void
}

export default function LeadPreviewDrawer({
  lead,
  open,
  onClose,
  onOpenFull,
}: LeadPreviewDrawerProps) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.leads.detail(lead?.id ?? ''),
    queryFn: () => leadsApi.get(lead!.id),
    enabled: open && !!lead?.id,
  })

  const detail = data?.data
  const score = detail?.score?.overall_score

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!lead) return null

  return (
    <>
      <div
        className={`lm-drawer-backdrop ${open ? 'lm-drawer-backdrop--open' : ''}`}
        onClick={onClose}
        aria-hidden={!open}
      />
      <aside
        className={`lm-drawer ${open ? 'lm-drawer--open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={`Preview ${lead.name}`}
      >
        <div className="lm-drawer__header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <h2 className="lm-drawer__title">{lead.name}</h2>
            <span className={statusPillClass(lead.status)}>
              {lead.status.replace('_', ' ')}
            </span>
          </div>
          <button type="button" className="lm-icon-btn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="lm-drawer__body">
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: 32, color: 'var(--color-text-muted)' }}>
              <Loader size={22} className="animate-spin" style={{ margin: '0 auto 12px' }} />
              <div style={{ fontSize: 13 }}>Loading lead intelligence…</div>
            </div>
          ) : (
            <>
              {score != null && (
                <div className="lm-drawer__section">
                  <div className="lm-drawer__label">AI Lead Score</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span
                      className={`lm-score lm-score--${scoreTier(score)}`}
                      style={{ fontSize: 16, minWidth: 48, padding: '8px 14px' }}
                    >
                      {score}
                    </span>
                    {detail?.score?.category && (
                      <span style={{ fontSize: 13, color: scoreColour(score), fontWeight: 600 }}>
                        {detail.score.category}
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div className="lm-drawer__section">
                <div className="lm-drawer__label">Industry</div>
                <div className="lm-drawer__value">{lead.industry}</div>
              </div>

              <div className="lm-drawer__section">
                <div className="lm-drawer__label">Location</div>
                <div className="lm-drawer__value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <MapPin size={14} color="var(--color-text-muted)" />
                  {lead.city}, {lead.country}
                </div>
              </div>

              {lead.website && (
                <div className="lm-drawer__section">
                  <div className="lm-drawer__label">Website</div>
                  <a
                    href={lead.website}
                    target="_blank"
                    rel="noreferrer"
                    className="lm-drawer__value"
                    style={{ color: 'var(--lm-blue)', display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <Globe size={14} /> {lead.website.replace(/^https?:\/\//, '')}
                    <ExternalLink size={12} />
                  </a>
                </div>
              )}

              {lead.phone && (
                <div className="lm-drawer__section">
                  <div className="lm-drawer__label">Phone</div>
                  <div className="lm-drawer__value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Phone size={14} color="var(--color-text-muted)" /> {lead.phone}
                  </div>
                </div>
              )}

              {lead.rating != null && (
                <div className="lm-drawer__section">
                  <div className="lm-drawer__label">Google Rating</div>
                  <div className="lm-drawer__value" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Star size={14} color="#fbbf24" fill="#fbbf24" />
                    {lead.rating.toFixed(1)}
                    {lead.reviews_count != null && (
                      <span style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>
                        ({lead.reviews_count} reviews)
                      </span>
                    )}
                  </div>
                </div>
              )}

              {detail?.audit?.executive_summary && (
                <div className="lm-drawer__section">
                  <div className="lm-drawer__label">AI Summary</div>
                  <p className="lm-drawer__value" style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                    {detail.audit.executive_summary.slice(0, 280)}
                    {detail.audit.executive_summary.length > 280 ? '…' : ''}
                  </p>
                </div>
              )}

              {!score && !detail?.audit && (
                <div
                  style={{
                    padding: 16,
                    borderRadius: 12,
                    background: 'var(--color-surface-raised)',
                    border: '1px solid var(--color-border)',
                    display: 'flex',
                    gap: 12,
                    alignItems: 'flex-start',
                  }}
                >
                  <Bot size={18} color="var(--lm-purple)" style={{ flexShrink: 0, marginTop: 2 }} />
                  <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.55 }}>
                    Run website analysis and AI audit to unlock lead scoring and intelligence for this business.
                  </div>
                </div>
              )}

              <div className="lm-drawer__section">
                <div className="lm-drawer__label">Added</div>
                <div className="lm-drawer__value">{formatDate(lead.created_at)}</div>
              </div>
            </>
          )}
        </div>

        <div className="lm-drawer__actions">
          <button type="button" className="btn btn-primary" onClick={() => onOpenFull(lead.id)}>
            Open Full Profile <ArrowRight size={14} />
          </button>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </aside>
    </>
  )
}

export { statusPillClass, scoreTier }

export function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) {
    return <span className="lm-score--none">—</span>
  }
  return (
    <span className={`lm-score lm-score--${scoreTier(score)}`}>{Math.round(score)}</span>
  )
}
