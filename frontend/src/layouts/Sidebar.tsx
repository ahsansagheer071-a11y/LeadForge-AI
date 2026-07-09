import * as React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpenDot,
  Sparkles,
  Eye,
  CloudUpload,
  History,
  BarChart3,
  Settings,
  HelpCircle,
  ChevronsLeft,
  ChevronsRight,
  type LucideIcon,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { useLocalStorage } from '@/hooks/hooks';
import { Tooltip } from '@/components/Tooltip';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { dashboardService } from '@/services/services';

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
  badge?: string;
}

const NAV_PRIMARY: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/projects', label: 'Projects', icon: FolderOpenDot },
  { to: '/generation', label: 'Generation', icon: Sparkles },
  { to: '/preview', label: 'Preview', icon: Eye },
  { to: '/deployment', label: 'Deployment', icon: CloudUpload },
];

const NAV_HISTORY: NavItem[] = [
  { to: '/history', label: 'History', icon: History },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
];

const NAV_BOTTOM: NavItem[] = [
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/help', label: 'Help', icon: HelpCircle },
];

interface SidebarProps {
  className?: string;
  onNavigate?: () => void;
}

export function Sidebar({ className, onNavigate }: SidebarProps) {
  const [collapsed, setCollapsed] = useLocalStorage<boolean>('lf_sidebar_collapsed', false);
  const { data: summary } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
  });
  const primaryItems = React.useMemo(
    () => NAV_PRIMARY.map((item) => (
      item.to === '/projects' && summary ? { ...item, badge: String(summary.total_leads) } : item
    )),
    [summary],
  );

  return (
    <aside
      className={cn(
        'flex flex-col z-20 overflow-hidden',
        'bg-[var(--color-glass)] backdrop-blur-xl border border-[var(--color-glass-border)] rounded-[var(--radius-xl)] shadow-2xl',
        'transition-all duration-300 ease-out',
        collapsed ? 'w-[76px]' : 'w-[260px]',
        className,
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex items-center px-4 pt-5 pb-4 border-b border-[var(--color-divider)]',
          collapsed && 'justify-center px-2',
        )}
      >
        <LeadForgeLogo variant={collapsed ? 'compact' : 'full'} size={collapsed ? 28 : 30} />
      </div>

      {/* Tagline */}
      {!collapsed && (
        <div className="px-4 pt-3 pb-2">
          <p className="text-[9.5px] uppercase tracking-[0.22em] text-[var(--color-text-muted)] font-mono leading-relaxed">
            Discover. Audit. Build. Convert.
          </p>
        </div>
      )}

      {/* Primary */}
      <nav className="px-2 mt-3 space-y-0.5 flex-1 overflow-y-auto lf-thin-scroll" onClick={onNavigate}>
        {!collapsed && (
          <p className="px-3 pt-1 pb-1.5 text-[9.5px] uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold font-mono">
            Workspace
          </p>
        )}
        {primaryItems.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}

        {!collapsed && (
          <p className="px-3 pt-5 pb-1.5 text-[9.5px] uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold font-mono">
            Insights
          </p>
        )}
        {NAV_HISTORY.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Bottom section */}
      <nav className="px-2 pb-3 space-y-0.5 border-t border-[var(--color-divider)] pt-3" onClick={onNavigate}>
        {NAV_BOTTOM.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'w-full mt-2 flex items-center gap-2',
            'px-3 py-2 rounded-[var(--radius-md)] text-[12px] font-medium',
            'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]',
            'hover:text-[var(--color-text-secondary)] transition-colors',
            collapsed && 'justify-center',
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronsRight className="size-4" /> : <ChevronsLeft className="size-4" />}
          {!collapsed && 'Collapse'}
        </button>
      </nav>
    </aside>
  );
}

function SidebarItem({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
  const Body = (
    <NavLink
      to={item.to}
      end={item.exact}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-md)]',
          'text-[13px] font-medium',
          'transition-all duration-[var(--anim-fast)]',
          collapsed && 'justify-center',
          isActive
            ? 'bg-gradient-to-r from-[var(--color-brand-soft)] to-transparent text-[#0ea5e9] shadow-[inset_0_0_0_1px_color-mix(in_oklab,var(--color-brand)_10%,transparent)]'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
        )
      }
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'size-[16px] flex-shrink-0 transition-all',
              isActive
                ? 'text-[#0ea5e9] drop-shadow-[0_0_8px_rgba(14,165,233,0.8)]'
                : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text)]',
            )}
            strokeWidth={isActive ? 2.5 : 2}
          />
          {!collapsed && (
            <>
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span
                  className={cn(
                    'text-[10px] rounded-full px-1.5 py-0.5 font-semibold font-mono',
                    isActive
                      ? 'bg-[var(--color-brand)] text-white shadow-[0_0_8px_color-mix(in_oklab,var(--color-brand)_40%,transparent)]'
                      : 'bg-[var(--color-surface-overlay)] text-[var(--color-text-muted)]',
                  )}
                >
                  {item.badge}
                </span>
              )}
            </>
          )}
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-[60%] rounded-r-full bg-[#0ea5e9] shadow-[0_0_12px_#0ea5e9]" />
          )}
        </>
      )}
    </NavLink>
  );

  return collapsed ? (
    <Tooltip side="right" content={item.label}>
      {Body}
    </Tooltip>
  ) : (
    Body
  );
}
