import * as React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpenDot,
  Globe,
  Activity,
  Settings,
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
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  exact?: boolean;
  badge?: string;
}

const NAV_PRIMARY: NavItem[] = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard, exact: true },
  { to: '/projects', label: 'Leads', icon: FolderOpenDot },
  { to: '/generation', label: 'Websites', icon: Globe },
  { to: '/history', label: 'Activity', icon: Activity },
  { to: '/settings', label: 'Settings', icon: Settings },
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
        'bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[var(--radius-lg)]',
        'transition-all duration-[var(--anim-normal)] ease-out',
        collapsed ? 'w-[68px]' : 'w-[240px]',
        className,
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex items-center px-4 py-4 border-b border-[var(--color-divider)]',
          collapsed && 'justify-center px-2',
        )}
      >
        <LeadForgeLogo variant={collapsed ? 'compact' : 'full'} size={collapsed ? 24 : 26} />
      </div>

      {/* Navigation */}
      <nav className="px-2 mt-3 space-y-0.5 flex-1 overflow-y-auto lf-thin-scroll" onClick={onNavigate}>
        {!collapsed && (
          <p className="lf-label px-3 pt-1 pb-1.5 text-[10px]">
            Workspace
          </p>
        )}
        {primaryItems.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Bottom section */}
      <nav className="px-2 pb-3 space-y-0.5 border-t border-[var(--color-divider)] pt-3" onClick={onNavigate}>
        {/* Theme switcher */}
        {!collapsed && (
          <div className="px-3 py-2">
            <ThemeSwitcher />
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'w-full mt-1 flex items-center gap-2',
            'px-3 py-2 rounded-[var(--radius-md)] text-[12px] font-medium',
            'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]',
            'hover:text-[var(--color-text-secondary)] transition-colors duration-[var(--anim-fast)]',
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
          'group relative flex items-center gap-3 px-3 py-2 rounded-[var(--radius-md)]',
          'text-[13px] font-medium',
          'transition-all duration-[var(--anim-fast)]',
          collapsed && 'justify-center',
          isActive
            ? 'bg-[var(--color-brand-subtle)] text-[var(--color-brand)]'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
        )
      }
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'size-[16px] flex-shrink-0 transition-colors duration-[var(--anim-fast)]',
              isActive
                ? 'text-[var(--color-brand)]'
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
                    'text-[10px] rounded-full px-1.5 py-0.5 font-medium font-mono',
                    isActive
                      ? 'bg-[var(--color-brand)] text-white'
                      : 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]',
                  )}
                >
                  {item.badge}
                </span>
              )}
            </>
          )}
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-[60%] rounded-r-full bg-[var(--color-brand)]" />
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
