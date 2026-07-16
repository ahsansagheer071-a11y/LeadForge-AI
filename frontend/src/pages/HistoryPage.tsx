import { useNavigate } from 'react-router-dom';
import { Clock, Search, RefreshCw, MapPin } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { formatRelative } from '@/utils';

function statusBadgeTone(status: string): 'success' | 'warning' | 'danger' | 'info' | 'muted' {
  switch (status) {
    case 'OUTREACH_READY': return 'success';
    case 'CONTACTED': return 'success';
    case 'CLOSED': return 'success';
    case 'ANALYZED': return 'info';
    case 'SCRAPED': return 'info';
    case 'FAILED': return 'danger';
    case 'NEW': return 'muted';
    default: return 'muted';
  }
}

export function HistoryPage() {
  const navigate = useNavigate();

  const { data: recent, isLoading, error, refetch } = useQuery({
    queryKey: ['history', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(50, 0),
  });

  const leads = recent?.leads ?? [];

  if (error && !recent) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5">
            <Clock className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-semibold text-[var(--color-text)] mb-2">Activity Unavailable</h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
            Unable to load activity history. Verify your connection and try again.
          </p>
          <button
            onClick={() => refetch()}
            className="bg-[var(--color-brand)] text-white px-6 py-2.5 rounded-[var(--radius-md)] font-medium text-[13px] hover:bg-[var(--color-brand-hover)] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Header ──────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Activity</h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Chronological record of all lead activity across your pipeline</p>
        </div>
        <div className="flex items-center gap-3">
          {leads.length > 0 && (
            <span className="text-[11px] font-mono text-[var(--color-text-muted)]">{recent?.total ?? leads.length} total</span>
          )}
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-1.5 rounded-[var(--radius-md)] border border-[var(--color-border)] text-[12px] font-medium text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border-strong)] transition-colors"
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>
      </div>

      {/* ── Main Panel ──────────────────────────────────────── */}
      <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-0">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 py-3 border-b border-[var(--color-border)] last:border-0">
                <Skeleton variant="rounded" width={36} height={36} />
                <div className="flex-1 space-y-1.5">
                  <Skeleton variant="text" width="50%" height={14} />
                  <Skeleton variant="text" width="35%" height={11} />
                </div>
                <Skeleton variant="rounded" width={70} height={22} />
                <Skeleton variant="text" width={80} height={11} />
              </div>
            ))}
          </div>
        ) : leads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="size-14 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center mb-4">
              <Clock className="size-6 text-[var(--color-brand)]" />
            </div>
            <h2 className="text-[16px] font-semibold text-[var(--color-text)] mb-1.5">No Activity Yet</h2>
            <p className="text-[13px] text-[var(--color-text-secondary)] mb-5 max-w-xs">
              Your timeline will populate as you discover, analyze, and engage with leads.
            </p>
            <button
              onClick={() => navigate('/projects')}
              className="flex items-center gap-2 bg-[var(--color-brand)] text-white px-5 py-2 rounded-[var(--radius-md)] font-medium text-[12px] hover:bg-[var(--color-brand-hover)] transition-colors"
            >
              <Search size={13} /> Start Discovery
            </button>
          </div>
        ) : (
          <>
            {/* Table header */}
            <div className="grid grid-cols-[1fr_140px_100px_100px_100px] px-4 py-2.5 bg-[var(--color-surface-hover)] border-b border-[var(--color-border)] text-[11px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">
              <div>Business</div>
              <div>Location</div>
              <div>Industry</div>
              <div className="text-center">Status</div>
              <div className="text-right">Created</div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-[var(--color-border)]">
              {leads.map((lead) => {
                const initial = lead.name[0]?.toUpperCase() ?? '?';
                return (
                  <div
                    key={lead.id}
                    onClick={() => navigate(`/project/${lead.id}`)}
                    className="grid grid-cols-[1fr_140px_100px_100px_100px] px-4 py-3 items-center hover:bg-[var(--color-surface-hover)] cursor-pointer transition-colors group"
                  >
                    {/* Business */}
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="size-9 rounded-lg bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center text-[12px] font-bold text-[var(--color-brand)] shrink-0">
                        {initial}
                      </div>
                      <div className="min-w-0">
                        <p className="text-[13px] font-medium text-[var(--color-text)] truncate group-hover:text-[var(--color-brand)] transition-colors">
                          {lead.name}
                        </p>
                        {lead.rating != null && (
                          <p className="text-[10px] font-mono text-[var(--color-text-muted)] mt-0.5">
                            Score: {lead.rating.toFixed(1)}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Location */}
                    <div className="flex items-center gap-1.5 text-[12px] text-[var(--color-text-secondary)] min-w-0">
                      <MapPin size={12} className="text-[var(--color-text-muted)] shrink-0" />
                      <span className="truncate">{lead.city}, {lead.country}</span>
                    </div>

                    {/* Industry */}
                    <div className="text-[12px] text-[var(--color-text-secondary)] truncate">
                      {lead.industry}
                    </div>

                    {/* Status */}
                    <div className="flex justify-center">
                      <Badge tone={statusBadgeTone(lead.status)} className="text-[10px]">
                        {lead.status.replace(/_/g, ' ')}
                      </Badge>
                    </div>

                    {/* Created */}
                    <div className="text-right text-[11px] font-mono text-[var(--color-text-muted)]">
                      {formatRelative(lead.created_at)}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* ── Summary Metrics ─────────────────────────────────── */}
      {leads.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard label="Total Entries" value={recent?.total ?? leads.length} />
          <MetricCard label="Industries" value={new Set(leads.map(l => l.industry)).size} />
          <MetricCard
            label="Avg Score"
            value={
              leads.filter(l => l.rating != null).length > 0
                ? (leads.reduce((a, l) => a + (l.rating ?? 0), 0) / leads.filter(l => l.rating != null).length).toFixed(1)
                : '—'
            }
          />
          <MetricCard
            label="Time Span"
            value={leads.length > 1 ? formatRelative(leads[leads.length - 1].created_at) : '—'}
          />
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] p-4">
      <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-2">{label}</p>
      <p className="text-[20px] font-bold text-[var(--color-text)]">{value}</p>
    </div>
  );
}
