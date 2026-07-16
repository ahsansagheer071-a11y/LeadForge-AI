import { cn } from '@/utils';

type LogoVariant = 'full' | 'compact' | 'monochrome' | 'glowing';

interface LeadForgeLogoProps {
  variant?: LogoVariant;
  className?: string;
  size?: number;
}

export function LeadForgeLogo({ variant = 'full', className, size = 32 }: LeadForgeLogoProps) {
  const isMonochrome = variant === 'monochrome';
  const iconSize = size;
  const fill = isMonochrome ? 'var(--color-text-muted)' : 'url(#lf-grad)';
  const accentFill = isMonochrome ? 'var(--color-text-muted)' : 'var(--color-brand)';

  const icon = (
    <svg
      width={iconSize}
      height={iconSize}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('flex-shrink-0', className)}
      aria-hidden
    >
      <defs>
        <linearGradient id="lf-grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--color-brand)" />
          <stop offset="100%" stopColor="var(--color-brand-hover)" />
        </linearGradient>
      </defs>

      {/* Outer ring */}
      <rect
        x="2" y="2" width="36" height="36" rx="10" ry="10"
        stroke={accentFill}
        strokeWidth="1.5"
        fill="none"
        opacity={0.25}
      />

      {/* L */}
      <path
        d="M12 12V28H24"
        stroke={fill}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* F */}
      <path
        d="M24 12H16M24 20H18"
        stroke={fill}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* AI circuit node */}
      <circle cx="20" cy="20" r="1.5" fill={accentFill} opacity={0.8} />

      {/* Circuit trace */}
      <path
        d="M20 20 L26 20 L28 18"
        stroke={accentFill}
        strokeWidth="0.75"
        strokeLinecap="round"
        opacity={0.4}
        fill="none"
      />
      <circle cx="28" cy="18" r="0.75" fill={accentFill} opacity={0.5} />
    </svg>
  );

  if (variant === 'compact' || variant === 'monochrome') {
    return icon;
  }

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      {icon}
      <div className="overflow-hidden">
        <p className="text-[15px] font-bold tracking-tight leading-tight text-[var(--color-text)]">
          LeadForge
        </p>
        <p className="text-[9.5px] uppercase tracking-[0.25em] text-[var(--color-text-muted)] font-mono leading-tight">
          AI
        </p>
      </div>
    </div>
  );
}
