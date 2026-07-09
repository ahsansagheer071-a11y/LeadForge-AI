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
        'h-[calc(100vh-3.5rem)] w-[320px] border-l border-slate-800 bg-[#040810]/95 backdrop-blur-xl z-20 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]',
        'flex flex-col overflow-hidden transition-all duration-300 ease-out',
        open ? 'opacity-100' : 'opacity-0 pointer-events-none w-0',
        'lf-thin-scroll',
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-5 pt-5 pb-3 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="relative">
             <Activity className="size-4 text-[#0ea5e9]" />
             <div className="absolute inset-0 bg-[#0ea5e9] blur-md opacity-50" />
          </div>
          <span className="text-[14px] font-mono uppercase tracking-widest text-white">Live Activity</span>
        </div>
        <button
          onClick={onClose}
          className="size-7 rounded-[8px] flex items-center justify-center text-slate-400 hover:bg-slate-800 hover:text-white transition-colors border border-transparent hover:border-slate-700"
        >
          <X className="size-3.5" />
        </button>
      </div>

      {/* Feed */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-2 relative">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="size-12 rounded-full border border-slate-800 bg-slate-900 flex items-center justify-center mb-3">
              <Activity className="size-5 text-slate-600" />
            </div>
            <p className="text-[12px] font-mono text-slate-500 uppercase tracking-widest">No Signal Detected</p>
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
  const colorClass = isSuccess ? 'text-[#10b981]' : isError ? 'text-red-500' : 'text-[#0ea5e9]';
  const bgClass = isSuccess ? 'bg-[#10b981]/10' : isError ? 'bg-red-500/10' : 'bg-[#0ea5e9]/10';

  return (
    <div
      className="group flex items-start gap-3 px-3 py-3 rounded-[12px] transition-all bg-slate-900/40 border border-slate-800/50 hover:bg-slate-800/80 hover:border-slate-700 relative overflow-hidden"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className={cn("mt-0.5 size-7 rounded-[6px] flex items-center justify-center border border-slate-700/50 shrink-0", bgClass)}>
        <Icon className={cn('size-3.5', colorClass)} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-bold text-white truncate group-hover:text-[#0ea5e9] transition-colors">{item.name}</p>
        <p className="text-[11px] font-mono text-slate-400 mt-1 line-clamp-1 uppercase tracking-wider">
          {item.status === 'NEW' ? 'Lead discovered' : `${item.status.replace('_', ' ')}`}
        </p>
        <p className="text-[10px] text-slate-500 mt-1.5">{formatRelative(item.created_at)}</p>
      </div>
    </div>
  );
}
