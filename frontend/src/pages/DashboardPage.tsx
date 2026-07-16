import { Users, CheckCircle, Globe, ExternalLink, Search } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { Button } from '@/components/Button';
import { dashboardService } from '@/services/services';
import { scoreTier } from '@/utils';

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

function getUserDisplayName(fullName: string | null | undefined, email: string | undefined): string {
  if (fullName?.trim()) return fullName.trim().split(' ')[0];
  return email?.split('@')[0] ?? 'there';
}

export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const { data: summary, isLoading: sumLoading, error: sumError, refetch: refetchSum } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const { data: recent, isLoading: recentLoading, error: recentError, refetch: refetchRecent } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(8, 0),
  });

  const summaryK = summary ?? { total_leads: 0, high_priority_leads: 0, audited_leads: 0, outreach_generated: 0, new_leads: 0, average_lead_score: 0 };
  const recentLeads = recent?.leads ?? [];
  const displayName = getUserDisplayName(user?.full_name, user?.email);
  const hasError = !!sumError || !!recentError;

  if (hasError && !summary && !recent) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <div className="p-10 text-center max-w-lg rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)]">
          <h2 className="text-[20px] font-bold text-[var(--color-text)] mb-2">Something went wrong</h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
            Unable to load dashboard data. Check your connection and try again.
          </p>
          <Button variant="primary" onClick={() => { refetchSum(); refetchRecent(); }}>
            Retry
          </Button>
        </div>
      </div>
    );
  }

  if (!sumLoading && summaryK.total_leads === 0) {
    return (
      <div className="space-y-8 lf-fade-in">
        <section>
          <h2 className="text-[var(--color-text)] text-[28px] md:text-[32px] font-semibold tracking-tight mb-2">
            {getGreeting()}, {displayName}.
          </h2>
          <p className="text-[var(--color-text-secondary)] text-[20px] font-medium opacity-80">
            Your pipeline is empty. Discover businesses to get started.
          </p>
        </section>
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="size-16 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center mx-auto mb-6">
              <Search className="size-7 text-[var(--color-brand)]" />
            </div>
            <h3 className="text-[18px] font-semibold text-[var(--color-text)] mb-2">Start your first pipeline</h3>
            <p className="text-[13px] text-[var(--color-text-muted)] mb-6 max-w-sm">
              Discover leads, run AI audits, generate websites, and convert prospects — all from one workspace.
            </p>
            <Button variant="primary" size="lg" onClick={() => navigate('/projects')} leftIcon={<Search size={16} />}>
              Discover Leads
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const accentForIndex = (i: number) => ['var(--color-brand)', 'var(--color-success)', 'var(--color-info)'][i] ?? 'var(--color-brand)';

  return (
    <div className="space-y-8 lf-fade-in">
      {/* ── Editorial Welcome ─────────────────────────────── */}
      <section>
        <h2 className="text-[var(--color-text)] text-[28px] md:text-[32px] font-semibold tracking-tight mb-2">
          {getGreeting()}, {displayName}.
        </h2>
        <p className="text-[var(--color-text-secondary)] text-[20px] font-medium opacity-80">
          The pipeline is active and generating leads.
        </p>
      </section>

      {/* ── Operational Metrics Bento ─────────────────────── */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <MetricCard
          label="Total Leads"
          value={summaryK.total_leads}
          loading={sumLoading}
          icon={Users}
          accent={accentForIndex(0)}
        />
        <MetricCard
          label="Audited"
          value={summaryK.audited_leads}
          loading={sumLoading}
          icon={CheckCircle}
          accent={accentForIndex(1)}
          detail={summaryK.total_leads > 0 ? `${Math.round((summaryK.audited_leads / summaryK.total_leads) * 100)}%` : undefined}
        />
        <MetricCard
          label="Outreach Ready"
          value={summaryK.outreach_generated}
          loading={sumLoading}
          icon={Globe}
          accent={accentForIndex(2)}
          badge={summaryK.outreach_generated > 0 ? 'Active' : undefined}
        />
      </section>

      {/* ── Bottom Split: Leads and Websites ──────────────── */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* High Priority Leads (Attio-style table) */}
        <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden flex flex-col transition-colors hover:border-[var(--color-border-strong)]">
          <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
            <h4 className="text-[13px] font-bold text-[var(--color-text)] font-mono">High Priority Leads</h4>
            <button
              onClick={() => navigate('/projects')}
              className="text-[11px] text-[var(--color-brand)] hover:underline font-medium transition-colors"
            >
              View All
            </button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {recentLoading ? (
              <div className="p-4 space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-4 py-2">
                    <Skeleton variant="circular" width={32} height={32} />
                    <div className="flex-1 space-y-2">
                      <Skeleton variant="text" width="40%" height={14} />
                      <Skeleton variant="text" width="25%" height={12} />
                    </div>
                    <Skeleton variant="rounded" width={40} height={20} />
                  </div>
                ))}
              </div>
            ) : recentLeads.length === 0 ? (
              <div className="p-10 text-center">
                <p className="text-[13px] text-[var(--color-text-muted)]">No leads yet. Start by discovering businesses.</p>
              </div>
            ) : (
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="text-[11px] text-[var(--color-text-muted)] border-b border-[var(--color-border)] bg-[var(--color-surface-hover)]">
                    <th className="px-4 py-2 font-medium font-mono">NAME</th>
                    <th className="px-4 py-2 font-medium font-mono">INDUSTRY</th>
                    <th className="px-4 py-2 font-medium font-mono">SCORE</th>
                    <th className="px-4 py-2 font-medium text-right font-mono">ACTION</th>
                  </tr>
                </thead>
                <tbody className="text-[13px]">
                  {recentLeads.map((lead) => {
                    const tier = lead.rating != null ? scoreTier(lead.rating) : null;
                    return (
                      <tr
                        key={lead.id}
                        className="border-b border-[var(--color-border)]/30 hover:bg-[var(--color-surface-hover)]/40 transition-colors cursor-pointer group"
                        onClick={() => navigate(`/project/${lead.id}`)}
                      >
                        <td className="px-4 py-3 font-medium text-[var(--color-text)]">{lead.name}</td>
                        <td className="px-4 py-3 text-[var(--color-text-secondary)]">{lead.industry || '—'}</td>
                        <td className="px-4 py-3">
                          {lead.rating != null ? (
                            <div className="flex items-center gap-1.5">
                              <span className={`w-1.5 h-1.5 rounded-full ${tier === 'hot' ? 'bg-[var(--color-success)]' : tier === 'warm' ? 'bg-[var(--color-brand)]' : 'bg-[var(--color-text-muted)]'}`} />
                              <span className="font-mono text-[12px]">{Math.round(lead.rating)}</span>
                            </div>
                          ) : (
                            <span className="text-[var(--color-text-muted)]">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <ExternalLink size={14} className="text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity inline" />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Recent Websites (Vercel-style empty state) */}
        <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] flex flex-col transition-colors hover:border-[var(--color-border-strong)]">
          <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
            <h4 className="text-[13px] font-bold text-[var(--color-text)] font-mono">Recent Websites</h4>
          </div>
          <div className="p-4 flex-1 flex items-center justify-center">
            <div className="text-center py-8">
              <div className="size-12 rounded-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center justify-center mx-auto mb-4">
                <Globe className="size-5 text-[var(--color-text-muted)]" />
              </div>
              <p className="text-[13px] text-[var(--color-text-muted)]">No websites generated yet</p>
              <p className="text-[11px] text-[var(--color-text-muted)] mt-1 opacity-70">Websites will appear here after generation</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

/* ── Metric Card (Bento style) ────────────────────────────── */
function MetricCard({ label, value, loading, icon: Icon, accent, detail, badge }: {
  label: string;
  value: number;
  loading: boolean;
  icon: React.ComponentType<{ className?: string; size?: number; color?: string }>;
  accent: string;
  detail?: string;
  badge?: string;
}) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] p-4 flex flex-col justify-between h-32 group hover:border-[var(--color-border-strong)] transition-colors">
      <div className="flex justify-between items-start">
        <p className="text-[11px] font-mono text-[var(--color-text-muted)] uppercase tracking-tighter">{label}</p>
        <Icon size={18} color={accent} className="shrink-0" />
      </div>
      <div className="flex items-end justify-between">
        <span className="text-[24px] font-bold text-[var(--color-text)] leading-none tracking-tight">
          {loading ? <Skeleton variant="text" width={50} height={28} /> : <AnimatedCounter value={value} />}
        </span>
        {detail && (
          <span className="text-[11px] font-mono text-[var(--color-text-muted)] mb-0.5">{detail}</span>
        )}
        {badge && (
          <Badge tone="success" className="text-[10px]">{badge}</Badge>
        )}
      </div>
    </div>
  );
}
