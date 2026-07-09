import * as React from 'react';
import { cn } from '@/utils';
import { Loader2 } from 'lucide-react';

export type ButtonVariant =
  | 'brand'
  | 'brand-soft'
  | 'neon'
  | 'glass'
  | 'glow'
  | 'outline'
  | 'ghost'
  | 'success'
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
    'bg-gradient-to-r from-[var(--color-brand)] to-[var(--color-brand-600)] text-white ' +
    'shadow-[0_4px_16px_color-mix(in_oklab,var(--color-brand)_30%,transparent)] ' +
    'hover:shadow-[0_6px_24px_color-mix(in_oklab,var(--color-brand)_45%,transparent)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 active:brightness-90 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  'brand-soft':
    'bg-[var(--color-brand-soft)] text-[var(--color-brand)] border border-[var(--color-brand-border)] ' +
    'hover:bg-[var(--color-brand-subtle)] hover:-translate-y-0.5 active:translate-y-0',
  neon:
    'bg-gradient-to-r from-[#0ea5e9] to-[#06b6d4] text-white ' +
    'shadow-[0_0_20px_rgba(14,165,233,0.4)] ' +
    'hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 active:brightness-90 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  glass:
    'bg-[var(--color-glass)] backdrop-blur-[var(--blur-md)] text-[var(--color-text)] ' +
    'border border-[var(--color-glass-border)] ' +
    'hover:bg-[var(--color-glass-strong)] hover:border-[var(--color-border-strong)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  glow:
    'bg-gradient-to-r from-[var(--color-brand)] to-[var(--color-brand-600)] text-white ' +
    'shadow-[var(--shadow-glow)] ' +
    'hover:shadow-[0_0_30px_color-mix(in_oklab,var(--color-brand)_50%,transparent)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 active:brightness-90 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  outline:
    'bg-transparent text-[var(--color-text)] border border-[var(--color-border-strong)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-brand-border)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  ghost:
    'bg-transparent text-[var(--color-text-secondary)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
  success:
    'bg-gradient-to-r from-[var(--color-success)] to-[#059669] text-white ' +
    'shadow-[0_4px_16px_rgba(16,185,129,0.3)] ' +
    'hover:shadow-[0_6px_24px_rgba(16,185,129,0.45)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 active:brightness-90 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  danger:
    'bg-gradient-to-r from-[var(--color-danger)] to-[#dc2626] text-white ' +
    'shadow-[0_4px_16px_rgba(220,38,38,0.3)] ' +
    'hover:shadow-[0_6px_24px_rgba(220,38,38,0.45)] hover:-translate-y-0.5 ' +
    'active:translate-y-0 active:brightness-90 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0',
  subtle:
    'bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]',
};

const sizeClass: Record<ButtonSize, string> = {
  xs: 'h-7 px-2 text-[11px] gap-1 rounded-[8px]',
  sm: 'h-8 px-3 text-[12.5px] gap-1.5 rounded-[9px]',
  md: 'h-9 px-3.5 text-[13px] gap-2 rounded-[10px]',
  lg: 'h-11 px-5 text-[14.5px] gap-2 rounded-[12px]',
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
    'inline-flex items-center justify-center font-medium',
    'transition-all duration-[var(--anim-fast)]',
    'focus-visible:outline-2 focus-visible:outline-[var(--color-brand)] focus-visible:outline-offset-2',
    'disabled:pointer-events-none',
    'select-none',
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
        <span className="-ml-0.5 inline-flex items-center group-hover:translate-x-0.5 transition-transform" aria-hidden>
          {leftIcon}
        </span>
      ) : null}
      {children}
      {rightIcon && !loading ? (
        <span className="-mr-0.5 inline-flex items-center group-hover:-translate-x-0.5 transition-transform" aria-hidden>
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
      className={cn(classes, 'group')}
      disabled={(rest as { disabled?: boolean }).disabled || loading}
      {...rest}
    >
      {content}
    </button>
  );
});
