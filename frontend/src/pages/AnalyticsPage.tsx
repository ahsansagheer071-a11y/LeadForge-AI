import { BarChart3, TrendingUp, Users, Globe } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';

import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';
import { Skeleton } from '@/components/Loading';

export function AnalyticsPage() {
  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });

  const stats = [
    { label: 'Total Leads', value: summary?.total_leads ?? 0, icon: Users },
    { label: 'AI Audited', value: summary?.audited_leads ?? 0, icon: BarChart3 },
    { label: 'Outreach Ready', value: summary?.outreach_generated ?? 0, icon: Globe },
    { label: 'Avg. Score', value: Math.round(summary?.average_lead_score ?? 0), icon: TrendingUp },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Analytics</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Usage metrics and performance insights</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card variant="glass" key={i}>
              <CardContent className="p-4"><Skeleton variant="rounded" width="100%" height={60} /></CardContent>
            </Card>
          ))
        ) : (
          stats.map((s) => (
            <Card variant="glass" key={s.label}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">{s.label}</span>
                  <div className="size-8 rounded-[8px] bg-[var(--color-brand-soft)] flex items-center justify-center">
                    <s.icon className="size-4 text-[var(--color-brand)]" />
                  </div>
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight">{s.value}</span>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      <Card variant="glass">
        <CardHeader>
          <CardTitle>More analytics coming soon</CardTitle>
        </CardHeader>
        <CardContent className="h-40 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-[var(--color-text-muted)]">
            <BarChart3 className="size-8 text-[var(--color-brand-soft)]" />
            <span className="text-[13px]">Detailed charts will be available in a future update.</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
