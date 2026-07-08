import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Tailwind-aware class combinator.
 * Lets you pass `className` strings while keeping Tailwind
 * conflicts resolved (latter overrides former).
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Safe string formatter for unexpected values. */
export function getErrorMessage(err: unknown): string {
  if (!err) return 'Unknown error';
  if (typeof err === 'string') return err;
  if (err instanceof Error) return err.message;
  try {
    const json = JSON.stringify(err);
    if (json && json !== '{}') return json;
  } catch {
    /* fallthrough */
  }
  return String(err);
}

/** Format ISO timestamp → human readable short form. */
export function formatRelative(iso: string | Date | null | undefined): string {
  if (!iso) return '—';
  const d = typeof iso === 'string' ? new Date(iso) : iso;
  if (Number.isNaN(d.getTime())) return '—';
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return d.toLocaleDateString();
}

/** Format bytes → human readable. */
export function formatBytes(bytes: number | null | undefined, decimals = 1): string {
  if (bytes == null || Number.isNaN(bytes)) return '—';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1);
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/** Compact number formatter (1234 → 1.2K). */
export function formatCompact(n: number | null | undefined): string {
  if (n == null) return '—';
  return Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
}

/** Currency formatter (USD by default). */
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Stable random id (URL-safe, no dashes). */
export function randId(prefix = 'id', len = 8): string {
  const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
  let out = '';
  const cryptoObj = typeof crypto !== 'undefined' ? crypto : undefined;
  if (cryptoObj?.getRandomValues) {
    const arr = new Uint8Array(len);
    cryptoObj.getRandomValues(arr);
    for (let i = 0; i < len; i++) out += chars[arr[i] % chars.length];
  } else {
    for (let i = 0; i < len; i++) out += chars[Math.floor(Math.random() * chars.length)];
  }
  return `${prefix}_${out}`;
}

/** Local-storage safe get (SSR-safe + JSON). */
export function safeGet<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (raw == null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function safeSet(key: string, value: unknown): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore quota errors */
  }
}

export function safeRemove(key: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(key);
  } catch { /* ignore */ }
}

/** Truncate a string safely. */
export function truncate(s: string, max = 80, ellipsis = '…'): string {
  if (!s) return '';
  return s.length > max ? `${s.slice(0, max - 1)}${ellipsis}` : s;
}

/** Initials from a human name. */
export function initialsFromName(name?: string | null, fallback = 'LF'): string {
  if (!name) return fallback;
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || fallback;
}

/** Sleep — used in retries / animations. */
export function sleep(ms: number): Promise<void> {
  return new Promise((res) => setTimeout(res, ms));
}

/** Score colour — returns a hex colour given a 0-100 score. */
export function scoreColour(score: number): string {
  if (score >= 80) return '#22c55e';
  if (score >= 60) return '#eab308';
  if (score >= 40) return '#f97316';
  return '#dc2626';
}

/** Score tier label. */
export function scoreTier(score: number): 'hot' | 'warm' | 'cold' {
  if (score >= 80) return 'hot';
  if (score >= 60) return 'warm';
  return 'cold';
}

/** Status CSS badge class map (Tailwind classes). */
const STATUS_TONE: Record<string, string> = {
  NEW: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/30',
  SCRAPED: 'bg-[var(--color-brand-soft)] text-[var(--color-brand)] border border-[var(--color-brand-border)]',
  ANALYZED: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30',
  OUTREACH_READY: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
  CONTACTED: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/30',
  CLOSED: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
  draft: 'bg-[var(--color-surface-overlay)] text-[var(--color-text-secondary)] border border-[var(--color-border)]',
  queued: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/30',
  generating: 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/30',
  previewing: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30',
  deployed: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30',
  failed: 'bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/30',
  archived: 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]',
};

export function statusBadgeClass(status: string): string {
  return STATUS_TONE[status] ?? 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]';
}
