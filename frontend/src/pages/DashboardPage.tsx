import { Sparkles, TrendingUp, Bot, MessageSquare, BarChart3, Globe, Zap, Search, Activity, ArrowRight, CircleDot } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { PremiumCard } from '@/components/PremiumCard';
import { ScoreGauge } from '@/components/ScoreGauge';
import { dashboardService, projectsService } from '@/services/services';
import { formatRelative } from '@/utils';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

const PIPELINE_COLORS: Record<string, string> = {
  NEW: '#3b82f6', SCRAPED: '#6366f1', ANALYZED: '#f59e0b',
  OUTREACH_READY: '#22c55e', CONTACTED: '#8b5cf6', CLOSED: '#16a34a',
};
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

function getAiInsight(summary: {
  total_leads: number; high_priority_leads: number; audited_leads: number;
  outreach_generated: number; new_leads: number;
}): { title: string; body: string; cta: string; path: string; urgency: 'critical' | 'opportunity' | 'info' } {
  if (summary.high_priority_leads > 0) return {
    title: 'Priority action recommended',
    body: `You have ${summary.high_priority_leads} high-priority lead${summary.high_priority_leads !== 1 ? 's' : ''} waiting. These scored 80+ on AI audit — ideal candidates for personalized outreach today.`,
    cta: 'Review high-priority leads', path: '/projects', urgency: 'critical',
  };
  if (summary.audited_leads > summary.outreach_generated) return {
    title: 'Outreach opportunity detected',
    body: `${summary.audited_leads - summary.outreach_generated} audited business${summary.audited_leads - summary.outreach_generated !== 1 ? 'es' : ''} still need outreach. Generate AI-crafted emails to convert analysis into conversations.`,
    cta: 'Generate outreach', path: '/projects', urgency: 'opportunity',
  };
  if (summary.total_leads > 0 && summary.audited_leads === 0) return {
    title: 'Unlock AI intelligence',
    body: 'Your pipeline has leads without AI audits. Run website analysis and scoring to uncover weaknesses, opportunities, and conversion gaps.',
    cta: 'Run AI audit', path: '/projects', urgency: 'info',
  };
  if (summary.new_leads > 0) return {
    title: 'Fresh leads need attention',
    body: `${summary.new_leads} new lead${summary.new_leads !== 1 ? 's' : ''} in your pipeline. Start with website analysis to prioritize who to contact first.`,
    cta: 'Analyze websites', path: '/projects', urgency: 'info',
  };
  return {
    title: 'Start building your pipeline',
    body: 'Discover businesses on Google Maps, run AI audits, and generate outreach — all from one workspace. Your next high-value lead is one search away.',
    cta: 'Discover leads', path: '/projects', urgency: 'info',
  };
}

function ChartTooltipBase({ active, payload, label }: {
  active?: boolean; payload?: Array<{ value: number; name: string; color?: string }>; label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[var(--radius-md)] bg-[var(--color-surface-overlay)] backdrop-blur-xl border border-[var(--color-border-strong)] p-3 text-[12px] shadow-[var(--shadow-pop)]">
      {label && <div className="text-[var(--color-text-muted)] mb-1.5 font-medium font-mono text-[11px] uppercase tracking-wider">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="font-semibold flex items-center gap-2" style={{ color: p.color ?? 'var(--color-text)' }}>
          <span className="size-1.5 rounded-full shrink-0" style={{ background: p.color ?? 'var(--color-text)' }} />
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}

/* ── Quick action tiles ─────────────────────────────────────── */
const QUICK_ACTIONS = [
  { icon: Search, label: 'Discover Leads', desc: 'Find new businesses', path: '/projects', color: '#0ea5e9' },
  { icon: Activity, label: 'Review Pipeline', desc: 'Manage your leads', path: '/projects', color: '#8b5cf6' },
  { icon: Sparkles, label: 'Generate Website', desc: 'AI-powered builder', path: '/generation', color: '#06b6d4' },
  { icon: BarChart3, label: 'Open Analytics', desc: 'View performance', path: '/analytics', color: '#10b981' },
];

/* ── Main DashboardPage ─────────────────────────────────────── */
export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const { data: summary, isLoading: sumLoading, error: sumError, refetch: refetchSum } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const { data: recent, isLoading: recentLoading, error: recentError, refetch: refetchRecent } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(10, 0),
  });
  const { data: statusDistribution, isLoading: distLoading, error: distError, refetch: refetchDist } = useQuery({
    queryKey: ['dashboard', 'status-distribution'],
    queryFn: () => dashboardService.statusDistribution(),
  });

  const { data: priorityData } = useQuery({
    queryKey: ['leads', 'dashboard-priority'],
    queryFn: () => projectsService.list(1, 100),
  });

  /* ── Derived data ────────────────────────────────────────── */
  const summaryK = summary ?? { total_leads: 0, high_priority_leads: 0, audited_leads: 0, outreach_generated: 0, new_leads: 0, average_lead_score: 0 };
  const recentLeads = recent?.leads ?? [];
  const priorityLeads = (priorityData?.items ?? []).filter((l) => l.rating != null && l.rating >= 4.0).slice(0, 8);
  const displayName = getUserDisplayName(user?.full_name, user?.email);
  const insight = getAiInsight(summaryK);
  const chartsLoading = distLoading || sumLoading;
  const hasError = !!sumError || !!recentError || !!distError;

  const statusChart = (statusDistribution?.distribution ?? []).map((d) => ({
    name: d.label.replace('_', ' '),
    value: d.count,
    fill: PIPELINE_COLORS[d.label] ?? '#6366f1',
  }));

  const pendingOutreach = Math.max(0, summaryK.audited_leads - summaryK.outreach_generated);
  const needsAudit = Math.max(0, summaryK.total_leads - summaryK.audited_leads);

  /* ── Error state ─────────────────────────────────────────── */
  if (hasError && !summary && !recent && !statusDistribution) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <PremiumCard variant="danger" innerClassName="p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-5">
            <BarChart3 className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-bold text-white mb-2">Connection Interrupted</h2>
          <p className="text-[13px] text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
            Unable to establish a secure link with the intelligence server. Verify your connection and try again.
          </p>
          <button
            onClick={() => { refetchSum(); refetchRecent(); refetchDist(); }}
            className="bg-gradient-to-r from-[var(--color-brand)] to-[var(--color-brand-600)] text-white px-6 py-2.5 rounded-[var(--radius-md)] font-medium hover:-translate-y-0.5 transition-all"
          >
            Re-establish Link
          </button>
        </PremiumCard>
      </div>
    );
  }

  /* ── Empty state ──────────────────────────────────────────── */
  if (!sumLoading && summaryK.total_leads === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <PremiumCard variant="featured" innerClassName="p-12 text-center max-w-xl">
          <div className="size-20 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(14,165,233,0.2)]">
            <Sparkles className="size-8 text-[#0ea5e9]" />
          </div>
          <h2 className="text-[24px] font-bold text-white mb-3">Your command center is ready</h2>
          <p className="text-[14px] text-[var(--color-text-secondary)] mb-8 max-w-md mx-auto leading-relaxed">
            Discover businesses on Google Maps, run AI-powered audits, generate premium websites, and convert leads with automated outreach.
          </p>
          <button
            onClick={() => navigate('/projects')}
            className="bg-gradient-to-r from-[#0ea5e9] to-[#06b6d4] text-white px-8 py-3 rounded-[var(--radius-md)] font-bold shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 transition-all inline-flex items-center gap-2"
          >
            <Search size={16} /> Start Discovery
          </button>
        </PremiumCard>
      </div>
    );
  }

  return (
    <div className="space-y-8 lf-fade-in">
      {/* ═══════════════════════════════════════════════════════════
         HERO COMMAND PANEL
      ════════════════════════════════════════════════════════════ */}
      <PremiumCard variant="featured" innerClassName="relative overflow-hidden">
        {/* Animated background orbs */}
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-[rgba(14,165,233,0.06)] blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-[rgba(139,92,246,0.05)] blur-[80px] pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full opacity-[0.015] pointer-events-none" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px)', backgroundSize: '40px 40px' }} />

        {/* Scanline */}
        <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.08) 2px, rgba(255,255,255,0.08) 4px)' }} />

        <div className="relative z-10 p-8 lg:p-12">
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-8">
            {/* Left content */}
            <div className="flex-1 max-w-2xl">
              <div className="flex items-center gap-3 mb-4">
                <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#0ea5e9] flex items-center gap-2">
                  <span className="size-1.5 rounded-full bg-[#0ea5e9] shadow-[0_0_6px_#0ea5e9]" />
                  {getGreeting()}, {displayName}
                </span>
                <span className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider border border-[var(--color-border)] rounded-full px-2 py-0.5">
                  v2.0
                </span>
              </div>

              <h1 className="lf-display text-white mb-3">
                Intelligence<br />
                <span className="lf-display-gradient">Command Center</span>
              </h1>

              <p className="text-[14px] text-[var(--color-text-secondary)] font-mono max-w-xl leading-relaxed mb-8">
                System active. {summaryK.total_leads > 0 ? `${summaryK.total_leads} targets in the network.` : 'Awaiting initial target acquisition.'} {summaryK.new_leads > 0 && `${summaryK.new_leads} new signal${summaryK.new_leads !== 1 ? 's' : ''} detected.`}
              </p>

              {/* Quick actions */}
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => navigate('/projects')}
                  className="bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-6 py-3 rounded-[var(--radius-md)] font-bold shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 transition-all flex items-center gap-2"
                >
                  <Search size={16} /> Initialize Discovery
                </button>
                {summaryK.total_leads > 0 && (
                  <button
                    onClick={() => navigate('/generation')}
                    className="bg-[var(--color-glass)] backdrop-blur-md text-[var(--color-text)] border border-[var(--color-glass-border)] px-6 py-3 rounded-[var(--radius-md)] font-medium hover:bg-[var(--color-glass-strong)] hover:-translate-y-0.5 transition-all flex items-center gap-2"
                  >
                    <Sparkles size={16} /> Generate Assets
                  </button>
                )}
              </div>
            </div>

            {/* Right: Priority metric */}
            <div className="flex flex-col items-end gap-4 shrink-0">
              <div className="text-right">
                <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] mb-2">Priority Targets</p>
                <div className="text-[clamp(3.5rem,6vw,5rem)] font-extrabold text-white leading-none drop-shadow-[0_0_30px_rgba(14,165,233,0.5)]">
                  {sumLoading ? <Skeleton variant="text" width={100} height={70} /> : <AnimatedCounter value={summaryK.high_priority_leads} />}
                </div>
                {!sumLoading && (
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-mono text-[#0ea5e9] mt-2">
                    <CircleDot className="size-3" /> 
                    {summaryK.high_priority_leads > 0 ? 'Requires immediate attention' : 'No hot targets'}
                  </span>
                )}
              </div>

              {/* Orbital data-flow visual */}
              <div className="relative size-20 hidden lg:block">
                <div className="absolute inset-0 rounded-full border border-[var(--color-border-strong)] opacity-30" />
                <div className="absolute inset-2 rounded-full border border-[var(--color-border)] opacity-20" />
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#0ea5e9] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '4s' }} />
                <div className="absolute inset-3 rounded-full border border-transparent border-b-[#06b6d4] border-l-[#06b6d4] animate-spin" style={{ animationDuration: '6s', animationDirection: 'reverse' }} />
                <div className="absolute inset-[calc(50%-3px)] size-1.5 rounded-full bg-[#0ea5e9] shadow-[0_0_10px_#0ea5e9]" />
              </div>
            </div>
          </div>
        </div>
      </PremiumCard>

      {/* ═══════════════════════════════════════════════════════════
         BENTO KPI AREA
      ════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4 lg:gap-6">
        {/* Featured — Total Intelligence */}
        <PremiumCard variant="featured" className="md:col-span-3 lg:col-span-2 md:row-span-2" innerClassName="p-7 lg:p-8 flex flex-col justify-between min-h-[260px]">
          <div className="flex items-start justify-between">
            <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Total Intelligence</span>
            <div className="size-11 rounded-[var(--radius-md)] flex items-center justify-center shrink-0 bg-[rgba(14,165,233,0.12)] border border-[rgba(14,165,233,0.25)] shadow-[0_0_12px_rgba(14,165,233,0.15)]">
              <Globe size={20} className="text-[#0ea5e9]" />
            </div>
          </div>
          <div>
            <div className="lf-metric text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.15)]">
              {sumLoading ? <Skeleton variant="text" width={90} height={60} /> : <AnimatedCounter value={summaryK.total_leads} />}
            </div>
            <div className="flex items-center gap-2 text-[12px] font-mono text-[#0ea5e9] mt-2">
              <TrendingUp size={13} /> Total captured targets
            </div>
          </div>
        </PremiumCard>

        {/* AI Audited */}
        <PremiumCard className="md:col-span-3 lg:col-span-2" innerClassName="p-6 flex flex-col justify-between min-h-[120px]">
          <div className="flex items-start justify-between">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">AI Audited</span>
            <Bot size={16} className="text-[#8b5cf6]" />
          </div>
          <div className="flex items-end justify-between">
            <div className="text-[28px] font-bold tracking-tight text-white">
              {sumLoading ? <Skeleton variant="text" width={50} height={32} /> : <AnimatedCounter value={summaryK.audited_leads} />}
            </div>
            {!sumLoading && summaryK.total_leads > 0 && (
              <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
                {Math.round((summaryK.audited_leads / summaryK.total_leads) * 100)}% complete
              </span>
            )}
          </div>
        </PremiumCard>

        {/* Outreach Ready */}
        <PremiumCard className="md:col-span-3 lg:col-span-2" innerClassName="p-6 flex flex-col justify-between min-h-[120px]">
          <div className="flex items-start justify-between">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Outreach Ready</span>
            <MessageSquare size={16} className="text-[#10b981]" />
          </div>
          <div className="flex items-end justify-between">
            <div className="text-[28px] font-bold tracking-tight text-white">
              {sumLoading ? <Skeleton variant="text" width={50} height={32} /> : <AnimatedCounter value={summaryK.outreach_generated} />}
            </div>
            {!sumLoading && summaryK.outreach_generated > 0 && (
              <Badge tone="success" className="text-[10px]">Active</Badge>
            )}
          </div>
        </PremiumCard>

        {/* New Leads */}
        <PremiumCard className="md:col-span-3 lg:col-span-2" innerClassName="p-6 flex flex-col justify-between min-h-[120px]">
          <div className="flex items-start justify-between">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">New Signals</span>
            <Activity size={16} className="text-[#06b6d4]" />
          </div>
          <div className="flex items-end justify-between">
            <div className="text-[28px] font-bold tracking-tight text-white">
              {sumLoading ? <Skeleton variant="text" width={50} height={32} /> : <AnimatedCounter value={summaryK.new_leads} />}
            </div>
            {!sumLoading && summaryK.new_leads > 0 && (
              <Badge tone="info" animated>Live</Badge>
            )}
          </div>
        </PremiumCard>

        {/* Score Gauge */}
        <PremiumCard className="md:col-span-3 lg:col-span-2" innerClassName="p-6 flex items-center justify-center min-h-[120px]">
          <ScoreGauge score={summaryK.average_lead_score ?? 0} size={110} strokeWidth={8} label="Avg Score" />
        </PremiumCard>
      </div>

      {/* ═══════════════════════════════════════════════════════════
         MIDDLE: CHARTS + AI INSIGHT
      ════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Flow (Donut) */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <BarChart3 size={14} className="text-[#0ea5e9]" /> Pipeline Flow
          </h3>
          {chartsLoading ? (
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
                <Tooltip content={<ChartTooltipBase />} />
                <Legend iconSize={7} wrapperStyle={{ fontSize: 11, fontFamily: 'JetBrains Mono, monospace', color: 'var(--color-text-secondary)' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </PremiumCard>

        {/* Status Distribution (Bar) */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Activity size={14} className="text-[#8b5cf6]" /> Status Distribution
          </h3>
          {chartsLoading ? (
            <div className="space-y-4 pt-4">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={18} />)}</div>
          ) : !statusDistribution || statusDistribution.distribution.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[260px] text-center">
              <Activity size={28} className="text-[var(--color-text-muted)] mb-3" />
              <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No distribution data</p>
            </div>
          ) : (
            <div className="space-y-4 pt-2">
              {statusDistribution.distribution.map((item) => {
                const width = statusDistribution.total > 0 ? Math.round((item.count / statusDistribution.total) * 100) : 0;
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

        {/* AI Insight */}
        <PremiumCard variant={insight.urgency === 'critical' ? 'featured' : 'standard'} className="lg:col-span-1" innerClassName="p-6 flex flex-col">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2" style={{ color: insight.urgency === 'critical' ? '#0ea5e9' : 'var(--color-text-muted)' }}>
            <Zap size={14} /> AI Directive
            {insight.urgency === 'critical' && <span className="size-1.5 rounded-full bg-red-500 shadow-[0_0_6px_red] animate-pulse" />}
          </h3>
          <p className="text-[17px] font-bold text-white mb-3 leading-tight">{insight.title}</p>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 leading-relaxed flex-1">{insight.body}</p>

          {/* Supporting metrics */}
          {summaryK.total_leads > 0 && (
            <div className="grid grid-cols-3 gap-3 mb-5">
              <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-2.5 text-center">
                <p className="text-[16px] font-bold text-white">{needsAudit}</p>
                <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Need Audit</p>
              </div>
              <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-2.5 text-center">
                <p className="text-[16px] font-bold text-white">{pendingOutreach}</p>
                <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Pending<br />Outreach</p>
              </div>
              <div className="bg-[var(--color-surface-hover)] rounded-[var(--radius-sm)] p-2.5 text-center">
                <p className="text-[16px] font-bold text-white">{Math.round(summaryK.average_lead_score)}</p>
                <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Avg Score</p>
              </div>
            </div>
          )}

          <button
            onClick={() => navigate(insight.path)}
            className="w-full bg-gradient-to-r from-[var(--color-brand-soft)] to-transparent border border-[var(--color-brand-border)] text-[#0ea5e9] py-3 rounded-[var(--radius-md)] font-mono text-[11px] uppercase tracking-wider hover:bg-[var(--color-brand-subtle)] transition-all flex items-center justify-center gap-2"
          >
            {insight.cta} <ArrowRight size={14} />
          </button>
        </PremiumCard>
      </div>

      {/* ═══════════════════════════════════════════════════════════
         BOTTOM: PRIORITY + RECENT + QUICK ACTIONS
      ════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority Matrix */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
            <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
              <CircleDot size={13} className="text-[#10b981]" /> Priority Matrix
            </h3>
            {priorityLeads.length > 0 && (
              <Badge tone="success" animated>{priorityLeads.length} hot</Badge>
            )}
          </div>
          {priorityLeads.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[200px] text-center">
              <CircleDot size={28} className="text-[var(--color-text-muted)] mb-3" />
              <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No high-priority targets</p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[400px] overflow-y-auto lf-thin-scroll pr-1">
              {priorityLeads.map((lead) => (
                <div
                  key={lead.id}
                  onClick={() => navigate(`/project/${lead.id}`)}
                  className="flex items-center justify-between p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] cursor-pointer transition-all border border-transparent hover:border-[rgba(14,165,233,0.2)] group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="size-8 rounded-full bg-gradient-to-br from-[#10b981]/20 to-[#059669]/20 border border-[#10b981]/30 flex items-center justify-center text-[11px] font-bold text-[#10b981] shrink-0">
                      {lead.name[0]?.toUpperCase() ?? '?'}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-semibold text-white truncate">{lead.name}</p>
                      <p className="text-[10px] font-mono text-[var(--color-text-muted)] truncate">{lead.industry}</p>
                    </div>
                  </div>
                  <Badge tone="success" className="shrink-0 text-[10px] group-hover:shadow-[0_0_12px_rgba(34,197,94,0.4)] transition-shadow">HOT</Badge>
                </div>
              ))}
            </div>
          )}
        </PremiumCard>

        {/* Recent Intel */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
            <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
              <Activity size={13} className="text-[#0ea5e9]" /> Recent Intel
            </h3>
            {recentLeads.length > 0 && !recentLoading && (
              <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{recent?.total ?? 0} total</span>
            )}
          </div>
          {recentLoading ? (
            <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={48} />)}</div>
          ) : recentLeads.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[200px] text-center">
              <Activity size={28} className="text-[var(--color-text-muted)] mb-3" />
              <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No recent activity</p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[400px] overflow-y-auto lf-thin-scroll pr-1">
              {recentLeads.slice(0, 6).map((lead) => (
                <div
                  key={lead.id}
                  onClick={() => navigate(`/project/${lead.id}`)}
                  className="flex items-center justify-between p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] cursor-pointer transition-all border border-transparent hover:border-[rgba(14,165,233,0.2)] group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="size-8 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center text-[11px] font-bold text-[#0ea5e9] shrink-0">
                      {lead.name[0]?.toUpperCase() ?? '?'}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13px] font-semibold text-white truncate">{lead.name}</p>
                      <p className="text-[10px] font-mono text-[#0ea5e9] truncate">{lead.status.replace(/_/g, ' ')}</p>
                    </div>
                  </div>
                  <span className="text-[9px] font-mono text-[var(--color-text-muted)] shrink-0">{formatRelative(lead.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </PremiumCard>

        {/* Quick Actions */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-5 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
            <Zap size={13} className="text-[#06b6d4]" /> Quick Actions
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {QUICK_ACTIONS.map((action) => (
              <button
                key={action.label}
                onClick={() => navigate(action.path)}
                className="flex flex-col items-center justify-center gap-2 p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] border border-transparent hover:border-[rgba(14,165,233,0.2)] transition-all group"
              >
                <div
                  className="size-10 rounded-[var(--radius-sm)] flex items-center justify-center transition-all group-hover:scale-110"
                  style={{ background: `${action.color}15`, border: `1px solid ${action.color}30` }}
                >
                  <action.icon size={18} style={{ color: action.color }} />
                </div>
                <span className="text-[11px] font-semibold text-white">{action.label}</span>
                <span className="text-[9px] font-mono text-[var(--color-text-muted)]">{action.desc}</span>
              </button>
            ))}
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}
