import * as React from 'react';
import { cn } from '@/utils';

export type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  invalid?: boolean;
  valid?: boolean;
};

export const Input = React.forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, invalid, valid, type = 'text', ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        'flex w-full h-9 rounded-[var(--radius-md)] px-3 text-[13px]',
        'bg-[var(--color-input-bg)] text-[var(--color-text)]',
        'border outline-none transition-colors duration-[var(--anim-fast)]',
        'placeholder:text-[var(--color-input-placeholder)]',
        invalid
          ? 'border-[var(--color-danger)] focus:border-[var(--color-danger)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-danger)_25%,transparent)]'
          : valid
            ? 'border-[var(--color-success)] focus:border-[var(--color-success)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-success)_25%,transparent)]'
            : 'border-[var(--color-input-border)] hover:border-[var(--color-border-strong)] focus:border-[var(--color-brand)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-brand)_25%,transparent)]',
        'backdrop-blur-[var(--blur-sm)]',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        className,
      )}
      {...rest}
    />
  );
});

export const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean; valid?: boolean }
>(function Textarea({ className, invalid, valid, rows = 4, ...rest }, ref) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      className={cn(
        'flex w-full rounded-[var(--radius-md)] px-3 py-2 text-[13px] resize-none',
        'bg-[var(--color-input-bg)] text-[var(--color-text)]',
        'border outline-none transition-colors duration-[var(--anim-fast)]',
        'placeholder:text-[var(--color-input-placeholder)]',
        invalid
          ? 'border-[var(--color-danger)] focus:border-[var(--color-danger)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-danger)_25%,transparent)]'
          : valid
            ? 'border-[var(--color-success)] focus:border-[var(--color-success)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-success)_25%,transparent)]'
            : 'border-[var(--color-input-border)] hover:border-[var(--color-border-strong)] focus:border-[var(--color-brand)] focus:ring-2 focus:ring-[color-mix(in_oklab,var(--color-brand)_25%,transparent)]',
        'backdrop-blur-[var(--blur-sm)]',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        className,
      )}
      {...rest}
    />
  );
});

export function Label({ className, children, ...rest }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn(
        'text-[12.5px] font-medium text-[var(--color-text-secondary)] mb-1.5 inline-block tracking-wide',
        className,
      )}
      {...rest}
    >
      {children}
    </label>
  );
}

export function FieldDescription({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('text-[11.5px] text-[var(--color-text-muted)] mt-1', className)} {...rest}>
      {children}
    </p>
  );
}

export function FormError({ children }: { children?: React.ReactNode }) {
  if (!children) return null;
  return (
    <p className="text-[11.5px] text-[var(--color-danger)] mt-1" role="alert">
      {children}
    </p>
  );
}
