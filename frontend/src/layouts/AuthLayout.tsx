import { type ReactNode } from 'react';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

interface AuthLayoutProps {
  children: ReactNode;
  /** Right-side content card */
  card: ReactNode;
}

const features = [
  { label: 'Lead Discovery', desc: 'Find overlooked businesses in any market' },
  { label: 'AI Website Audit', desc: 'Instant design and SEO scoring' },
  { label: 'Website Generation', desc: 'Premium sites built in seconds' },
  { label: 'Automated Outreach', desc: 'Convert leads with smart campaigns' },
];

export function AuthLayout({ children, card }: AuthLayoutProps) {
  return (
    <div className="min-h-screen w-full flex bg-[var(--color-bg)]">
      {/* ── Left: Brand panel (hidden on mobile) ─────────── */}
      <div className="hidden lg:flex lg:w-[52%] xl:w-[55%] flex-col justify-between p-10 xl:p-14 relative overflow-hidden">
        {/* Subtle background gradient */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_80%_60%_at_20%_20%,var(--color-brand-soft),transparent_70%)]" />
        </div>

        <div className="relative z-10">
          <LeadForgeLogo variant="full" size={36} />
        </div>

        <div className="relative z-10 max-w-lg">
          <h1 className="text-[clamp(1.75rem,3vw,2.5rem)] font-bold tracking-tight leading-[1.15] text-[var(--color-text)] mb-4">
            Lead intelligence,
            <br />
            <span className="text-[var(--color-brand)]">without the noise.</span>
          </h1>
          <p className="text-[14px] text-[var(--color-text-secondary)] leading-relaxed mb-10 max-w-md">
            Discover businesses, audit their web presence, generate premium sites, and convert them — all from one platform.
          </p>

          <div className="space-y-4">
            {features.map((f) => (
              <div key={f.label} className="flex items-start gap-3">
                <div className="size-1.5 rounded-full bg-[var(--color-brand)] mt-[7px] shrink-0" />
                <div>
                  <p className="text-[13px] font-medium text-[var(--color-text)]">{f.label}</p>
                  <p className="text-[12px] text-[var(--color-text-muted)]">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-[11px] text-[var(--color-text-muted)]">
            &copy; {new Date().getFullYear()} LeadForge AI. All rights reserved.
          </p>
        </div>
      </div>

      {/* ── Right: Form area ───────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Mobile header */}
        <div className="lg:hidden flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
          <LeadForgeLogo variant="full" size={28} />
          <ThemeSwitcher />
        </div>

        <div className="flex-1 flex items-center justify-center px-5 py-10 lg:py-0">
          <div className="w-full max-w-[400px]">
            {children}
            {card}
          </div>
        </div>

        {/* Desktop theme switcher + footer */}
        <div className="hidden lg:flex items-center justify-between px-10 pb-6">
          <p className="text-[11px] text-[var(--color-text-muted)]">
            &copy; {new Date().getFullYear()} LeadForge AI
          </p>
          <ThemeSwitcher />
        </div>
      </div>
    </div>
  );
}
