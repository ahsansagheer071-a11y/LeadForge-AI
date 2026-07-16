import { type ReactNode } from 'react';
import { cn } from '@/utils';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  variant?: 'subtle' | 'standard' | 'featured' | 'danger' | 'glass';
  featured?: boolean;
}

export function PremiumCard({ children, className, innerClassName }: PremiumCardProps) {
  return (
    <div
      className={cn(
        'relative rounded-[var(--radius-lg)]',
        'bg-[var(--color-surface)] border border-[var(--color-border)]',
        'transition-colors duration-[var(--anim-fast)]',
        'hover:border-[var(--color-border-strong)]',
        className,
      )}
    >
      <div className={cn('relative z-10 h-full w-full', innerClassName)}>
        {children}
      </div>
    </div>
  );
}
