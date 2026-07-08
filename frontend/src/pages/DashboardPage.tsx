import { Sparkles, TrendingUp, Search, Bot, MessageSquare, Download, ArrowRight, Zap, Target, BarChart3, Activity, Users, Globe } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { Card, CardContent } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { PremiumCard } from '@/components/PremiumCard';
import { AnimatedCounter } from '@/components/AnimatedCounter';
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

function KpiSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}><CardContent className="p-4"><Skeleton variant="rounded" width="100%" height={100} /></CardContent></Card>
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
  const avgScore = summaryK.average_lead_score;

  const statusChart = (statusDistribution?.distribution ?? []).map((d) => ({
    name: d.label.replace('_', ' '),
    value: d.count,
    fill: PIPELINE_COLORS[d.label] ?? '#6366f1',
  }));
  const chartsLoading = distLoading;

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      {/* ── Hero ─────────────────────────── */}
      <div className="flex flex-wrap items-end justify-between gap-6 pb-7 border-b border-[var(--color-border)]">
        <div>
          <p className="text-[11px] font-medium text-[var(--color-text-muted)] uppercase tracking-[0.08em] mb-2">{getGreeting()}</p>
          <h1 className="text-[clamp(1.75rem,4vw,2.25rem)] font-bold tracking-tight leading-tight mb-1.5">{displayName}</h1>
          <p className="text-[12.5px] text-[var(--color-text-muted)]">Discover &bull; Analyze &bull; Convert</p>
        </div>
      </div>

      {/* ── Executive summary ──────────── */}
      {sumLoading ? (
        <div className="rounded-[16px] border border-[var(--color-border)] p-7 bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-hover)]">
          <Skeleton variant="text" width={120} height={36} />
          <Skeleton variant="text" width="60%" height={16} className="mt-3" />
        </div>
      ) : (
        <div className="rounded-[16px] border border-[var(--color-border)] p-7 bg-gradient-to-br from-[var(--color-surface)] to-[var(--color-surface-hover)] flex flex-wrap items-center justify-between gap-6 shadow-sm">
          <div>
            <p className="text-[14px] font-semibold mb-2">Welcome back.</p>
            <div className="text-[clamp(2rem,5vw,2.75rem)] font-extrabold tracking-tight bg-gradient-to-r from-[var(--color-brand)] to-[var(--color-brand-400)] bg-clip-text text-transparent leading-none">
              <AnimatedCounter value={summaryK.high_priority_leads} />
            </div>
            <p className="text-[13px] text-[var(--color-text-secondary)] mt-1.5">High Priority Leads</p>
            <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5">
              Score 80+ &middot; {summaryK.total_leads} total in pipeline
              {avgScore > 0 && ` · Avg score ${avgScore.toFixed(1)}`}
            </p>
          </div>
        </div>
      )}

      {/* ── KPI Cards ──────────────────── */}
      {sumLoading ? (
        <KpiSkeleton />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <PremiumCard innerClassName="p-4 flex flex-col gap-3.5 min-h-[120px]">
            <div className="flex items-start justify-between gap-2">
              <span className="text-[12.5px] font-medium text-[var(--color-text-secondary)]">Total Leads</span>
              <div className="size-9 rounded-[10px] flex items-center justify-center shrink-0" style={{ background: 'rgba(37,99,235,0.12)', border: '1px solid rgba(37,99,235,0.2)' }}>
                <Users size={17} color="#2563eb" />
              </div>
            </div>
            <div className="text-[2rem] font-bold tracking-tight leading-none text-[var(--color-text)]">
              <AnimatedCounter value={summaryK.total_leads} />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--color-text-muted)]">
              <TrendingUp size={11} /> Pipeline total
            </span>
          </PremiumCard>

          <PremiumCard innerClassName="p-4 flex flex-col gap-3.5 min-h-[120px]">
            <div className="flex items-start justify-between gap-2">
              <span className="text-[12.5px] font-medium text-[var(--color-text-secondary)]">High Priority</span>
              <div className="size-9 rounded-[10px] flex items-center justify-center shrink-0" style={{ background: 'rgba(34,197,94,0.12)', border: '1px solid rgba(34,197,94,0.2)' }}>
                <Target size={17} color="#22c55e" />
              </div>
            </div>
            <div className="text-[2rem] font-bold tracking-tight leading-none text-[var(--color-text)]">
              <AnimatedCounter value={summaryK.high_priority_leads} />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--color-success)]">
              <TrendingUp size={11} /> Score &ge; 80
            </span>
          </PremiumCard>

          <PremiumCard innerClassName="p-4 flex flex-col gap-3.5 min-h-[120px]">
            <div className="flex items-start justify-between gap-2">
              <span className="text-[12.5px] font-medium text-[var(--color-text-secondary)]">AI Audited</span>
              <div className="size-9 rounded-[10px] flex items-center justify-center shrink-0" style={{ background: 'rgba(124,58,237,0.12)', border: '1px solid rgba(124,58,237,0.2)' }}>
                <Bot size={17} color="#7c3aed" />
              </div>
            </div>
            <div className="text-[2rem] font-bold tracking-tight leading-none text-[var(--color-text)]">
              <AnimatedCounter value={summaryK.audited_leads} />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--color-text-muted)]">
              {summaryK.new_leads} awaiting review
            </span>
          </PremiumCard>

          <PremiumCard innerClassName="p-4 flex flex-col gap-3.5 min-h-[120px]">
            <div className="flex items-start justify-between gap-2">
              <span className="text-[12.5px] font-medium text-[var(--color-text-secondary)]">Outreach Ready</span>
              <div className="size-9 rounded-[10px] flex items-center justify-center shrink-0" style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.2)' }}>
                <MessageSquare size={17} color="#6366f1" />
              </div>
            </div>
            <div className="text-[2rem] font-bold tracking-tight leading-none text-[var(--color-text)]">
              <AnimatedCounter value={summaryK.outreach_generated} />
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[var(--color-text-muted)]">
              AI-generated templates
            </span>
          </PremiumCard>
        </div>
      )}

      {/* ── Quick actions ──────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {[
          { label: 'Discover Leads', icon: Search, path: '/projects' },
          { label: 'Run AI Audit', icon: Bot, path: '/projects' },
          { label: 'Generate Outreach', icon: MessageSquare, path: '/projects' },
          { label: 'Export CSV', icon: Download, path: '/projects' },
        ].map((action) => (
          <button
            key={action.label}
            type="button"
            onClick={() => navigate(action.path)}
            className="flex items-center justify-center gap-2.5 py-4 px-4.5 rounded-[12px] border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] text-[13px] font-semibold cursor-pointer transition-all duration-200 hover:scale-[1.02] hover:-translate-y-0.5 hover:border-[var(--color-brand-border)] hover:shadow-md active:scale-[0.99] shadow-sm"
          >
            <action.icon size={18} className="text-[var(--color-brand)] shrink-0" />
            {action.label}
          </button>
        ))}
      </div>

      {/* ── Pipeline Analytics ─────────── */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-[15px] font-semibold tracking-tight">Pipeline Analytics</h2>
            <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5">Where your leads are and how they score</p>
          </div>
        </div>
        {chartsLoading ? (
          <div className="text-[13px] text-[var(--color-text-muted)] text-center py-6">Loading analytics&hellip;</div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Lead Pipeline Pie */}
            <div className="rounded-[14px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
              <h3 className="text-[14px] font-semibold mb-4">Lead Pipeline</h3>
              {statusChart.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
                  <div className="size-12 rounded-[12px] border border-[var(--color-border)] flex items-center justify-center bg-[var(--color-surface-hover)]">
                    <BarChart3 size={22} className="text-[var(--color-text-muted)]" />
                  </div>
                  <p className="text-[13px] font-semibold text-[var(--color-text)]">No pipeline data yet</p>
                  <p className="text-[12px] text-[var(--color-text-muted)] max-w-[260px]">Discover leads to see how they move through your funnel.</p>
                  <button type="button" onClick={() => navigate('/projects')} className="text-[12px] text-[var(--color-brand)] font-medium hover:underline">Discover leads</button>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie data={statusChart} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={56} outerRadius={84} paddingAngle={2} stroke="none">
                      {statusChart.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                    <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 11, color: 'var(--color-text-muted)', paddingTop: 8 }} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Lead Score Gauge */}
            <div className="rounded-[14px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
              <h3 className="text-[14px] font-semibold mb-4">Lead Score</h3>
              <p className="text-[11.5px] text-[var(--color-text-muted)] mb-4">Average AI quality across scored leads</p>
              {avgScore <= 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
                  <div className="size-12 rounded-[12px] border border-[var(--color-border)] flex items-center justify-center bg-[var(--color-surface-hover)]">
                    <Target size={22} className="text-[var(--color-text-muted)]" />
                  </div>
                  <p className="text-[13px] font-semibold text-[var(--color-text)]">No scores yet</p>
                  <p className="text-[12px] text-[var(--color-text-muted)] max-w-[260px]">Run AI audits on your leads to generate quality scores.</p>
                  <button type="button" onClick={() => navigate('/projects')} className="text-[12px] text-[var(--color-brand)] font-medium hover:underline">Run AI audit</button>
                </div>
              ) : (
                <>
                  <ScoreGauge score={avgScore} />
                  <p className="text-[11.5px] text-[var(--color-text-muted)] text-center">{summaryK.high_priority_leads} leads scored 80+</p>
                </>
              )}
            </div>

            {/* Status Distribution (bar) */}
            {statusDistribution && statusDistribution.distribution.length > 0 && (
              <div className="rounded-[14px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
                <h3 className="text-[14px] font-semibold mb-4">Status Distribution</h3>
                <div className="space-y-3">
                  {statusDistribution.distribution.map((item) => {
                    const width = statusDistribution.total > 0 ? Math.round((item.count / statusDistribution.total) * 100) : 0;
                    return (
                      <div key={item.label} className="space-y-1">
                        <div className="flex items-center justify-between text-[12px]">
                          <span>{item.label.replace(/_/g, ' ')}</span>
                          <span className="text-[var(--color-text-muted)]">{item.count}</span>
                        </div>
                        <div className="h-2 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
                          <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${width}%`, background: PIPELINE_COLORS[item.label] ?? 'var(--color-brand)' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recent Activity */}
            <div className="rounded-[14px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-sm">
              <h3 className="text-[14px] font-semibold mb-4">Recent Activity</h3>
              {recentLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={20} />)}
                </div>
              ) : recentLeads.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-10 text-center gap-3">
                  <div className="size-12 rounded-[12px] border border-[var(--color-border)] flex items-center justify-center bg-[var(--color-surface-hover)]">
                    <Activity size={22} className="text-[var(--color-text-muted)]" />
                  </div>
                  <p className="text-[13px] font-semibold text-[var(--color-text)]">No activity yet</p>
                  <p className="text-[12px] text-[var(--color-text-muted)] max-w-[260px]">Your timeline fills as you discover and process leads.</p>
                  <button type="button" onClick={() => navigate('/projects')} className="text-[12px] text-[var(--color-brand)] font-medium hover:underline">Discover Leads</button>
                </div>
              ) : (
                <div className="divide-y divide-[var(--color-border)]">
                  {recentLeads.slice(0, 6).map((lead) => (
                    <div
                      key={lead.id}
                      onClick={() => navigate(`/project/${lead.id}`)}
                      onKeyDown={(e) => e.key === 'Enter' && navigate(`/project/${lead.id}`)}
                      role="button"
                      tabIndex={0}
                      className="flex items-center gap-3.5 py-3 cursor-pointer hover:opacity-80 transition-opacity"
                    >
                      <div className="size-9 rounded-[10px] flex items-center justify-center shrink-0 bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                        <Globe size={15} className="text-[var(--color-brand)]" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[13px] font-semibold text-[var(--color-text)] truncate">{lead.name}</p>
                        <p className="text-[11.5px] text-[var(--color-text-muted)]">{lead.industry} &middot; {lead.city}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <Badge tone={lead.status === 'OUTREACH_READY' ? 'success' : lead.status === 'ANALYZED' ? 'warning' : 'neutral'}>{lead.status.replace('_', ' ')}</Badge>
                        <p className="text-[11px] text-[var(--color-text-muted)] mt-1">{formatRelative(lead.created_at)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── High Priority Leads ────────── */}
      {priorityLeads.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-[15px] font-semibold tracking-tight">High Priority Leads</h2>
              <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5">Top-scored opportunities</p>
            </div>
            <button type="button" onClick={() => navigate('/projects')} className="text-[11.5px] text-[var(--color-brand)] font-medium hover:underline">View all</button>
          </div>
          <div className="rounded-[14px] border border-[var(--color-border)] overflow-hidden bg-[var(--color-surface)]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="text-[11px] font-semibold text-[var(--color-text-muted)] uppercase tracking-[0.06em] bg-[var(--color-surface-hover)]">
                  <th className="text-left px-4.5 py-3">Business</th>
                  <th className="text-left px-4.5 py-3">Industry</th>
                  <th className="text-left px-4.5 py-3">Location</th>
                  <th className="text-left px-4.5 py-3">Status</th>
                  <th className="text-left px-4.5 py-3">Rating</th>
                </tr>
              </thead>
              <tbody>
                {priorityLeads.map((lead) => (
                  <tr
                    key={lead.id}
                    onClick={() => navigate(`/project/${lead.id}`)}
                    className="cursor-pointer transition-colors hover:bg-[var(--color-surface-hover)]"
                  >
                    <td className="px-4.5 py-3.5 text-[13px] font-semibold text-[var(--color-text)] border-b border-[var(--color-border)]">{lead.name}</td>
                    <td className="px-4.5 py-3.5 text-[13px] text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">{lead.industry}</td>
                    <td className="px-4.5 py-3.5 text-[13px] text-[var(--color-text-secondary)] border-b border-[var(--color-border)]">{lead.city}, {lead.country}</td>
                    <td className="px-4.5 py-3.5 border-b border-[var(--color-border)]"><Badge tone={lead.status === 'OUTREACH_READY' ? 'success' : lead.status === 'ANALYZED' ? 'warning' : 'neutral'}>{lead.status.replace('_', ' ')}</Badge></td>
                    <td className="px-4.5 py-3.5 border-b border-[var(--color-border)]">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/15 text-emerald-500 border border-emerald-500/25">HOT</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── AI Insights ════════════════ */}
      <PremiumCard innerClassName="p-5">
        <div className="flex flex-wrap items-start gap-5">
          <div className="size-11 rounded-[12px] flex items-center justify-center shrink-0 bg-gradient-to-br from-[var(--color-brand-soft)] to-[var(--color-brand-subtle)] border border-[var(--color-brand-border)]">
            <Sparkles size={22} color="#818cf8" />
          </div>
          <div className="flex-1 min-w-[200px]">
            <div className="text-[14px] font-semibold text-[var(--color-text)] mb-2">
              <Zap size={14} className="inline mr-1.5 align-[-2px]" />
              AI Insights
            </div>
            <p className="text-[13px] font-semibold text-[var(--color-text)] mb-1.5">{insight.title}</p>
            <p className="text-[12.5px] text-[var(--color-text-secondary)] leading-relaxed mb-4">{insight.body}</p>
            <button type="button" onClick={() => navigate(insight.path)} className="inline-flex items-center gap-1.5 text-[12px] font-medium text-[var(--color-brand)] hover:underline">
              {insight.cta} <ArrowRight size={13} />
            </button>
          </div>
        </div>
      </PremiumCard>
    </div>
  );
}
