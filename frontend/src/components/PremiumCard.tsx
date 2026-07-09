import { type ReactNode } from 'react';
import { cn } from '@/utils';

type CardVariant = 'subtle' | 'standard' | 'featured' | 'danger' | 'glass';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  innerClassName?: string;
  variant?: CardVariant;
  featured?: boolean;
}

const rgbGradient = 'conic-gradient(from var(--angle), #00f5a0, #00d9ff, #2563ff, #7c3aed, #ff2bd6, #00f5a0)';
const dangerGradient = 'conic-gradient(from var(--angle), #dc2626, #f97316, #ff2bd6, #dc2626)';

const variantConfig: Record<CardVariant, {
  padding: string;
  speed: string;
  glow: string;
  glowOpacity: string;
  borderOpacity: string;
  gradient: string;
  glowClass: string;
  borderClass: string;
}> = {
  subtle: {
    padding: 'p-[1px]',
    speed: '12s',
    glow: 'blur-[10px]',
    glowOpacity: 'opacity-20',
    borderOpacity: 'opacity-60',
    gradient: rgbGradient,
    glowClass: 'premium-card-rgb-glow',
    borderClass: 'premium-card-rgb-border',
  },
  standard: {
    padding: 'p-[2px]',
    speed: '8s',
    glow: 'blur-[12px]',
    glowOpacity: 'opacity-40',
    borderOpacity: 'opacity-100',
    gradient: rgbGradient,
    glowClass: 'premium-card-rgb-glow',
    borderClass: 'premium-card-rgb-border',
  },
  featured: {
    padding: 'p-[3px]',
    speed: '5s',
    glow: 'blur-[16px]',
    glowOpacity: 'opacity-50',
    borderOpacity: 'opacity-100',
    gradient: rgbGradient,
    glowClass: 'premium-card-rgb-glow',
    borderClass: 'premium-card-rgb-border',
  },
  glass: {
    padding: 'p-[2px]',
    speed: '8s',
    glow: 'blur-[12px]',
    glowOpacity: 'opacity-30',
    borderOpacity: 'opacity-80',
    gradient: rgbGradient,
    glowClass: 'premium-card-rgb-glow',
    borderClass: 'premium-card-rgb-border',
  },
  danger: {
    padding: 'p-[2px]',
    speed: '6s',
    glow: 'blur-[12px]',
    glowOpacity: 'opacity-40',
    borderOpacity: 'opacity-100',
    gradient: dangerGradient,
    glowClass: 'premium-card-rgb-glow-danger',
    borderClass: 'premium-card-rgb-border-danger',
  },
};

export function PremiumCard({ children, className, innerClassName, variant: _v, featured }: PremiumCardProps) {
  const resolvedVariant: CardVariant = _v === 'glass' ? 'standard' : (_v as CardVariant) ?? (featured ? 'featured' : 'standard');
  const cfg = variantConfig[resolvedVariant];

  return (
    <div
      className={cn(
        'relative rounded-[var(--radius-lg)] group',
        cfg.padding,
        className,
      )}
    >
      {/* Blurred outer glow */}
      <div
        className={cn(
          cfg.glowClass,
          'absolute inset-0 z-0 rounded-[var(--radius-lg)] transition-all duration-300',
          cfg.glowOpacity,
          'group-hover:opacity-80',
          cfg.glow,
          'pointer-events-none',
        )}
        style={{
          background: cfg.gradient,
          animation: `lf-conic-spin ${cfg.speed} linear infinite`,
        }}
      />
      {/* Sharp inner RGB perimeter */}
      <div
        className={cn(
          cfg.borderClass,
          'absolute inset-0 z-0 rounded-[var(--radius-lg)] transition-all duration-300',
          cfg.borderOpacity,
          'pointer-events-none',
        )}
        style={{
          background: cfg.gradient,
          animation: `lf-conic-spin ${cfg.speed} linear infinite`,
        }}
      />
      {/* Dark inner surface */}
      <div
        className={cn(
          'relative z-10 h-full w-full rounded-[calc(var(--radius-lg)-1px)]',
          'bg-[var(--color-glass-strong)] backdrop-blur-xl',
          'transition-transform duration-200 group-hover:-translate-y-0.5',
          'shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]',
          innerClassName,
        )}
      >
        {children}
      </div>
    </div>
  );
}
