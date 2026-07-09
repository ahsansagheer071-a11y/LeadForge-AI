import { Sparkles, TrendingUp, Bot, MessageSquare, BarChart3, Globe, Zap } from 'lucide-react';
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
}): { title: string; body: string; cta: string; path: string } {
  if (summary.high_priority_leads > 0) return {
    title: 'Priority action recommended',
    body: `You have ${summary.high_priority_leads} high-priority lead${summary.high_priority_leads !== 1 ? 's' : ''} waiting. These scored 80+ on AI audit — ideal candidates for personalized outreach today.`,
    cta: 'Review high-priority leads', path: '/projects',
  };
  if (summary.audited_leads > summary.outreach_generated) return {
    title: 'Outreach opportunity detected',
    body: `${summary.audited_leads - summary.outreach_generated} audited business${summary.audited_leads - summary.outreach_generated !== 1 ? 'es' : ''} still need outreach. Generate AI-crafted emails to convert analysis into conversations.`,
    cta: 'Generate outreach', path: '/projects',
  };
  if (summary.total_leads > 0 && summary.audited_leads === 0) return {
    title: 'Unlock AI intelligence',
    body: 'Your pipeline has leads without AI audits. Run website analysis and scoring to uncover weaknesses, opportunities, and conversion gaps.',
    cta: 'Run AI audit', path: '/projects',
  };
  if (summary.new_leads > 0) return {
    title: 'Fresh leads need attention',
    body: `${summary.new_leads} new lead${summary.new_leads !== 1 ? 's' : ''} in your pipeline. Start with website analysis to prioritize who to contact first.`,
    cta: 'Analyze websites', path: '/projects',
  };
  return {
    title: 'Start building your pipeline',
    body: 'Discover businesses on Google Maps, run AI audits, and generate outreach — all from one workspace. Your next high-value lead is one search away.',
    cta: 'Discover leads', path: '/projects',
  };
}

function ChartTooltip({ active, payload, label }: {
  active?: boolean; payload?: Array<{ value: number; name: string; color?: string }>; label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-[10px] bg-[var(--color-surface-overlay)] border border-[var(--color-border)] p-2.5 text-[12px] shadow-lg backdrop-blur-sm">
      {label && <div className="text-[var(--color-text-muted)] mb-1.5 font-medium">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="font-semibold" style={{ color: p.color ?? 'var(--color-text)' }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
}


export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);

  const { data: summary, isLoading: sumLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(10, 0),
  });
  const { data: statusDistribution, isLoading: distLoading } = useQuery({
    queryKey: ['dashboard', 'status-distribution'],
    queryFn: () => dashboardService.statusDistribution(),
  });

  const { data: priorityData } = useQuery({
    queryKey: ['leads', 'dashboard-priority'],
    queryFn: () => projectsService.list(1, 100),
  });

  const summaryK = summary ?? { total_leads: 0, high_priority_leads: 0, audited_leads: 0, outreach_generated: 0, new_leads: 0, average_lead_score: 0 };
  const recentLeads = recent?.leads ?? [];
  const priorityLeads = (priorityData?.items ?? []).filter((l) => l.rating != null && l.rating >= 4.0).slice(0, 8);
  const displayName = getUserDisplayName(user?.full_name, user?.email);
  const insight = getAiInsight(summaryK);
  

  const statusChart = (statusDistribution?.distribution ?? []).map((d) => ({
    name: d.label.replace('_', ' '),
    value: d.count,
    fill: PIPELINE_COLORS[d.label] ?? '#6366f1',
  }));
  const chartsLoading = distLoading;

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      {/* ── Top Section: Hero Command Panel ─────────────────────────── */}
      <div className="relative rounded-[24px] overflow-hidden bg-gradient-to-br from-[#0f172a] to-[#020617] border border-[var(--color-border)] shadow-2xl p-8 lg:p-12 group">
        <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_top_right,rgba(14,165,233,0.15),transparent_50%)] transition-opacity duration-700 group-hover:opacity-70" />
        <div className="absolute inset-0 z-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(139,92,246,0.15),transparent_50%)] transition-opacity duration-700 group-hover:opacity-70" />
        
        {/* Animated grid background */}
        <div className="absolute inset-0 z-0 opacity-[0.03] bg-[url('data:image/svg+xml;utf8,<svg width=%2240%22 height=%2240%22 xmlns=%22http://www.w3.org/2000/svg%22><g fill=%22%23fff%22 fill-rule=%22evenodd%22><path d=%22M0 0h40v40H0zM19 19h2v2h-2z%22/></g></svg>')] animate-[lf-slide-in-right_20s_linear_infinite]" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-8">
          <div>
            <p className="text-[#0ea5e9] font-mono text-[12px] uppercase tracking-[0.2em] mb-3">{getGreeting()}, {displayName}</p>
            <h1 className="text-[clamp(2.5rem,5vw,3.5rem)] font-extrabold tracking-tight leading-none mb-4 text-white drop-shadow-md">
              Command <span className="bg-gradient-to-r from-[#0ea5e9] to-[#8b5cf6] bg-clip-text text-transparent">Center</span>
            </h1>
            <p className="text-[15px] text-slate-400 max-w-xl font-mono">
              SYSTEM ACTIVE. ANALYZING {summaryK.total_leads} TARGETS. {summaryK.new_leads} AWAITING DISCOVERY.
            </p>
            <div className="mt-8 flex gap-4">
              <button onClick={() => navigate('/projects')} className="bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-6 py-3 rounded-[12px] font-bold shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] transition-all flex items-center gap-2">
                <Sparkles size={18} /> Initialize Discovery
              </button>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[12px] text-slate-400 font-mono uppercase tracking-widest mb-2">Priority Targets</p>
            <div className="text-[clamp(4rem,8vw,6rem)] font-bold text-white leading-none drop-shadow-[0_0_40px_rgba(14,165,233,0.6)]">
              {sumLoading ? <Skeleton variant="text" width={100} height={80} /> : <AnimatedCounter value={summaryK.high_priority_leads} />}
            </div>
          </div>
        </div>
      </div>

      {/* ── KPI Section: Asymmetrical Grid ─────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <PremiumCard featured className="md:col-span-2 md:row-span-2" innerClassName="p-8 flex flex-col justify-between min-h-[240px]">
          <div className="flex items-start justify-between gap-2">
            <span className="text-[14px] font-mono uppercase tracking-wider text-[var(--color-text-secondary)]">Total Intelligence</span>
            <div className="size-12 rounded-[14px] flex items-center justify-center shrink-0" style={{ background: 'rgba(14,165,233,0.15)', border: '1px solid rgba(14,165,233,0.3)' }}>
              <Globe size={24} className="text-[#0ea5e9]" />
            </div>
          </div>
          <div>
            <div className="text-[clamp(3rem,5vw,4.5rem)] font-bold tracking-tight leading-none text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">
              {sumLoading ? <Skeleton variant="text" width={80} height={60} /> : <AnimatedCounter value={summaryK.total_leads} />}
            </div>
            <span className="inline-flex items-center gap-2 text-[13px] font-mono text-[#0ea5e9] mt-3">
              <TrendingUp size={14} /> Total captured websites
            </span>
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-6 flex flex-col justify-between min-h-[140px] md:col-span-2">
          <div className="flex items-start justify-between gap-2">
            <span className="text-[12px] font-mono uppercase tracking-wider text-[var(--color-text-secondary)]">AI Audited</span>
            <Bot size={18} className="text-[#8b5cf6]" />
          </div>
          <div className="text-[2rem] font-bold tracking-tight leading-none text-white mt-2">
            {sumLoading ? <Skeleton variant="text" width={40} height={30} /> : <AnimatedCounter value={summaryK.audited_leads} />}
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-6 flex flex-col justify-between min-h-[140px] md:col-span-2">
          <div className="flex items-start justify-between gap-2">
            <span className="text-[12px] font-mono uppercase tracking-wider text-[var(--color-text-secondary)]">Outreach Ready</span>
            <MessageSquare size={18} className="text-[#10b981]" />
          </div>
          <div className="text-[2rem] font-bold tracking-tight leading-none text-white mt-2">
            {sumLoading ? <Skeleton variant="text" width={40} height={30} /> : <AnimatedCounter value={summaryK.outreach_generated} />}
          </div>
        </PremiumCard>
      </div>

      {/* ── Middle Section: Pipeline, AI Insight, Score ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Chart */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[14px] font-mono uppercase tracking-widest mb-6 text-white border-b border-[var(--color-border)] pb-3">Pipeline Flow</h3>
          {chartsLoading ? (
             <div className="h-[240px] flex items-center justify-center"><Skeleton variant="rounded" width="100%" height="100%" /></div>
          ) : statusChart.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[240px] text-center">
               <BarChart3 size={32} className="text-slate-600 mb-3" />
               <p className="text-[13px] font-mono text-slate-400">NO DATA ACQUIRED</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={statusChart} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={3} stroke="none">
                  {statusChart.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                </Pie>
                <Tooltip content={<ChartTooltip />} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: 11, fontFamily: 'monospace' }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </PremiumCard>

        {/* Status Distribution */}
        <PremiumCard className="lg:col-span-1" innerClassName="p-6">
          <h3 className="text-[14px] font-mono uppercase tracking-widest mb-6 text-white border-b border-[var(--color-border)] pb-3">Status Distribution</h3>
          {chartsLoading ? (
            <div className="space-y-4">{Array.from({ length: 4 }).map((_,i) => <Skeleton key={i} variant="text" width="100%" height={16} />)}</div>
          ) : (
            <div className="space-y-4">
              {statusDistribution?.distribution.map((item) => {
                const width = statusDistribution.total > 0 ? Math.round((item.count / statusDistribution.total) * 100) : 0;
                return (
                  <div key={item.label} className="space-y-1.5">
                    <div className="flex items-center justify-between text-[11px] font-mono uppercase">
                      <span>{item.label.replace(/_/g, ' ')}</span>
                      <span className="text-[#0ea5e9]">{item.count}</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-[#0ea5e9] to-[#8b5cf6]" style={{ width: `${width}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </PremiumCard>

        {/* AI Insight */}
        <PremiumCard featured className="lg:col-span-1" innerClassName="p-6 bg-gradient-to-b from-[#0a0f1a] to-[#040810]">
          <h3 className="text-[14px] font-mono uppercase tracking-widest mb-6 text-[#0ea5e9] border-b border-[#0ea5e9]/20 pb-3 flex items-center gap-2">
            <Zap size={16} /> AI Directive
          </h3>
          <p className="text-[18px] font-bold text-white mb-3 leading-tight">{insight.title}</p>
          <p className="text-[14px] text-slate-400 mb-8 leading-relaxed">{insight.body}</p>
          <button onClick={() => navigate(insight.path)} className="w-full bg-[#1e293b] hover:bg-[#334155] border border-slate-700 text-white py-3 rounded-[10px] font-mono text-[12px] uppercase tracking-wider transition-colors">
            {insight.cta}
          </button>
        </PremiumCard>
      </div>

      {/* ── ScoreGauge ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <PremiumCard className="lg:col-span-1 flex items-center justify-center" innerClassName="p-6 flex flex-col items-center justify-center">
          <ScoreGauge score={summaryK.average_lead_score ?? 0} />
        </PremiumCard>

      {/* ── Bottom Section: Recent Leads & High Priority ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:col-span-2">
        <PremiumCard innerClassName="p-6">
          <div className="flex items-center justify-between mb-6 border-b border-[var(--color-border)] pb-3">
            <h3 className="text-[14px] font-mono uppercase tracking-widest text-white">Priority Matrix</h3>
          </div>
          {priorityLeads.length === 0 ? (
            <p className="text-[13px] text-slate-500 font-mono">No hot targets identified.</p>
          ) : (
            <div className="space-y-3">
              {priorityLeads.map(lead => (
                <div key={lead.id} onClick={() => navigate(`/project/${lead.id}`)} className="flex items-center justify-between p-3 rounded-[10px] bg-[var(--color-surface-hover)] hover:bg-[#1e293b] cursor-pointer transition-colors border border-transparent hover:border-slate-700">
                  <div>
                    <p className="text-[14px] font-bold text-white">{lead.name}</p>
                    <p className="text-[11px] font-mono text-slate-400">{lead.industry}</p>
                  </div>
                  <Badge tone="success" className="shadow-[0_0_10px_rgba(34,197,94,0.3)]">HOT</Badge>
                </div>
              ))}
            </div>
          )}
        </PremiumCard>

        <PremiumCard innerClassName="p-6">
          <div className="flex items-center justify-between mb-6 border-b border-[var(--color-border)] pb-3">
            <h3 className="text-[14px] font-mono uppercase tracking-widest text-white">Recent Intel</h3>
          </div>
          {recentLoading ? (
            <Skeleton variant="text" width="100%" height={100} />
          ) : recentLeads.length === 0 ? (
             <p className="text-[13px] text-slate-500 font-mono">No recent activity.</p>
          ) : (
            <div className="space-y-3">
              {recentLeads.slice(0, 5).map(lead => (
                <div key={lead.id} onClick={() => navigate(`/project/${lead.id}`)} className="flex items-center justify-between p-3 rounded-[10px] bg-[var(--color-surface-hover)] hover:bg-[#1e293b] cursor-pointer transition-colors border border-transparent hover:border-slate-700">
                  <div>
                    <p className="text-[14px] font-bold text-white">{lead.name}</p>
                    <p className="text-[11px] font-mono text-[#0ea5e9]">{lead.status.replace('_', ' ')}</p>
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{formatRelative(lead.created_at)}</span>
                </div>
              ))}
            </div>
          )}
        </PremiumCard>
      </div>
    </div>

    </div>
  );
}
