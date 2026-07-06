/**
 * Error / empty-state components.
 */

import * as React from 'react';
import {
  AlertTriangle,
  Inbox,
  WifiOff,
  type LucideIcon,
} from 'lucide-react';
import { Button } from './Button';
import { cn } from '@/utils';

/* ── ErrorBoundary ─────────────────────────────────────────── */

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: (err: Error, reset: () => void) => React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', error, info);
  }

  reset = () => this.setState({ hasError: false, error: null });

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) return this.props.fallback(this.state.error, this.reset);
      return (
        <div className="flex flex-col items-center justify-center h-full p-10 gap-4 text-center">
          <div className="size-12 rounded-full bg-red-500/10 flex items-center justify-center">
            <AlertTriangle className="size-6 text-red-500" />
          </div>
          <h2 className="text-base font-semibold tracking-tight">Something went wrong</h2>
          <p className="text-[12.5px] text-[var(--color-text-muted)] max-w-sm">
            {this.state.error.message}
          </p>
          <Button variant="outline" onClick={this.reset}>Reload</Button>
        </div>
      );
    }
    return this.props.children;
  }
}

/* ── ApiError (inline) ─────────────────────────────────────── */

export function ApiError({
  title = 'Request failed',
  message,
  onRetry,
  className,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-[12px] border border-red-500/30 bg-red-500/5',
        'text-red-600 dark:text-red-400 p-4',
        'flex items-start gap-3',
        className,
      )}
    >
      <AlertTriangle className="size-4 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-[13px] font-medium">{title}</p>
        {message && (
          <p className="text-[12px] mt-0.5 opacity-90">{message}</p>
        )}
      </div>
      {onRetry && (
        <Button size="sm" variant="ghost" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

/* ── NetworkError ─────────────────────────────────────────── */

export function NetworkError({ onRetry }: { onRetry?: () => void }) {
  return (
    <ApiError
      title="Connection lost"
      message="We can't reach our servers right now. Check your connection and try again."
      onRetry={onRetry}
    />
  );
}

/* ── EmptyState ───────────────────────────────────────────── */

export function EmptyState({
  title = 'No items yet',
  message,
  icon: Icon = Inbox,
  action,
  className,
}: {
  title?: string;
  message?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'rounded-[14px] border border-dashed border-[var(--color-border)]',
        'bg-[var(--color-surface-hover)]/40',
        'flex flex-col items-center justify-center p-10 gap-3 text-center',
        className,
      )}
    >
      <div className="size-12 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
        <Icon className="size-5 text-[var(--color-text-muted)]" />
      </div>
      <h3 className="text-[14.5px] font-semibold tracking-tight">{title}</h3>
      {message && (
        <p className="text-[12.5px] text-[var(--color-text-muted)] max-w-sm">
          {message}
        </p>
      )}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/* ── NoData (compact) ─────────────────────────────────────── */

export function NoData({
  title = 'No data available',
  message = 'Try adjusting filters or refresh to fetch new data.',
}: { title?: string; message?: string }) {
  return (
    <div className="flex items-center gap-3 p-4 rounded-[10px] bg-[var(--color-surface-hover)]/40 text-[var(--color-text-muted)]">
      <WifiOff className="size-4 flex-shrink-0" />
      <div>
        <p className="text-[12.5px] font-medium text-[var(--color-text)]">{title}</p>
        <p className="text-[11.5px]">{message}</p>
      </div>
    </div>
  );
}
