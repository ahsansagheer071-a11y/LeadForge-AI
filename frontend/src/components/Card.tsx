import * as React from 'react';
import { cn } from '@/utils';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass' | 'premium';
}

export function Card({
  className,
  variant = 'default',
  children,
  ...rest
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-[14px] border transition-colors duration-150',
        variant === 'default' && 'bg-[var(--color-surface)] border-[var(--color-border)] shadow-[var(--shadow-card)]',
        variant === 'glass' && 'bg-[var(--color-glass)] backdrop-blur-[var(--blur-md)] border-[var(--color-glass-border)] shadow-[var(--shadow-card)]',
        variant === 'premium' && 'bg-[var(--color-surface)] border-[var(--color-brand-border)] shadow-[var(--shadow-glow)]',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-5 py-4 border-b border-[var(--color-border)] flex items-center justify-between gap-3',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3 className={cn('text-[14.5px] font-semibold tracking-tight', className)} {...rest}>
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn(
        'text-[12.5px] text-[var(--color-text-muted)] mt-0.5',
        className,
      )}
      {...rest}
    >
      {children}
    </p>
  );
}

export function CardContent({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn('p-5', className)} {...rest}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...rest
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'px-5 py-4 border-t border-[var(--color-border)] flex items-center justify-between gap-3',
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
