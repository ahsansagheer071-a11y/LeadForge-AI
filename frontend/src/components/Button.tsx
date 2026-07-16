import * as React from 'react';
import { cn } from '@/utils';
import { Loader2 } from 'lucide-react';

export type ButtonVariant =
  | 'primary'
  | 'secondary'
  | 'ghost'
  | 'outline'
  | 'danger'
  | 'subtle'
  | 'brand'
  | 'neon'
  | 'glass'
  | 'glow'
  | 'success';

type VariantAlias = Exclude<ButtonVariant, 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'subtle'>;

const variantAlias: Record<VariantAlias, 'primary' | 'secondary' | 'ghost' | 'outline'> = {
  brand: 'primary',
  neon: 'primary',
  glass: 'secondary',
  glow: 'primary',
  success: 'outline',
};

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

const variantClass: Record<string, string> = {
  primary:
    'bg-[var(--color-brand)] text-white ' +
    'hover:bg-[var(--color-brand-hover)] active:bg-[var(--color-brand-active)] ' +
    'disabled:opacity-40 disabled:cursor-not-allowed',
  secondary:
    'bg-[var(--color-surface-hover)] text-[var(--color-text)] border border-[var(--color-border)] ' +
    'hover:bg-[var(--color-border)] ' +
    'disabled:opacity-40 disabled:cursor-not-allowed',
  ghost:
    'bg-transparent text-[var(--color-text-secondary)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
  outline:
    'bg-transparent text-[var(--color-text)] border border-[var(--color-border)] ' +
    'hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border-strong)] ' +
    'disabled:opacity-40 disabled:cursor-not-allowed',
  danger:
    'bg-[var(--color-danger)] text-white ' +
    'hover:opacity-90 active:opacity-80 ' +
    'disabled:opacity-40 disabled:cursor-not-allowed',
  subtle:
    'bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)]',
};

const sizeClass: Record<ButtonSize, string> = {
  xs: 'h-7 px-2 text-[11px] gap-1 rounded-[var(--radius-sm)]',
  sm: 'h-8 px-3 text-[12px] gap-1.5 rounded-[var(--radius-md)]',
  md: 'h-9 px-3.5 text-[13px] gap-2 rounded-[var(--radius-md)]',
  lg: 'h-11 px-5 text-[14px] gap-2 rounded-[var(--radius-lg)]',
};

function resolveVariant(v: ButtonVariant): string {
  if (v in variantAlias) return variantAlias[v as VariantAlias];
  return v;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  props,
  ref,
) {
  const {
    variant = 'primary',
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

  const resolved = resolveVariant(variant);

  const classes = cn(
    'inline-flex items-center justify-center font-medium',
    'transition-all duration-[var(--anim-fast)]',
    'focus-visible:outline-2 focus-visible:outline-[var(--color-brand)] focus-visible:outline-offset-2',
    'disabled:pointer-events-none',
    'select-none',
    variantClass[resolved],
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
      className={cn(classes, 'group')}
      disabled={(rest as { disabled?: boolean }).disabled || loading}
      {...rest}
    >
      {content}
    </button>
  );
});
