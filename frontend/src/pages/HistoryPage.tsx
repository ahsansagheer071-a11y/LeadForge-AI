import { Clock, Filter } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { EmptyState } from '@/components/ErrorStates';

const historyItems = [
  { action: 'Generated website', project: 'Acme Coffee Roasters', status: 'success', time: '2h ago' },
  { action: 'Deployed to Vercel', project: 'Acme Coffee Roasters', status: 'success', time: '1h ago' },
  { action: 'Preview failed', project: 'Northwind Logistics', status: 'failed', time: '3h ago' },
  { action: 'New project created', project: 'Boulder Yoga Studio', status: 'info', time: '1d ago' },
  { action: 'Lead score updated', project: 'Pinecrest Dental', status: 'info', time: '2d ago' },
];

export function HistoryPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">History</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Track all actions across your workspace</p>
        </div>
        <Button variant="outline" size="sm" leftIcon={<Filter className="size-3.5" />}>Filter</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity Log</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {historyItems.length === 0 ? (
            <div className="p-8">
              <EmptyState title="No history yet" message="Actions will appear here as you use the workspace." />
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {historyItems.map((item, i) => (
                <div key={i} className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <div className="size-8 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center flex-shrink-0">
                    <Clock className="size-4 text-[var(--color-text-muted)]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium">{item.action}</p>
                    <p className="text-[11.5px] text-[var(--color-text-muted)]">{item.project}</p>
                  </div>
                  <Badge tone={item.status === 'success' ? 'success' : item.status === 'failed' ? 'danger' : 'info'}>{item.status}</Badge>
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
