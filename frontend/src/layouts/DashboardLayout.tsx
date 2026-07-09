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
    <div className={cn('flex h-screen w-full overflow-hidden text-[var(--color-text)]', className)}>
      {/* Floating Sidebar */}
      <div className="flex-shrink-0 z-40 p-4 pb-0 h-full flex flex-col">
        {sidebar}
      </div>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Floating TopBar */}
        <div className="flex-shrink-0 z-30 pt-4 px-4 pb-0">
          {topBar}
        </div>

        {/* Main Content Workspace */}
        <div className="flex-1 min-h-0 flex relative pt-2 px-4 pb-0">
          <div className={cn(
            'flex-1 min-w-0 overflow-hidden rounded-t-[var(--radius-xl)]',
            'bg-[var(--color-glass-strong)] backdrop-blur-md',
            'border border-[var(--color-glass-border)] border-b-0 shadow-2xl',
            'relative',
          )}>
            {children}
          </div>

          {/* Activity Panel Overlay */}
          {activityOpen && activityPanel && (
            <div className="w-[320px] ml-4 flex-shrink-0 z-20 lf-slide-in-right h-full rounded-t-[var(--radius-xl)] bg-[var(--color-glass-strong)] backdrop-blur-xl border border-[var(--color-glass-border)] border-b-0 shadow-2xl overflow-hidden">
              {activityPanel}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="z-30">
          {footer}
        </div>
      </div>
    </div>
  );
}

export function Workspace({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <main className={cn(
      'lf-thin-scroll h-full w-full overflow-y-auto',
      'px-6 py-8 md:px-10 md:py-10 lg:px-14 lg:py-12',
      'lf-fade-in',
      className,
    )}>
      <div className="max-w-[1500px] mx-auto h-full">{children}</div>
    </main>
  );
}
