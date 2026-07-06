import { useEffect, useState } from 'react';
import { BarChart3, FolderOpenDot, Sparkles, Globe, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { projectsService } from '@/services/services';
import { formatRelative, formatCompact } from '@/utils';
import type { LeadResponse } from '@/types';

const kpiData = [
  { label: 'Total Projects', value: 24, icon: FolderOpenDot, change: '+12%', tone: 'brand' as const },
  { label: 'Active Generations', value: 3, icon: Sparkles, change: '+2', tone: 'info' as const },
  { label: 'Deployments Live', value: 7, icon: Globe, change: '+3', tone: 'success' as const },
  { label: 'Avg. Lead Score', value: 74, icon: TrendingUp, change: '+5%', tone: 'warning' as const },
];

export function DashboardPage() {
  const [projects, setProjects] = useState<LeadResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsService.list().then((paginated) => {
      setProjects(paginated.items);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Executive overview of your workspace</p>
      </div>

      {/* KPI Grid */}
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
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight">{kpi.value}</span>
                <span className="text-[11px] text-[var(--color-success)]">{kpi.change}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Generations (7d)</CardTitle>
          </CardHeader>
          <CardContent className="h-48 flex items-center justify-center">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <BarChart3 className="size-6" />
              <span className="text-[13px]">Chart placeholder</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead Score Distribution</CardTitle>
          </CardHeader>
          <CardContent className="h-48 flex items-center justify-center">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <BarChart3 className="size-6" />
              <span className="text-[13px]">Chart placeholder</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} variant="text" width="100%" height={20} />
              ))}
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {projects.map((p) => (
                <div key={p.id} className="flex items-center gap-4 px-5 py-3 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium truncate">{p.name}</p>
                    <p className="text-[11.5px] text-[var(--color-text-muted)]">{p.website ?? '—'}</p>
                  </div>
                  <Badge tone={p.status === 'deployed' ? 'success' : p.status === 'failed' ? 'danger' : p.status === 'generating' ? 'info' : 'neutral'}>{p.status}</Badge>
                  <span className="text-[11px] text-[var(--color-text-muted)]">{formatRelative(p.updated_at)}</span>
                  {p.rating != null && (
                    <span className="text-[12px] font-semibold text-amber-500">★ {p.rating.toFixed(1)}</span>
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
