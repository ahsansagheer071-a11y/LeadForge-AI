import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sun,
  Moon,
  Monitor,
  ChevronDown,
  LogOut,
  Settings,
} from 'lucide-react';
import { cn } from '@/utils';
import { useTheme } from '@/contexts/ThemeContext';
import { useAuthStore } from '@/store';
import { useOutsideClick } from '@/hooks/hooks';

const themeIcons = { light: Sun, dark: Moon, system: Monitor } as const;

export function TopBar({ className }: { className?: string }) {
  const { mode, cycle } = useTheme();
  const ThemeIcon = themeIcons[mode];
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useOutsideClick(menuRef, menuOpen, () => setMenuOpen(false));

  return (
    <header
      className={cn(
        'h-14 w-full border-b border-[var(--color-border)] bg-[var(--color-surface)]/80 backdrop-blur-md',
        'flex items-center justify-between gap-3 px-4 lg:px-6 sticky top-0 z-30',
        className,
      )}
    >
      {/* Search */}


      {/* Right */}
      <div className="flex items-center gap-1">
        {/* Theme toggle */}
        <button
          onClick={cycle}
          className="size-8 rounded-[8px] flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
          aria-label={`Theme: ${mode}`}
          title={`Theme: ${mode}`}
        >
          <ThemeIcon className="size-4" />
        </button>

        {/* Notifications */}


        {/* Avatar / User menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 ml-2 pl-2 pr-1.5 py-1 rounded-[8px] hover:bg-[var(--color-surface-hover)] transition-colors"
          >
            <div className="size-7 rounded-full bg-[var(--color-brand)] flex items-center justify-center text-[11px] font-bold text-white">
              {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <span className="text-[12.5px] font-medium text-[var(--color-text)] hidden sm:block">
              {user?.full_name ?? 'User'}
            </span>
            <ChevronDown className="size-3 text-[var(--color-text-muted)]" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1 w-48 rounded-[12px] bg-[var(--color-glass)] backdrop-blur-[var(--blur-lg)] border border-[var(--color-glass-border)] shadow-[var(--shadow-pop)] py-1 z-50 lf-fade-in">
              <button
                onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
              >
                <Settings className="size-4" />
                Settings
              </button>
              <div className="h-px bg-[var(--color-border)] mx-2 my-1" />
              <button
                onClick={() => { setMenuOpen(false); logout(); navigate('/login'); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-danger)] transition-colors"
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
