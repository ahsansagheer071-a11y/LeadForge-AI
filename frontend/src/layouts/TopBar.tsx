import { useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
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

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Command Center', subtitle: 'Mission Status & Priority Intel' },
  '/projects': { title: 'Projects', subtitle: 'Discover. Audit. Build. Convert.' },
  '/generation': { title: 'Generation', subtitle: 'Synthesize AI-Powered Assets' },
  '/preview': { title: 'Preview Simulator', subtitle: 'Validate Generated Digital Assets' },
  '/deployment': { title: 'Deployment Center', subtitle: 'Extract & Distribute Artifacts' },
  '/history': { title: 'History', subtitle: 'Past Operations & Audit Trail' },
  '/analytics': { title: 'Analytics', subtitle: 'Performance Metrics & Trends' },
  '/settings': { title: 'Settings', subtitle: 'Configure Your Workspace' },
  '/help': { title: 'Help & Support', subtitle: 'Documentation & Resources' },
};

export function TopBar({ className }: { className?: string }) {
  const { mode, cycle } = useTheme();
  const ThemeIcon = themeIcons[mode];
  const navigate = useNavigate();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useOutsideClick(menuRef, menuOpen, () => setMenuOpen(false));

  const pageInfo = pageTitles[location.pathname] ?? { title: 'LeadForge AI', subtitle: 'Premium Lead Intelligence' };

  return (
    <header
      className={cn(
        'h-16 w-full rounded-[var(--radius-xl)] border border-[var(--color-glass-border)] bg-[var(--color-glass)] backdrop-blur-xl shadow-2xl',
        'flex items-center justify-between gap-3 px-5 z-30',
        className,
      )}
    >
      {/* Left: Page title area */}
      <div className="flex flex-col">
        <h1 className="text-[16px] font-bold tracking-tight">
          <span className="bg-gradient-to-r from-[#0ea5e9] via-[#06b6d4] to-[#8b5cf6] bg-clip-text text-transparent">
            {pageInfo.title}
          </span>
        </h1>
        <span className="text-[9.5px] text-[var(--color-text-muted)] uppercase tracking-[0.2em] font-mono">
          {pageInfo.subtitle}
        </span>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={cycle}
          className="size-8 rounded-[var(--radius-sm)] flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
          aria-label={`Theme: ${mode}`}
          title={`Theme: ${mode}`}
        >
          <ThemeIcon className="size-4" />
        </button>

        {/* Avatar / User menu */}
        <div className="relative" ref={menuRef}>
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2.5 ml-2 pl-2 pr-1.5 py-1 rounded-[var(--radius-md)] hover:bg-[var(--color-surface-hover)] transition-all group"
          >
            <div className="size-8 rounded-full bg-gradient-to-br from-[#0ea5e9] to-[#8b5cf6] flex items-center justify-center text-[11px] font-bold text-white shadow-[0_0_0_2px_rgba(14,165,233,0.3)] group-hover:shadow-[0_0_0_2px_rgba(14,165,233,0.6),0_0_20px_rgba(139,92,246,0.4)] transition-shadow">
              {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
            </div>
            <span className="text-[12.5px] font-medium text-[var(--color-text)] hidden sm:block">
              {user?.full_name ?? 'User'}
            </span>
            <ChevronDown className="size-3 text-[var(--color-text-muted)]" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-1.5 w-48 rounded-[var(--radius-lg)] bg-[var(--color-glass-strong)] backdrop-blur-[var(--blur-lg)] border border-[var(--color-glass-border)] shadow-[var(--shadow-pop)] py-1 z-50 lf-scale-up">
              <div className="px-3 py-2 border-b border-[var(--color-divider)] mb-1">
                <p className="text-[12px] font-medium text-[var(--color-text)]">{user?.full_name ?? 'User'}</p>
                <p className="text-[10px] text-[var(--color-text-muted)] font-mono">{user?.email ?? ''}</p>
              </div>
              <button
                onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                className="w-full flex items-center gap-2.5 px-3 py-2 text-[13px] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors"
              >
                <Settings className="size-4" />
                Settings
              </button>
              <div className="h-px bg-[var(--color-divider)] mx-2 my-1" />
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
