/**
 * Loading primitives.
 * Premium feel: subtle pulses, smooth entrances, no flashy effects.
 */

import * as React from 'react';
import { Loader2, type LucideIcon } from 'lucide-react';
import { cn } from '@/utils';

/* ── Skeleton ─────────────────────────────────────────────── */
type SkeletonProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number; // for text variant only
  delay?: number; // ms — stagger animation start
};

export function Skeleton({
  className,
  variant = 'rectangular',
  width,
  height,
  lines,
  delay = 0,
  style,
  ...rest
}: SkeletonProps) {
  const base = 'lf-pulse bg-[var(--color-surface-hover)]';
  const variantClass = {
    text: 'h-3 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-md',
    rounded: 'rounded-[12px]',
  }[variant];

  const sharedStyle: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
    animationDelay: delay ? `${delay}ms` : undefined,
    ...style,
  };

  if (variant === 'text' && lines && lines > 1) {
    return (
      <div className={cn('flex flex-col gap-1.5', className)} {...rest}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={cn(base, variantClass, i === lines - 1 && 'w-3/4')}
            style={{
              ...sharedStyle,
              width: i === lines - 1 ? '75%' : sharedStyle.width ?? '100%',
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={cn(base, variantClass, className)}
      style={sharedStyle}
      {...rest}
    />
  );
}

/* ── Card skeleton ───────────────────────────────────────── */
export function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="lf-card p-5 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={36} height={36} />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" delay={60} />
        </div>
      </div>
      <div className="space-y-2 pt-2">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} variant="text" width="100%" delay={120 * i} />
        ))}
      </div>
    </div>
  );
}

/* ── Spinner ──────────────────────────────────────────────── */
export function Spinner({
  size = 16,
  className,
  icon,
}: { size?: number; className?: string; icon?: LucideIcon }) {
  const Icon = icon ?? Loader2;
  return (
    <Icon
      size={size}
      className={cn('lf-spin text-current', className)}
      aria-label="Loading"
    />
  );
}

/* ── Page loader ──────────────────────────────────────────── */
export function PageLoader({
  label = 'Loading workspace',
}: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center w-full h-full p-12 gap-4"
    >
      <div className="relative h-12 w-12 rounded-full bg-[var(--color-brand-subtle)] flex items-center justify-center">
          <Spinner size={20} icon={Loader2} className="text-[var(--color-brand)]" />
        </div>
      <p className="text-[12.5px] text-[var(--color-text-muted)]">{label}…</p>
    </div>
  );
}

/* ── Button loader ──────────────────────────────────────────
   A button-shaped skeleton used inside buttons / form rows
   while the action is busy. NOT the same as <Button loading>.
*/
export function ButtonLoader({ className }: { className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      <Spinner size={14} />
      <span className="text-[12.5px] text-[var(--color-text-muted)]">Working…</span>
    </span>
  );
}

/* ── Progress bar ─────────────────────────────────────────── */
export function ProgressBar({
  value,
  max = 100,
  size = 'md',
  tone = 'brand',
  showLabel = false,
  className,
}: {
  value: number;
  max?: number;
  size?: 'sm' | 'md';
  showLabel?: boolean;
  tone?: 'brand' | 'success' | 'warning' | 'danger';
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const fillClass = {
    brand: 'bg-[var(--color-brand)]',
    success: 'bg-[var(--color-success)]',
    warning: 'bg-[var(--color-warning)]',
    danger: 'bg-[var(--color-danger)]',
  }[tone];

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'w-full rounded-full bg-[var(--color-surface-hover)] overflow-hidden',
          size === 'sm' ? 'h-1' : 'h-2',
        )}
        aria-label={showLabel ? `${pct.toFixed(0)} percent` : undefined}
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={cn('h-full rounded-full transition-[width] duration-200 ease-out', fillClass)}
          style={{ width: `${pct}%` }}
        />
      </div>
      {showLabel && (
        <p className="text-[11px] text-[var(--color-text-muted)] mt-1">
          {pct.toFixed(0)}%
        </p>
      )}
    </div>
  );
}
