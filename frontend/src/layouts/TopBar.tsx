import { useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  ChevronDown,
  LogOut,
  Settings,
} from 'lucide-react';
import { cn } from '@/utils';
import { useAuthStore } from '@/store';
import { useOutsideClick } from '@/hooks/hooks';

const pageTitles: Record<string, { title: string; subtitle?: string }> = {
  '/dashboard': { title: 'Overview' },
  '/projects': { title: 'Leads' },
  '/generation': { title: 'Websites' },
  '/preview': { title: 'Preview' },
  '/deployment': { title: 'Deployment' },
  '/history': { title: 'Activity' },
  '/analytics': { title: 'Analytics' },
  '/settings': { title: 'Settings' },
  '/help': { title: 'Help' },
};

export function TopBar({ className }: { className?: string }) {
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useOutsideClick(menuRef, menuOpen, () => setMenuOpen(false));

  const pageInfo = pageTitles[location.pathname] ?? { title: 'LeadForge' };

  return (
    <header
      className={cn(
        'h-14 w-full border-b border-[var(--color-border)] bg-[var(--color-surface)]',
        'flex items-center justify-between gap-3 px-6 z-30',
        'transition-colors duration-[var(--anim-normal)]',
        className,
      )}
    >
      {/* Left: Page title */}
      <div className="flex items-center gap-3">
        <h1 className="text-[16px] font-semibold text-[var(--color-text)] tracking-tight">
          {pageInfo.title}
        </h1>
        {pageInfo.subtitle && (
          <span className="lf-label text-[10px] hidden sm:inline">
            {pageInfo.subtitle}
          </span>
        )}
      </div>

      {/* Right: User menu */}
      <div className="flex items-center gap-3">
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2.5 px-2 py-1.5 rounded-[var(--radius-md)] hover:bg-[var(--color-surface-hover)] transition-colors duration-[var(--anim-fast)] group"
          >
            <div className="size-7 rounded-full bg-[var(--color-brand)] flex items-center justify-center text-[11px] font-semibold text-white">
              {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <span className="text-[12.5px] font-medium text-[var(--color-text)] hidden sm:block">
              {user?.full_name ?? 'User'}
            </span>
            <ChevronDown className="size-3 text-[var(--color-text-muted)]" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1.5 w-48 rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] shadow-[var(--shadow-pop)] py-1 z-50 lf-scale-up">
              <div className="px-3 py-2 border-b border-[var(--color-divider)] mb-1">
                <p className="text-[12px] font-medium text-[var(--color-text)]">{user?.full_name ?? 'User'}</p>
                <p className="text-[10px] text-[var(--color-text-muted)] font-mono">{user?.email ?? ''}</p>
              </div>
              <button
                onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors duration-[var(--anim-fast)]"
              >
                <Settings className="size-4" />
                Settings
              </button>
              <div className="h-px bg-[var(--color-divider)] mx-2 my-1" />
              <button
                onClick={() => { setMenuOpen(false); logout(); navigate('/login'); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-danger)] transition-colors duration-[var(--anim-fast)]"
              >
                <LogOut className="size-4" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
