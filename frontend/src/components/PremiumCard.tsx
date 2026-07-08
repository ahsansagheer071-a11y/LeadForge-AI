import { type ReactNode } from 'react';
import { cn } from '@/utils';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
}

export function PremiumCard({ children, className, innerClassName }: PremiumCardProps) {
  return (
    <div
      className={cn(
        'relative rounded-[14px] bg-[var(--color-surface)] border border-[var(--color-border)]',
        'shadow-[var(--shadow-card)] transition-shadow duration-200 hover:shadow-lg',
        'hover:border-[var(--color-brand-border)] group',
        className,
      )}
    >
      <div
        className={cn(
          'rounded-[13px] transition-transform duration-200 group-hover:-translate-y-0.5 h-full',
          innerClassName,
        )}
      >
        {children}
      </div>
    </div>
  );
}
