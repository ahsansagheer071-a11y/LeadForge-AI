/**
 * Sidebar (left navigation).
 * Collapsible on lg / md / sm breakpoints, animated active pill, lucide icons.
 */

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
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { useLocalStorage } from '@/hooks/hooks';
import { Tooltip } from '@/components/Tooltip';
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
        'h-[calc(100vh-3.5rem)] sticky top-[3.5rem]',
        'border-r border-[var(--color-border)] bg-[var(--color-surface)]',
        'flex flex-col transition-[width] duration-200 ease-out',
        collapsed ? 'w-[76px]' : 'w-[244px]',
        'overflow-hidden',
        className,
      )}
    >
      {/* Logo */}
      <div
        className={cn(
          'flex items-center gap-2.5 px-4 pt-5 pb-3',
          collapsed && 'justify-center px-2',
        )}
      >
        <div className="size-8 rounded-[9px] bg-[var(--color-brand)] flex items-center justify-center shadow-[0_2px_10px_color-mix(in_oklab,var(--color-brand)_45%,transparent)]">
          <Zap className="size-4 text-white" strokeWidth={2.5} />
        </div>
        {!collapsed && (
          <div className="overflow-hidden">
            <p className="text-[13.5px] font-semibold leading-tight tracking-tight">
              LeadForge
            </p>
            <p className="text-[10.5px] text-[var(--color-text-muted)] leading-tight">
              Premium
            </p>
          </div>
        )}
      </div>

      {/* Primary */}
      <nav className="px-2 mt-2 space-y-0.5" onClick={onNavigate}>
        {!collapsed && (
          <p className="px-3 pt-2 pb-1 text-[10.5px] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
            Workspace
          </p>
        )}
        {primaryItems.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}

        {!collapsed && (
          <p className="px-3 pt-4 pb-1 text-[10.5px] uppercase tracking-wider text-[var(--color-text-muted)] font-semibold">
            Insights
          </p>
        )}
        {NAV_HISTORY.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}
      </nav>

      <div className="flex-1" />

      {/* Bottom section */}
      <nav className="px-2 pb-3 space-y-0.5" onClick={onNavigate}>
        {NAV_BOTTOM.map((item) => (
          <SidebarItem key={item.to} item={item} collapsed={collapsed} />
        ))}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            'w-full mt-3 flex items-center gap-2',
            'px-3 py-2 rounded-[8px] text-[12.5px] font-medium',
            'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)]',
            'hover:text-[var(--color-text)] transition-colors',
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
          'group relative flex items-center gap-2.5 px-3 py-2 rounded-[9px]',
          'text-[13px] font-medium',
          'transition-colors duration-150',
          collapsed && 'justify-center',
          isActive
            ? 'bg-[var(--color-brand-soft)] text-[var(--color-brand)]'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
        )
      }
    >
      {({ isActive }) => (
        <>
          <item.icon
            className={cn(
              'size-[15px] flex-shrink-0',
              isActive ? 'text-[var(--color-brand)]' : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text)]',
            )}
            strokeWidth={2}
          />
          {!collapsed && (
            <>
              <span className="flex-1 truncate">{item.label}</span>
              {item.badge && (
                <span
                  className={cn(
                    'text-[10px] rounded-full px-1.5 py-0.5 font-semibold',
                    isActive
                      ? 'bg-[var(--color-brand)] text-white'
                      : 'bg-[var(--color-surface-overlay)] text-[var(--color-text-muted)]',
                  )}
                >
                  {item.badge}
                </span>
              )}
            </>
          )}
          {isActive && (
            <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-[var(--color-brand)]" />
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
