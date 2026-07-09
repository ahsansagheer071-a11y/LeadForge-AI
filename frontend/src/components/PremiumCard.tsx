import { type ReactNode } from 'react';
import { cn } from '@/utils';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  featured?: boolean;
  variant?: string;
}

export function PremiumCard({ children, className, innerClassName, featured, variant: _variant }: PremiumCardProps) {
  return (
    <div
      className={cn(
        'relative rounded-[16px] group',
        featured ? 'p-[3px]' : 'p-[2px]',
        className
      )}
    >
      {/* Blurred outer glow */}
      <div 
        className={cn(
          'premium-card-rgb-glow absolute inset-0 z-0 opacity-50 group-hover:opacity-80 blur-[12px] transition-opacity duration-300 rounded-[16px]',
          'bg-[conic-gradient(from_var(--angle),#0ea5e9,#10b981,#0ea5e9,#8b5cf6,#d946ef,#0ea5e9)]'
        )}
        style={{ animation: `lf-conic-spin ${featured ? '5s' : '8s'} linear infinite` }}
      />
      {/* Sharp inner RGB border */}
      <div 
        className={cn(
          'premium-card-rgb-border absolute inset-0 z-0 opacity-100 rounded-[16px]',
          'bg-[conic-gradient(from_var(--angle),#0ea5e9,#10b981,#0ea5e9,#8b5cf6,#d946ef,#0ea5e9)]'
        )}
        style={{ animation: `lf-conic-spin ${featured ? '5s' : '8s'} linear infinite` }}
      />
      {/* Dark inner surface */}
      <div
        className={cn(
          'relative z-10 h-full w-full rounded-[14px] bg-[var(--color-surface)] bg-opacity-95 backdrop-blur-xl',
          innerClassName
        )}
      >
        {children}
      </div>
    </div>
  );
}
