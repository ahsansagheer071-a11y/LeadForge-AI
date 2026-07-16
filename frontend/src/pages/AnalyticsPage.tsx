import { useNavigate } from 'react-router-dom';
import { BarChart3, TrendingUp, Users, Bot, Globe, Zap } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { dashboardService } from '@/services/services';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { Badge } from '@/components/Badge';
import { ScoreGauge } from '@/components/ScoreGauge';
import { Skeleton } from '@/components/Loading';

const PIPELINE_COLORS: Record<string, string> = {
  NEW: '#3b82f6',
  SCRAPED: '#8b5cf6',
  ANALYZED: '#f59e0b',
  OUTREACH_READY: '#10b981',
  CONTACTED: '#8b5cf6',
  CLOSED: '#22c55e',
};

function ChartTooltip({ active, payload }: {
  active?: boolean; payload?: Array<{ value: number; name: string; color?: string }>;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--radius-md)] bg-[var(--color-surface-overlay)] backdrop-blur-xl border border-[var(--color-border-strong)] p-3 text-[12px] shadow-[var(--shadow-pop)]">
      {payload.map((p, i) => (
        <div key={i} className="font-semibold flex items-center gap-2" style={{ color: p.color ?? 'var(--color-text)' }}>
          <span className="size-1.5 rounded-full shrink-0" style={{ background: p.color ?? 'var(--color-text)' }} />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPage() {
  const navigate = useNavigate();

  const { data: summary, isLoading: sumLoading, error: sumError, refetch: refetchSum } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const { data: statusDist, isLoading: distLoading, error: distError, refetch: refetchDist } = useQuery({
    queryKey: ['analytics', 'status-distribution'],
    queryFn: () => dashboardService.statusDistribution(),
  });
  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['analytics', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(5, 0),
  });

  const s = summary ?? { total_leads: 0, new_leads: 0, audited_leads: 0, outreach_generated: 0, average_lead_score: 0, high_priority_leads: 0 };
  const hasError = !!sumError || !!distError;
  const isLoading = sumLoading || distLoading;
  const recentLeads = recent?.leads ?? [];

  const statusChart = (statusDist?.distribution ?? []).map((d) => ({
    name: d.label.replace(/_/g, ' '),
    value: d.count,
    fill: PIPELINE_COLORS[d.label] ?? '#6366f1',
  }));

  const pendingOutreach = Math.max(0, s.audited_leads - s.outreach_generated);
  const needsAudit = Math.max(0, s.total_leads - s.audited_leads);

  if (hasError && !summary && !statusDist) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5">
            <BarChart3 className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-semibold text-[var(--color-text)] mb-2">Analytics Unavailable</h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
            Unable to load analytics data. Verify your connection and try again.
          </p>
          <button
            onClick={() => { refetchSum(); refetchDist(); }}
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
      <div>
        <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Analytics</h1>
        <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Operational metrics from your lead pipeline</p>
      </div>

      {/* ── Metric Cards ────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<Users size={16} className="text-[var(--color-brand)]" />}
          label="Total Leads"
          value={isLoading ? null : <AnimatedCounter value={s.total_leads} />}
          loading={isLoading}
        />
        <MetricCard
          icon={<Bot size={16} className="text-purple-400" />}
          label="AI Audited"
          value={isLoading ? null : <AnimatedCounter value={s.audited_leads} />}
          loading={isLoading}
          progress={s.total_leads > 0 ? Math.round((s.audited_leads / s.total_leads) * 100) : undefined}
        />
        <MetricCard
          icon={<Globe size={16} className="text-emerald-400" />}
          label="Outreach Ready"
          value={isLoading ? null : <AnimatedCounter value={s.outreach_generated} />}
          loading={isLoading}
          badge={s.outreach_generated > 0 ? 'Active' : undefined}
          badgeTone="success"
        />
        <MetricCard
          icon={<Zap size={16} className="text-amber-400" />}
          label="New Leads"
          value={isLoading ? null : <AnimatedCounter value={s.new_leads} />}
          loading={isLoading}
        />
      </div>

      {/* ── Charts Row ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Pipeline Donut */}
        <Panel title="Pipeline Flow" icon={<BarChart3 size={14} className="text-[var(--color-text-muted)]" />}>
          {isLoading ? (
            <div className="h-[240px] flex items-center justify-center"><Skeleton variant="rounded" width="100%" height="100%" /></div>
          ) : statusChart.length === 0 ? (
            <EmptyChartState icon={<BarChart3 size={28} />} message="No pipeline data" />
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={statusChart} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={85} paddingAngle={3} stroke="none">
                  {statusChart.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend iconSize={7} wrapperStyle={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Panel>

        {/* Status Distribution */}
        <Panel title="Status Distribution" icon={<TrendingUp size={14} className="text-[var(--color-text-muted)]" />}>
          {isLoading ? (
            <div className="space-y-4 pt-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={18} />)}</div>
          ) : !statusDist || statusDist.distribution.length === 0 ? (
            <EmptyChartState icon={<TrendingUp size={28} />} message="No distribution data" />
          ) : (
            <div className="space-y-3.5 pt-1">
              {statusDist.distribution.map((item) => {
                const pct = statusDist.total > 0 ? Math.round((item.count / statusDist.total) * 100) : 0;
                return (
                  <div key={item.label} className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="text-[var(--color-text-secondary)]">{item.label.replace(/_/g, ' ')}</span>
                      <span className="text-[var(--color-text)] font-semibold">{item.count}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${pct}%`,
                          background: PIPELINE_COLORS[item.label] ?? '#6366f1',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Panel>

        {/* Score + Quick Stats */}
        <Panel title="Intelligence Summary" icon={<Zap size={14} className="text-[var(--color-text-muted)]" />}>
          <div className="flex flex-col items-center">
            <ScoreGauge score={s.average_lead_score ?? 0} size={110} strokeWidth={7} label="Avg Score" />
            <div className="grid grid-cols-3 gap-2.5 mt-4 w-full">
              <StatCell value={needsAudit} label="Need Audit" />
              <StatCell value={pendingOutreach} label="Pending Outreach" />
              <StatCell value={s.high_priority_leads} label="Priority" />
            </div>
          </div>
        </Panel>
      </div>

      {/* ── Recent Leads ─────────────────────────────────────── */}
      <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
        <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
          <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">Recent Activity</h3>
          <button
            onClick={() => navigate('/projects')}
            className="text-[11px] font-mono text-[var(--color-brand)] hover:underline flex items-center gap-1"
          >
            View All <TrendingUp size={10} />
          </button>
        </div>
        {recentLoading ? (
          <div className="p-4 space-y-2.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton variant="rounded" width={32} height={32} />
                <div className="flex-1 space-y-1.5">
                  <Skeleton variant="text" width="40%" height={13} />
                  <Skeleton variant="text" width="25%" height={11} />
                </div>
              </div>
            ))}
          </div>
        ) : recentLeads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No recent leads. Start by discovering leads.</p>
            <button
              onClick={() => navigate('/projects')}
              className="mt-3 text-[12px] font-medium text-[var(--color-brand)] hover:underline"
            >
              Discover Leads
            </button>
          </div>
        ) : (
          <div className="divide-y divide-[var(--color-border)]">
            {recentLeads.map((lead) => (
              <div
                key={lead.id}
                onClick={() => navigate(`/project/${lead.id}`)}
                className="flex items-center gap-3 px-4 py-3 hover:bg-[var(--color-surface-hover)] cursor-pointer transition-colors group"
              >
                <div className="size-8 rounded-lg bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center text-[11px] font-bold text-[var(--color-brand)] shrink-0">
                  {lead.name[0]?.toUpperCase() ?? '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-medium text-[var(--color-text)] truncate group-hover:text-[var(--color-brand)] transition-colors">
                    {lead.name}
                  </p>
                  <p className="text-[10px] font-mono text-[var(--color-text-muted)] truncate">
                    {lead.industry} &middot; {lead.city}
                  </p>
                </div>
                <Badge tone="info" className="text-[10px]">{lead.status.replace(/_/g, ' ')}</Badge>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────── */

function Panel({ title, icon, children }: { title: string; icon?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center gap-2">
        {icon}
        <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function MetricCard({ icon, label, value, loading, progress, badge, badgeTone }: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode | null;
  loading?: boolean;
  progress?: number;
  badge?: string;
  badgeTone?: 'success' | 'warning' | 'danger' | 'info' | 'muted';
}) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] p-4 hover:border-[var(--color-border-strong)] transition-colors">
      <div className="flex items-start justify-between mb-3">
        <span className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">{label}</span>
        <div className="size-8 rounded-[var(--radius-sm)] bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center justify-center">
          {icon}
        </div>
      </div>
      <div className="text-[24px] font-bold text-[var(--color-text)] leading-none">
        {loading ? <Skeleton variant="text" width={60} height={30} /> : value}
      </div>
      {progress != null && progress > 0 && (
        <div className="flex items-center gap-2 mt-2.5">
          <div className="h-1.5 rounded-full bg-[var(--color-surface-hover)] flex-1 overflow-hidden">
            <div className="h-full rounded-full bg-[var(--color-brand)]" style={{ width: `${progress}%` }} />
          </div>
          <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{progress}%</span>
        </div>
      )}
      {badge && badgeTone && (
        <Badge tone={badgeTone} className="mt-2 text-[10px]">{badge}</Badge>
      )}
    </div>
  );
}

function StatCell({ value, label }: { value: number; label: string }) {
  return (
    <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-md)] p-2.5 text-center">
      <p className="text-[18px] font-bold text-[var(--color-text)]">{value}</p>
      <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider leading-tight">{label}</p>
    </div>
  );
}

function EmptyChartState({ icon, message }: { icon: React.ReactNode; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[240px] text-center">
      <div className="text-[var(--color-text-muted)] mb-3">{icon}</div>
      <p className="text-[12px] font-mono text-[var(--color-text-muted)]">{message}</p>
    </div>
  );
}
