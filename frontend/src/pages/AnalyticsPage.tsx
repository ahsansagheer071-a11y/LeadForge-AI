import { useNavigate } from 'react-router-dom';
import { BarChart3, Globe, TrendingUp, Users, Activity, Zap, Search, Bot } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { dashboardService } from '@/services/services';
import { PremiumCard } from '@/components/PremiumCard';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { Badge } from '@/components/Badge';
import { ScoreGauge } from '@/components/ScoreGauge';
import { Skeleton } from '@/components/Loading';

const PIPELINE_COLORS: Record<string, string> = {
  NEW: '#3b82f6', SCRAPED: '#6366f1', ANALYZED: '#f59e0b',
  OUTREACH_READY: '#22c55e', CONTACTED: '#8b5cf6', CLOSED: '#16a34a',
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
        <PremiumCard variant="danger" innerClassName="p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-5">
            <BarChart3 className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-bold text-white mb-2">Analytics Unavailable</h2>
          <p className="text-[13px] text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
            Unable to load analytics data. Verify your connection and try again.
          </p>
          <button
            onClick={() => { refetchSum(); refetchDist(); }}
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
          <h1 className="lf-display text-white mb-1">Intelligence <span className="lf-display-gradient">Analytics</span></h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] font-mono">Live metrics from your lead pipeline</p>
        </div>
        <button
          onClick={() => navigate('/projects')}
          className="bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-5 py-2.5 rounded-[var(--radius-md)] font-bold text-[12px] shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
        >
          <Search size={14} /> Pipeline
        </button>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
        <PremiumCard variant="featured" innerClassName="p-5 lg:p-6">
          <div className="flex items-start justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Leads</span>
            <div className="size-9 rounded-[var(--radius-sm)] bg-[rgba(14,165,233,0.12)] border border-[rgba(14,165,233,0.25)] flex items-center justify-center">
              <Users size={16} className="text-[#0ea5e9]" />
            </div>
          </div>
          <div className="text-[clamp(1.8rem,3vw,2.5rem)] font-extrabold text-white leading-none">
            {isLoading ? <Skeleton variant="text" width={80} height={40} /> : <AnimatedCounter value={s.total_leads} />}
          </div>
          <div className="flex items-center gap-1.5 mt-2">
            <TrendingUp size={12} className="text-[#0ea5e9]" />
            <span className="text-[10px] font-mono text-[var(--color-text-muted)]">Total captured targets</span>
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-5 lg:p-6">
          <div className="flex items-start justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">AI Audited</span>
            <div className="size-9 rounded-[var(--radius-sm)] bg-[rgba(139,92,246,0.12)] border border-[rgba(139,92,246,0.25)] flex items-center justify-center">
              <Bot size={16} className="text-[#8b5cf6]" />
            </div>
          </div>
          <div className="text-[clamp(1.8rem,3vw,2.5rem)] font-extrabold text-white leading-none">
            {isLoading ? <Skeleton variant="text" width={60} height={40} /> : <AnimatedCounter value={s.audited_leads} />}
          </div>
          {s.total_leads > 0 && (
            <div className="flex items-center gap-1.5 mt-2">
              <div className="h-1.5 rounded-full bg-[var(--color-surface-hover)] flex-1 overflow-hidden">
                <div className="h-full rounded-full bg-gradient-to-r from-[#8b5cf6] to-[#a78bfa]" style={{ width: `${Math.round((s.audited_leads / s.total_leads) * 100)}%` }} />
              </div>
              <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{Math.round((s.audited_leads / s.total_leads) * 100)}%</span>
            </div>
          )}
        </PremiumCard>

        <PremiumCard innerClassName="p-5 lg:p-6">
          <div className="flex items-start justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Outreach Ready</span>
            <div className="size-9 rounded-[var(--radius-sm)] bg-[rgba(16,185,129,0.12)] border border-[rgba(16,185,129,0.25)] flex items-center justify-center">
              <Globe size={16} className="text-[#10b981]" />
            </div>
          </div>
          <div className="text-[clamp(1.8rem,3vw,2.5rem)] font-extrabold text-white leading-none">
            {isLoading ? <Skeleton variant="text" width={60} height={40} /> : <AnimatedCounter value={s.outreach_generated} />}
          </div>
          {s.outreach_generated > 0 && (
            <Badge tone="success" className="mt-2 text-[10px]">Active</Badge>
          )}
        </PremiumCard>

        <PremiumCard innerClassName="p-5 lg:p-6">
          <div className="flex items-start justify-between mb-3">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">New Signals</span>
            <div className="size-9 rounded-[var(--radius-sm)] bg-[rgba(6,182,212,0.12)] border border-[rgba(6,182,212,0.25)] flex items-center justify-center">
              <Activity size={16} className="text-[#06b6d4]" />
            </div>
          </div>
          <div className="text-[clamp(1.8rem,3vw,2.5rem)] font-extrabold text-white leading-none">
            {isLoading ? <Skeleton variant="text" width={60} height={40} /> : <AnimatedCounter value={s.new_leads} />}
          </div>
          {s.new_leads > 0 && (
            <Badge tone="info" animated className="mt-2 text-[10px]">Live</Badge>
          )}
        </PremiumCard>
      </div>

      {/* Second Row: Chart + Distribution + Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Flow Donut */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <BarChart3 size={14} className="text-[#0ea5e9]" /> Pipeline Flow
          </h3>
          {isLoading ? (
            <div className="h-[260px] flex items-center justify-center"><Skeleton variant="rounded" width="100%" height="100%" /></div>
          ) : statusChart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[260px] text-center">
              <BarChart3 size={32} className="text-[var(--color-text-muted)] mb-3" />
              <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No pipeline data</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={statusChart} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={65} outerRadius={90} paddingAngle={3} stroke="none">
                  {statusChart.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend iconSize={7} wrapperStyle={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </PremiumCard>

        {/* Status Distribution */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Activity size={14} className="text-[#8b5cf6]" /> Status Distribution
          </h3>
          {isLoading ? (
            <div className="space-y-4 pt-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={18} />)}</div>
          ) : !statusDist || statusDist.distribution.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[260px] text-center">
              <Activity size={28} className="text-[var(--color-text-muted)] mb-3" />
              <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No distribution data</p>
            </div>
          ) : (
            <div className="space-y-4 pt-2">
              {statusDist.distribution.map((item) => {
                const width = statusDist.total > 0 ? Math.round((item.count / statusDist.total) * 100) : 0;
                return (
                  <div key={item.label} className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono">
                      <span className="uppercase tracking-wider text-[var(--color-text-secondary)]">{item.label.replace(/_/g, ' ')}</span>
                      <span className="text-[#0ea5e9] font-semibold">{item.count}</span>
                    </div>
                    <div className="h-2 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${width}%`,
                          background: `linear-gradient(90deg, ${PIPELINE_COLORS[item.label] ?? '#6366f1'}, ${PIPELINE_COLORS[item.label] ?? '#6366f1'}88)`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </PremiumCard>

        {/* Score + Quick Stats */}
        <PremiumCard variant="featured" className="lg:col-span-1" innerClassName="p-6 flex flex-col">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Zap size={14} className="text-[#06b6d4]" /> Intelligence Summary
          </h3>
          <ScoreGauge score={s.average_lead_score ?? 0} size={120} strokeWidth={8} label="Avg Score" />
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-3 text-center">
              <p className="text-[18px] font-bold text-white">{needsAudit}</p>
              <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Need Audit</p>
            </div>
            <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-3 text-center">
              <p className="text-[18px] font-bold text-white">{pendingOutreach}</p>
              <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Pending<br />Outreach</p>
            </div>
            <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-3 text-center">
              <p className="text-[18px] font-bold text-white">{s.high_priority_leads}</p>
              <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Priority</p>
            </div>
          </div>
        </PremiumCard>
      </div>

      {/* Recent Leads */}
      <PremiumCard innerClassName="p-6">
        <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
            <Activity size={13} className="text-[#0ea5e9]" /> Recent Activity
          </h3>
          <button
            onClick={() => navigate('/projects')}
            className="text-[10px] font-mono text-[#0ea5e9] hover:underline flex items-center gap-1"
          >
            View All <TrendingUp size={10} />
          </button>
        </div>
        {recentLoading ? (
          <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={44} />)}</div>
        ) : recentLeads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-[200px] text-center">
            <Activity size={28} className="text-[var(--color-text-muted)] mb-3" />
            <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No recent leads. Start by discovering leads.</p>
            <button
              onClick={() => navigate('/projects')}
              className="mt-4 bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-5 py-2 rounded-[var(--radius-md)] font-bold text-[11px] shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
            >
              <Search size={12} /> Discover Leads
            </button>
          </div>
        ) : (
          <div className="divide-y divide-[var(--color-border)] -mx-6">
            {recentLeads.map((lead) => (
              <div
                key={lead.id}
                onClick={() => navigate(`/project/${lead.id}`)}
                className="flex items-center gap-4 px-6 py-3.5 hover:bg-[var(--color-surface-hover)] cursor-pointer transition-all group"
              >
                <div className="size-9 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center text-[12px] font-bold text-[#0ea5e9] shrink-0">
                  {lead.name[0]?.toUpperCase() ?? '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-white truncate group-hover:text-[#0ea5e9] transition-colors">{lead.name}</p>
                  <p className="text-[10px] font-mono text-[var(--color-text-muted)] truncate">{lead.industry} &middot; {lead.city}</p>
                </div>
                <Badge tone="info" className="text-[10px]">{lead.status.replace(/_/g, ' ')}</Badge>
              </div>
            ))}
          </div>
        )}
      </PremiumCard>
    </div>
  );
}
