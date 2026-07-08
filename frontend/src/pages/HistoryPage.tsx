import { Clock, Filter } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/ErrorStates';

import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';
import { formatRelative } from '@/utils';
import { Skeleton } from '@/components/Loading';

export function HistoryPage() {
  const { data: recent, isLoading } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(50, 0),
  });

  const historyItems = (recent?.leads ?? []).map((lead) => ({
    id: lead.id,
    action: lead.status === 'NEW' ? 'Lead discovered' : `Lead updated to ${lead.status.replace('_', ' ')}`,
    project: lead.name,
    status: lead.status === 'OUTREACH_READY' ? 'success' : lead.status === 'FAILED' ? 'danger' : 'info',
    time: formatRelative(lead.created_at),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">History</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Track all actions across your workspace</p>
        </div>
        <Button variant="outline" size="sm" leftIcon={<Filter className="size-3.5" />}>Filter</Button>
      </div>

      <Card variant="glass">
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 space-y-4">
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} variant="text" width="100%" height={24} delay={i*60} />)}
            </div>
          ) : historyItems.length === 0 ? (
            <div className="p-8">
              <EmptyState title="No history yet" message="Actions will appear here as you use the workspace." />
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {historyItems.map((item) => (
                <div key={item.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <div className="size-8 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center flex-shrink-0">
                    <Clock className="size-4 text-[var(--color-text-muted)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium">{item.action}</p>
                    <p className="text-[11.5px] text-[var(--color-text-muted)]">{item.project}</p>
                  </div>
                  <Badge tone={item.status as 'success'|'danger'|'info'}>{item.status}</Badge>
                  <span className="text-[11px] text-[var(--color-text-muted)]">{item.time}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
