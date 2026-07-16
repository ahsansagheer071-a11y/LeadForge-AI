import * as React from 'react';
import { cn } from '@/utils';

type Tone = 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral';

const styles: Record<Tone, string> = {
  brand: 'bg-[var(--color-brand-soft)] text-[var(--color-brand)] border border-[var(--color-brand-border)]',
  success: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20',
  warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20',
  danger: 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20',
  info: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20',
  muted: 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]',
  neutral: 'bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
};

export function Badge({
  className,
  tone = 'muted',
  animated: _animated,
  children,
  ...rest
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone; animated?: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium leading-tight whitespace-nowrap',
        styles[tone],
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
