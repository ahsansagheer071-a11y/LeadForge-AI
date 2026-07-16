import * as React from 'react';
import { cn } from '@/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  /** backward-compat: accepted but unused (react-hook-form may spread this) */
  invalid?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, className, id, ...props },
  ref,
) {
  const inputId = id || (label ? `input-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label
          htmlFor={inputId}
          className="lf-label text-[11px]"
        >
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        className={cn(
          'h-9 px-3 text-[13px] rounded-[var(--radius-md)]',
          'bg-[var(--color-input-bg)] border border-[var(--color-input-border)]',
          'text-[var(--color-text)] placeholder:text-[var(--color-input-placeholder)]',
          'focus:outline-none focus:border-[var(--color-brand)] focus:ring-1 focus:ring-[var(--color-brand-subtle)]',
          'transition-colors duration-[var(--anim-fast)]',
          error && 'border-[var(--color-danger)] focus:border-[var(--color-danger)] focus:ring-[var(--color-danger)]',
          className,
        )}
        {...props}
      />
      {error && <p className="text-[11px] text-[var(--color-danger)]">{error}</p>}
      {hint && !error && <p className="text-[11px] text-[var(--color-text-muted)]">{hint}</p>}
    </div>
  );
});

/* Backward-compatible named exports */
export function Label({
  children,
  className,
  ...rest
}: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label className={cn('lf-label text-[11px]', className)} {...rest}>
      {children}
    </label>
  );
}

export function FormError({
  children,
  message,
  className,
}: {
  children?: React.ReactNode;
  message?: string;
  className?: string;
}) {
  const text = message ?? children;
  if (!text) return null;
  return (
    <p className={cn('text-[11px] text-[var(--color-danger)]', className)}>
      {text}
    </p>
  );
}
