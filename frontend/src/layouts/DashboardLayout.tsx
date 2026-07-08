/**
 * DashboardLayout — top nav + left sidebar + main workspace
 * + collapsible right activity panel + footer status bar.
 *
 * Uses CSS Grid for the outer composition.
 */

import * as React from 'react';
import { cn } from '@/utils';

interface DashboardLayoutProps {
  topBar: React.ReactNode;
  sidebar: React.ReactNode;
  activityPanel?: React.ReactNode;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  activityOpen?: boolean;
}

export function DashboardLayout({
  topBar,
  sidebar,
  activityPanel,
  footer,
  children,
  className,
  activityOpen = false,
}: DashboardLayoutProps) {
  return (
    <div
      className={cn(
        'min-h-screen w-full grid bg-[var(--color-bg)] text-[var(--color-text)]',
        // rows: topbar | body | footer
        // body: 3 columns — sidebar | workspace | activity (auto-hidden when not open)
        'grid-rows-[auto_1fr_auto]',
        'grid-cols-[auto_1fr_auto]',
        transitionClass,
        className,
      )}
      style={{
        gridTemplateAreas: activityOpen
          ? `"top top top" "side main activity" "foot foot foot"`
          : `"top top top" "side main main" "foot foot foot"`,
      }}
    >
      <div style={{ gridArea: 'top' }} className="z-30">
        {topBar}
      </div>
      <div style={{ gridArea: 'side' }} className="z-20">
        {sidebar}
      </div>
      <div style={{ gridArea: 'main' }} className="min-w-0">
        {children}
      </div>
      {activityOpen && activityPanel ? (
        <div style={{ gridArea: 'activity' }} className="z-10 lf-fade-in">
          {activityPanel}
        </div>
      ) : null}
      <div style={{ gridArea: 'foot' }}>{footer}</div>
    </div>
  );
}

/* Standard transition class for grid changes. */
const transitionClass =
  '[transition:grid-template-columns_220ms_ease,grid-template-rows_220ms_ease]';

/* ─── Workspace container ────────────────────────────────── */

export function Workspace({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <main
      className={cn(
        'lf-thin-scroll h-[calc(100vh-3.5rem)] overflow-y-auto',
        // generous padding for a SaaS feel
        'px-4 py-6 md:px-8 md:py-8 lg:px-12 lg:py-10',
        'bg-[var(--color-bg)]',
        className,
      )}
    >
      <div className="max-w-[1440px] mx-auto">{children}</div>
    </main>
  );
}
