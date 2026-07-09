import { useNavigate } from 'react-router-dom';
import { Clock, Search, TrendingUp, Sparkles } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';
import { PremiumCard } from '@/components/PremiumCard';
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
        <PremiumCard variant="danger" innerClassName="p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-5">
            <Clock className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-bold text-white mb-2">History Unavailable</h2>
          <p className="text-[13px] text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
            Unable to load activity history. Verify your connection and try again.
          </p>
          <button
            onClick={() => refetch()}
            className="bg-gradient-to-r from-[var(--color-brand)] to-[var(--color-brand-600)] text-white px-6 py-2.5 rounded-[var(--radius-md)] font-medium hover:-translate-y-0.5 transition-all"
          >
            Re-establish Link
          </button>
        </PremiumCard>
      </div>
    );
  }

  return (
    <div className="space-y-8 lf-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="lf-display text-white mb-1">Activity <span className="lf-display-gradient">Timeline</span></h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] font-mono">Chronological record of all lead activity</p>
        </div>
        <div className="flex items-center gap-3">
          {leads.length > 0 && (
            <span className="text-[11px] font-mono text-[var(--color-text-muted)]">{recent?.total ?? leads.length} total entries</span>
          )}
          <button
            onClick={() => refetch()}
            className="bg-[var(--color-glass)] backdrop-blur-md text-[var(--color-text)] border border-[var(--color-glass-border)] px-4 py-2 rounded-[var(--radius-md)] font-medium text-[12px] hover:bg-[var(--color-glass-strong)] hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
          >
            <TrendingUp size={13} /> Refresh
          </button>
        </div>
      </div>

      <PremiumCard variant="featured" innerClassName="p-6 lg:p-8">
        {isLoading ? (
          <div className="space-y-5">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton variant="rounded" width={32} height={32} />
                <div className="flex-1 space-y-2">
                  <Skeleton variant="text" width="60%" height={14} />
                  <Skeleton variant="text" width="40%" height={12} />
                </div>
              </div>
            ))}
          </div>
        ) : leads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="size-16 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center mb-5 shadow-[0_0_30px_rgba(14,165,233,0.2)]">
              <Clock className="size-7 text-[#0ea5e9]" />
            </div>
            <h2 className="text-[18px] font-bold text-white mb-2">No Activity Yet</h2>
            <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm">
              Your timeline will populate as you discover, analyze, and engage with leads.
            </p>
            <button
              onClick={() => navigate('/projects')}
              className="bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-6 py-2.5 rounded-[var(--radius-md)] font-bold text-[12px] shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
            >
              <Search size={14} /> Start Discovery
            </button>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline vertical line */}
            <div className="absolute left-4 top-0 bottom-0 w-px bg-gradient-to-b from-[#0ea5e9] via-[#8b5cf6] to-transparent opacity-30" />

            <div className="space-y-0 divide-y divide-[var(--color-border)]">
              {leads.map((lead) => {
                const initial = lead.name[0]?.toUpperCase() ?? '?';
                return (
                  <div
                    key={lead.id}
                    onClick={() => navigate(`/project/${lead.id}`)}
                    className="relative flex items-start gap-5 py-4 pl-0 hover:bg-[var(--color-surface-hover)] -mx-6 px-6 cursor-pointer transition-all group"
                  >
                    {/* Timeline node */}
                    <div className="relative z-10 mt-0.5">
                      <div className="size-8 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center text-[11px] font-bold text-[#0ea5e9] shrink-0 shadow-[0_0_12px_rgba(14,165,233,0.2)] group-hover:shadow-[0_0_20px_rgba(14,165,233,0.4)] transition-shadow">
                        {initial}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <p className="text-[13px] font-semibold text-white truncate group-hover:text-[#0ea5e9] transition-colors">{lead.name}</p>
                          <p className="text-[11px] font-mono text-[var(--color-text-muted)] mt-0.5">
                            {lead.industry} &middot; {lead.city}, {lead.country}
                          </p>
                        </div>
                        <Badge tone={statusBadgeTone(lead.status)} className="text-[10px] shrink-0">
                          {lead.status.replace(/_/g, ' ')}
                        </Badge>
                      </div>

                      {/* Status insight row */}
                      <div className="flex items-center gap-3 mt-2.5">
                        <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--color-text-muted)]">
                          <Clock size={10} />
                          <span>Created {formatRelative(lead.created_at)}</span>
                        </div>
                        {lead.rating != null && (
                          <div className="flex items-center gap-1.5 text-[10px] font-mono text-[var(--color-text-muted)]">
                            <Sparkles size={10} className="text-[#0ea5e9]" />
                            <span>Score: {lead.rating.toFixed(1)}</span>
                          </div>
                        )}
                        <div className="text-[10px] font-mono text-[var(--color-text-muted)]">
                          {lead.id.slice(0, 8)}...
                        </div>
                      </div>
                    </div>

                    {/* Arrow indicator */}
                    <TrendingUp size={14} className="text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity shrink-0 self-center" />
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </PremiumCard>

      {/* Summary bar */}
      {leads.length > 0 && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <PremiumCard variant="subtle" innerClassName="p-4 text-center">
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Entries</p>
            <p className="text-[22px] font-extrabold text-white mt-1">{recent?.total ?? leads.length}</p>
          </PremiumCard>
          <PremiumCard variant="subtle" innerClassName="p-4 text-center">
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Industries</p>
            <p className="text-[22px] font-extrabold text-white mt-1">{new Set(leads.map(l => l.industry)).size}</p>
          </PremiumCard>
          <PremiumCard variant="subtle" innerClassName="p-4 text-center">
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Avg Score</p>
            <p className="text-[22px] font-extrabold text-white mt-1">
              {leads.filter(l => l.rating != null).length > 0
                ? (leads.reduce((a, l) => a + (l.rating ?? 0), 0) / leads.filter(l => l.rating != null).length).toFixed(1)
                : '—'}
            </p>
          </PremiumCard>
          <PremiumCard variant="subtle" innerClassName="p-4 text-center">
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Time Span</p>
            <p className="text-[22px] font-extrabold text-white mt-1">
              {leads.length > 1
                ? formatRelative(leads[leads.length - 1].created_at)
                : '—'}
            </p>
          </PremiumCard>
        </div>
      )}
    </div>
  );
}
