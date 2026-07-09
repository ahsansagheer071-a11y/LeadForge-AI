import { cn } from '@/utils';

type LogoVariant = 'full' | 'compact' | 'monochrome' | 'glowing';

interface LeadForgeLogoProps {
  variant?: LogoVariant;
  className?: string;
  size?: number;
}

export function LeadForgeLogo({ variant = 'full', className, size = 32 }: LeadForgeLogoProps) {
  const isMonochrome = variant === 'monochrome';
  const isGlowing = variant === 'glowing';
  const iconSize = variant === 'full' ? size : size;
  const fill = isMonochrome ? '#94a3b8' : 'url(#lf-grad)';
  const glowFilter = isGlowing ? 'url(#lf-glow)' : undefined;
  const accentFill = isMonochrome ? '#64748b' : '#0ea5e9';

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
          <stop offset="0%" stopColor="#0ea5e9" />
          <stop offset="50%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
        <linearGradient id="lf-mono" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#94a3b8" />
          <stop offset="100%" stopColor="#64748b" />
        </linearGradient>
        {isGlowing && (
          <filter id="lf-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>

      {/* Outer ring — forged metal appearance */}
      <rect
        x="2"
        y="2"
        width="36"
        height="36"
        rx="10"
        ry="10"
        stroke={isMonochrome ? '#475569' : '#0ea5e9'}
        strokeWidth="1.5"
        fill="none"
        opacity={isMonochrome ? 0.4 : 0.3}
      />
      <rect
        x="5"
        y="5"
        width="30"
        height="30"
        rx="7"
        ry="7"
        stroke={accentFill}
        strokeWidth="0.75"
        fill="none"
        opacity={0.5}
      />

      {/* Spark / forge accent top-right */}
      <circle cx="30" cy="10" r="1.5" fill={accentFill} opacity={0.8} />
      <line x1="30" y1="10" x2="28" y2="8" stroke={accentFill} strokeWidth="0.5" opacity={0.4} />
      <line x1="30" y1="10" x2="33" y2="9" stroke={accentFill} strokeWidth="0.5" opacity={0.4} />

      {/* L — bold geometric */}
      <path
        d="M12 12V28H24"
        stroke={fill}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={glowFilter}
      />

      {/* F — connected to L */}
      <path
        d="M24 12H16M24 20H18"
        stroke={fill}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={glowFilter}
      />

      {/* AI circuit node — subtle dot at connection */}
      <circle cx="20" cy="20" r="1.5" fill={isMonochrome ? '#cbd5e1' : '#06b6d4'} opacity={0.9} />

      {/* Circuit trace from node to edge */}
      <path
        d="M20 20 L26 20 L28 18"
        stroke={accentFill}
        strokeWidth="0.75"
        strokeLinecap="round"
        opacity={0.5}
        fill="none"
      />
      <circle cx="28" cy="18" r="0.75" fill={accentFill} opacity={0.6} />

      {/* Bottom accent bar */}
      <line
        x1="10" y1="33" x2="30" y2="33"
        stroke={isMonochrome ? '#475569' : 'url(#lf-grad)'}
        strokeWidth="1"
        strokeLinecap="round"
        opacity={0.4}
      />
    </svg>
  );

  if (variant === 'compact' || variant === 'monochrome') {
    return icon;
  }

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      {icon}
      <div className="overflow-hidden">
        <p className="text-[15px] font-bold tracking-tight leading-tight bg-gradient-to-r from-[#0ea5e9] via-[#8b5cf6] to-[#06b6d4] bg-clip-text text-transparent">
          LeadForge
        </p>
        <p className="text-[9.5px] uppercase tracking-[0.25em] text-[var(--color-text-muted)] font-mono leading-tight">
          AI
        </p>
      </div>
    </div>
  );
}
