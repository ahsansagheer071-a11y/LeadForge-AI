import { X, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn, formatRelative } from '@/utils';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';
import { Separator } from '@/components/Separator';



export function RightActivityPanel({
  open,
  onClose,
  className,
}: {
  open: boolean;
  onClose: () => void;
  className?: string;
}) {
  const { data } = useQuery({
    queryKey: ['dashboard', 'recent-leads'],
    queryFn: () => dashboardService.recentLeads(10, 0),
  });
  const items = data?.leads ?? [];

  return (
    <aside
      className={cn(
        'h-[calc(100vh-3.5rem)] w-[320px] border-l border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md z-20',
        'flex flex-col overflow-hidden transition-all duration-300 ease-out',
        open ? 'opacity-100' : 'opacity-0 pointer-events-none w-0',
        'lf-thin-scroll',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 pt-4 pb-2">
        <div className="flex items-center gap-2">
          <Activity className="size-4 text-[var(--color-brand)]" />
          <span className="text-[13px] font-semibold">Activity</span>
        </div>
        <button
          onClick={onClose}
          className="size-7 rounded-[6px] flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
          aria-label="Close activity panel"
        >
          <X className="size-3.5" />
        </button>
      </div>

      <Separator />

      {/* Feed */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="size-10 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center mb-2">
              <Activity className="size-4 text-[var(--color-text-muted)]" />
            </div>
            <p className="text-[12.5px] text-[var(--color-text-muted)]">No recent activity</p>
          </div>
        ) : (
          items.map((n) => <ActivityItem key={n.id} item={n} />)
        )}
      </div>
    </aside>
  );
}

function ActivityItem({ item }: { item: any }) {
  const Icon = item.status === 'OUTREACH_READY' ? CheckCircle2 : item.status === 'FAILED' ? AlertCircle : Activity;
  const kind = item.status === 'OUTREACH_READY' ? 'success' : item.status === 'FAILED' ? 'error' : 'info';
  return (
    <div
      className={cn(
        'group flex items-start gap-3 px-3 py-2.5 rounded-[10px] transition-colors',
        'hover:bg-[var(--color-surface-hover)]',
        'hover:bg-[var(--color-surface-hover)]',
      )}
    >
      <div className="mt-0.5">
        <Icon className={cn('size-4', kind === 'success' && 'text-[var(--color-success)]', kind === 'error' && 'text-[var(--color-danger)]', kind === 'info' && 'text-[var(--color-brand)]')} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-[12.5px] font-medium truncate">{item.name}</p>
        </div>
        <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5 line-clamp-2">
          {item.status === 'NEW' ? 'Lead discovered' : `Lead updated to ${item.status.replace('_', ' ')}`}
        </p>
        <p className="text-[10.5px] text-[var(--color-text-muted)] mt-0.5">{formatRelative(item.created_at)}</p>
      </div>
    </div>
  );
}
