import { X, Activity, CheckCircle2, AlertCircle, Info, ArrowUpRight } from 'lucide-react';
import { cn, formatRelative } from '@/utils';
import { useNotificationsStore } from '@/store';
import { Badge } from '@/components/Badge';
import { Separator } from '@/components/Separator';
import type { AppNotification, NotificationKind } from '@/types';

const kindIcon: Record<NotificationKind, typeof Activity> = {
  success: CheckCircle2,
  warning: AlertCircle,
  error: AlertCircle,
  info: Info,
};

const kindBadge: Record<NotificationKind, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted'> = {
  success: 'success',
  warning: 'warning',
  error: 'danger',
  info: 'info',
};

export function RightActivityPanel({
  open,
  onClose,
  className,
}: {
  open: boolean;
  onClose: () => void;
  className?: string;
}) {
  const items = useNotificationsStore((s) => s.items);

  return (
    <aside
      className={cn(
        'h-[calc(100vh-3.5rem)] w-[320px] border-l border-[var(--color-border)] bg-[var(--color-surface)]',
        'flex flex-col overflow-hidden transition-all duration-200 ease-out',
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

function ActivityItem({ item }: { item: AppNotification }) {
  const Icon = kindIcon[item.kind];
  return (
    <div
      className={cn(
        'group flex items-start gap-3 px-3 py-2.5 rounded-[10px] transition-colors',
        'hover:bg-[var(--color-surface-hover)]',
        !item.read && 'bg-[var(--color-brand-soft)]',
      )}
    >
      <div className="mt-0.5">
        <Icon className={cn('size-4', item.kind === 'success' && 'text-[var(--color-success)]', item.kind === 'warning' && 'text-[var(--color-warning)]', item.kind === 'error' && 'text-[var(--color-danger)]', item.kind === 'info' && 'text-[var(--color-info)]')} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-[12.5px] font-medium truncate">{item.title}</p>
          <Badge tone={kindBadge[item.kind]} className="text-[9px] px-1 py-0">{item.kind}</Badge>
        </div>
        {item.message && (
          <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5 line-clamp-2">{item.message}</p>
        )}
        <p className="text-[10.5px] text-[var(--color-text-muted)] mt-0.5">{formatRelative(item.created_at)}</p>
      </div>
    </div>
  );
}
