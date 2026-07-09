import * as React from 'react';
import { cn } from '@/utils';

type Tone = 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral';

const styles: Record<Tone, string> = {
  brand: 'bg-[var(--color-brand-soft)] text-[var(--color-brand)] border border-[var(--color-brand-border)]',
  success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.15)]',
  warning: 'bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-[0_0_10px_rgba(234,179,8,0.15)]',
  danger: 'bg-red-500/10 text-red-400 border border-red-500/30 shadow-[0_0_10px_rgba(220,38,38,0.15)]',
  info: 'bg-sky-500/10 text-sky-400 border border-sky-500/30 shadow-[0_0_10px_rgba(14,165,233,0.15)]',
  muted: 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]',
  neutral: 'bg-[var(--color-surface-overlay)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
};

export function Badge({
  className,
  tone = 'muted',
  animated = false,
  children,
  ...rest
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone; animated?: boolean }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold leading-tight whitespace-nowrap tracking-wide',
        styles[tone],
        animated && 'lf-pulse-glow',
        className,
      )}
      {...rest}
    >
      {children}
    </span>
  );
}
