/**
 * Premium Button — variants: brand, ghost, outline, soft, danger.
 * Sizes: xs, sm, md, lg. Supports loading spinner + icon slot.
 */

import * as React from 'react';
import { cn } from '@/utils';
import { Loader2 } from 'lucide-react';

export type ButtonVariant =
  | 'brand'
  | 'brand-soft'
  | 'outline'
  | 'ghost'
  | 'soft'
  | 'danger'
  | 'subtle';

export type ButtonSize = 'xs' | 'sm' | 'md' | 'lg';

type AsButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: false;
};

type AsChildProps = {
  asChild: true;
  children: React.ReactNode;
} & Omit<React.HTMLAttributes<HTMLElement>, 'children'>;

export type ButtonProps = {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
  className?: string;
  children?: React.ReactNode;
} & (AsButtonProps | AsChildProps);

const variantClass: Record<ButtonVariant, string> = {
  brand:
    'bg-[var(--color-brand)] text-white shadow-[0_4px_12px_color-mix(in_oklab,var(--color-brand)_30%,transparent)] ' +
    'hover:bg-[var(--color-brand-hover)] active:bg-[var(--color-brand-active)] ' +
    'disabled:opacity-50 disabled:cursor-not-allowed',
  'brand-soft':
    'bg-[var(--color-brand-soft)] text-[var(--color-brand)] border border-[var(--color-brand-border)] ' +
    'hover:bg-[var(--color-brand-subtle)]',
  outline:
    'bg-[var(--color-surface)] text-[var(--color-text)] border border-[var(--color-border)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border-strong)]',
  ghost:
    'bg-transparent text-[var(--color-text-secondary)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
  soft:
    'bg-[var(--color-surface-hover)] text-[var(--color-text)] ' +
    'hover:bg-[var(--color-surface-overlay)]',
  danger:
    'bg-[var(--color-danger)] text-white shadow-[0_4px_12px_color-mix(in_oklab,var(--color-danger)_25%,transparent)] ' +
    'hover:opacity-90 disabled:opacity-50',
  subtle:
    'bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]',
};

const sizeClass: Record<ButtonSize, string> = {
  xs: 'h-7 px-2 text-[11px] gap-1',
  sm: 'h-8 px-3 text-[12.5px] gap-1.5',
  md: 'h-9 px-3.5 text-[13px] gap-2',
  lg: 'h-11 px-5 text-[14.5px] gap-2',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  props,
  ref,
) {
  const {
    variant = 'brand',
    size = 'md',
    loading,
    leftIcon,
    rightIcon,
    fullWidth,
    className,
    children,
    asChild,
    ...rest
  } = props as ButtonProps & { asChild?: boolean };

  const classes = cn(
    'inline-flex items-center justify-center rounded-[10px] font-medium',
    'transition-[background,border-color,color,box-shadow,opacity] duration-150',
    'focus-visible:outline-2 focus-visible:outline-[var(--color-brand)] focus-visible:outline-offset-2',
    'disabled:pointer-events-none',
    variantClass[variant],
    sizeClass[size],
    fullWidth && 'w-full',
    className,
  );

  const content = (
    <>
      {loading ? (
        <Loader2 className="lf-spin size-3.5" aria-hidden />
      ) : leftIcon ? (
        <span className="-ml-0.5 inline-flex items-center" aria-hidden>
          {leftIcon}
        </span>
      ) : null}
      {children}
      {rightIcon && !loading ? (
        <span className="-mr-0.5 inline-flex items-center" aria-hidden>
          {rightIcon}
        </span>
      ) : null}
    </>
  );

  if (asChild) {
    const child = React.Children.only(children) as React.ReactElement<{ className?: string }>;
    return React.cloneElement(child, {
      ...(rest as Record<string, unknown>),
      className: cn(classes, child.props.className),
      children: content,
    } as Record<string, unknown>);
  }

  return (
    <button
      ref={ref}
      className={classes}
      disabled={(rest as { disabled?: boolean }).disabled || loading}
      {...rest}
    >
      {content}
    </button>
  );
});
