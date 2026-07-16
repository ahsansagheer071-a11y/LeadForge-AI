import { X, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { cn, formatRelative } from '@/utils';
import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '@/services/services';

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
        'h-[calc(100vh-3.5rem)] w-[320px] border-l border-[var(--color-border)] bg-[var(--color-surface)] z-20',
        'flex flex-col overflow-hidden transition-all duration-[var(--anim-normal)] ease-[var(--anim-ease-out)]',
        open ? 'opacity-100' : 'opacity-0 pointer-events-none w-0',
        'lf-thin-scroll',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-3">
          <Activity className="size-4 text-[var(--color-text-muted)]" />
          <span className="text-[13px] font-medium tracking-wide text-[var(--color-text)]">Activity</span>
        </div>
        <button
          onClick={onClose}
          className="size-7 rounded-[8px] flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
        >
          <X className="size-3.5" />
        </button>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-2">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="size-12 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center mb-3">
              <Activity className="size-5 text-[var(--color-text-muted)]" />
            </div>
            <p className="text-[12.5px] text-[var(--color-text-muted)]">No recent activity</p>
          </div>
        ) : (
          items.map((n, i) => <ActivityItem key={n.id} item={n} index={i} />)
        )}
      </div>
    </aside>
  );
}

function ActivityItem({ item, index }: { item: any; index: number }) {
  const isSuccess = item.status === 'OUTREACH_READY';
  const isError = item.status === 'FAILED';
  const Icon = isSuccess ? CheckCircle2 : isError ? AlertCircle : Activity;
  const colorClass = isSuccess
    ? 'text-emerald-500'
    : isError
      ? 'text-red-500'
      : 'text-[var(--color-brand)]';
  const bgClass = isSuccess
    ? 'bg-emerald-500/10'
    : isError
      ? 'bg-red-500/10'
      : 'bg-[var(--color-brand-soft)]';

  return (
    <div
      className="group flex items-start gap-3 px-3 py-3 rounded-[12px] transition-colors bg-[var(--color-surface-hover)]/50 border border-[var(--color-border)]/50 hover:bg-[var(--color-surface-hover)]"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className={cn("mt-0.5 size-7 rounded-[6px] flex items-center justify-center shrink-0", bgClass)}>
        <Icon className={cn('size-3.5', colorClass)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-medium text-[var(--color-text)] truncate">{item.name}</p>
        <p className="text-[11px] text-[var(--color-text-muted)] mt-1 line-clamp-1 uppercase tracking-wider">
          {item.status === 'NEW' ? 'Lead discovered' : `${item.status.replace('_', ' ')}`}
        </p>
        <p className="text-[10px] text-[var(--color-text-muted)] mt-1 opacity-70">{formatRelative(item.created_at)}</p>
      </div>
    </div>
  );
}
