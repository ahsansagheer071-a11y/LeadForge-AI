import { BarChart3, FolderOpenDot, Send, Sparkles, TrendingUp } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { dashboardService } from '@/services/services';
import { formatCompact, formatRelative } from '@/utils';

export function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(10, 0),
  });
  const { data: statusDistribution, isLoading: distributionLoading } = useQuery({
    queryKey: ['dashboard', 'status-distribution'],
    queryFn: () => dashboardService.statusDistribution(),
  });

  const kpiData = [
    { label: 'Total Projects', value: summary?.total_leads ?? 0, icon: FolderOpenDot, meta: `${summary?.new_leads ?? 0} new` },
    { label: 'Audited Leads', value: summary?.audited_leads ?? 0, icon: Sparkles, meta: 'analysis complete' },
    { label: 'Outreach Ready', value: summary?.outreach_generated ?? 0, icon: Send, meta: 'generated' },
    { label: 'Avg. Lead Score', value: Math.round(summary?.average_lead_score ?? 0), icon: TrendingUp, meta: `${summary?.high_priority_leads ?? 0} high priority` },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Executive overview of your workspace</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiData.map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">{kpi.label}</span>
                <div className="size-8 rounded-[8px] bg-[var(--color-brand-soft)] flex items-center justify-center">
                  <kpi.icon className="size-4 text-[var(--color-brand)]" />
                </div>
              </div>
              {summaryLoading ? (
                <Skeleton variant="text" width={96} height={30} />
              ) : (
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight">{formatCompact(kpi.value)}</span>
                  <span className="text-[11px] text-[var(--color-text-muted)]">{kpi.meta}</span>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
          </CardHeader>
          <CardContent className="min-h-48">
            {distributionLoading ? (
              <div className="space-y-3 pt-2">
                {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={18} />)}
              </div>
            ) : statusDistribution?.distribution.length ? (
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
                        <div className="h-full bg-[var(--color-brand)]" style={{ width: `${width}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState title="No status data" message="Lead status distribution will appear after leads are created." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead Score Snapshot</CardTitle>
          </CardHeader>
          <CardContent className="h-48 flex items-center justify-center">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <BarChart3 className="size-6" />
              <span className="text-[13px]">
                {summaryLoading
                  ? 'Loading score data...'
                  : `${Math.round(summary?.average_lead_score ?? 0)} average score across ${summary?.audited_leads ?? 0} audited lead(s).`}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {recentLoading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} variant="text" width="100%" height={20} />
              ))}
            </div>
          ) : !recent?.leads.length ? (
            <div className="p-8">
              <EmptyState title="No recent projects" message="Projects will appear here after leads are created." />
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {recent.leads.map((p) => (
                <div key={p.id} className="flex items-center gap-4 px-5 py-3 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium truncate">{p.name}</p>
                    <p className="text-[11.5px] text-[var(--color-text-muted)]">{p.city}, {p.country}</p>
                  </div>
                  <Badge tone={p.status === 'OUTREACH_READY' ? 'success' : p.status === 'ANALYZED' ? 'warning' : 'neutral'}>{p.status}</Badge>
                  <span className="text-[11px] text-[var(--color-text-muted)]">{formatRelative(p.created_at)}</span>
                  {p.rating != null && (
                    <span className="text-[12px] font-semibold text-amber-500">* {p.rating.toFixed(1)}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
