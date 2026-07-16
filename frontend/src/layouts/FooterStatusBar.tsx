import { cn } from '@/utils';

export function FooterStatusBar({ className }: { className?: string }) {
  return (
    <footer
      className={cn(
        'h-7 px-6 border-t border-[var(--color-border)] bg-[var(--color-surface)]',
        'flex items-center justify-between text-[10.5px] text-[var(--color-text-muted)]',
        'transition-colors duration-[var(--anim-normal)]',
        className,
      )}
    >
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-2">
          <span className="size-1.5 rounded-full bg-[var(--color-success)]" />
          All systems operational
        </span>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden sm:inline">LeadForge AI</span>
      </div>
    </footer>
  );
}
