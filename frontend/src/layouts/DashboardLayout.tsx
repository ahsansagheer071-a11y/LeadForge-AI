import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { Menu, X } from 'lucide-react';
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
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const closeSidebar = useCallback(() => setSidebarOpen(false), []);
  const toggleSidebar = useCallback(() => setSidebarOpen(p => !p), []);

  useEffect(() => {
    if (!sidebarOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') closeSidebar(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [sidebarOpen, closeSidebar]);

  useEffect(() => {
    document.body.style.overflow = sidebarOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [sidebarOpen]);

  const sidebarWithNav = React.isValidElement(sidebar)
    ? React.cloneElement(sidebar as React.ReactElement<{ onNavigate?: () => void }>, { onNavigate: closeSidebar })
    : sidebar;

  return (
    <div className={cn('flex h-screen w-full overflow-hidden bg-[var(--color-bg)]', className)}>
      {/* Sidebar — desktop: inline; mobile: off-canvas drawer */}
      <div className="hidden lg:flex flex-shrink-0 z-40 p-4 pb-0 h-full flex-col">
        {sidebarWithNav}
      </div>

      {/* Mobile drawer */}
      <div
        className={cn(
          'fixed inset-0 z-50 lg:hidden transition-opacity duration-[var(--anim-normal)]',
          sidebarOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0',
        )}
      >
        <div className="absolute inset-0 bg-black/50" onClick={closeSidebar} />
        <div
          className={cn(
            'absolute left-0 top-0 bottom-0 w-[280px] transition-transform duration-[var(--anim-normal)] ease-out',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          {sidebarWithNav}
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* TopBar */}
        <div className="flex-shrink-0 z-30 flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            className="lg:hidden size-9 ml-4 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors duration-[var(--anim-fast)] shrink-0"
            aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
          <div className="flex-1 min-w-0">{topBar}</div>
        </div>

        {/* Main Content Workspace */}
        <div className="flex-1 min-h-0 flex relative">
          <div className="flex-1 min-w-0 overflow-hidden bg-[var(--color-bg)]">
            {children}
          </div>

          {/* Activity Panel Overlay */}
          {activityOpen && activityPanel && (
            <div className="hidden lg:block w-[320px] border-l border-[var(--color-border)] bg-[var(--color-surface)] flex-shrink-0 z-20 lf-slide-in-right h-full overflow-hidden">
              {activityPanel}
            </div>
          )}
        </div>

        {/* Footer */}
        {footer}
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
      'lf-thin-scroll h-full w-full overflow-y-auto overflow-x-hidden',
      'px-6 py-6 md:px-10 md:py-8 lg:px-12 lg:py-10',
      'lf-fade-in',
      className,
    )}>
      <div className="max-w-[1400px] mx-auto h-full">{children}</div>
    </main>
  );
}
