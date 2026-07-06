import { BarChart3, TrendingUp, Users, Globe } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';

const stats = [
  { label: 'Total Generations', value: '142', icon: BarChart3, change: '+18%' },
  { label: 'Active Users', value: '8', icon: Users, change: '+2' },
  { label: 'Deployments', value: '37', icon: Globe, change: '+5' },
  { label: 'Avg. Score', value: '68', icon: TrendingUp, change: '+4%' },
];

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Analytics</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Usage metrics and performance insights</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">{s.label}</span>
                <div className="size-8 rounded-[8px] bg-[var(--color-brand-soft)] flex items-center justify-center">
                  <s.icon className="size-4 text-[var(--color-brand)]" />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight">{s.value}</span>
                <span className="text-[11px] text-[var(--color-success)]">{s.change}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Generations Over Time</CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <BarChart3 className="size-6" />
              <span className="text-[13px]">Chart placeholder</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Lead Score Trends</CardTitle>
          </CardHeader>
          <CardContent className="h-64 flex items-center justify-center">
            <div className="flex items-center gap-3 text-[var(--color-text-muted)]">
              <TrendingUp className="size-6" />
              <span className="text-[13px]">Chart placeholder</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
