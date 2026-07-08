import { cn } from '@/utils';
import { Package } from 'lucide-react';

export function FooterStatusBar({ className }: { className?: string }) {
  return (
    <footer
      className={cn(
        'h-7 px-4 border-t border-[var(--color-border)] bg-[var(--color-surface)]',
        'flex items-center justify-between text-[10.5px] text-[var(--color-text-muted)]',
        className,
      )}
    >
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-[var(--color-success)] shadow-[var(--shadow-success-glow)] animate-pulse" />
          All systems operational
        </span>
        <span className="hidden sm:inline">v0.1.0-alpha</span>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden sm:flex items-center gap-1">
          <Package className="size-3" />
          Build #2412
        </span>
      </div>
    </footer>
  );
}
