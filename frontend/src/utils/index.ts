import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { LeadStatus } from '@/types'

// ── Tailwind class merger ─────────────────────────────────
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ── Date formatting ───────────────────────────────────────
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateRelative(iso: string): string {
  const now = Date.now()
  const then = new Date(iso).getTime()
  const diff = now - then
  const mins = Math.floor(diff / 60_000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return formatDate(iso)
}

// ── Status badge CSS class ────────────────────────────────
export function statusBadgeClass(status: LeadStatus): string {
  const map: Record<LeadStatus, string> = {
    NEW: 'badge badge-new',
    SCRAPED: 'badge badge-scraped',
    ANALYZED: 'badge badge-analyzed',
    OUTREACH_READY: 'badge badge-outreach-ready',
    CONTACTED: 'badge badge-contacted',
    CLOSED: 'badge badge-closed',
  }
  return map[status] ?? 'badge'
}

// ── Score colour ──────────────────────────────────────────
export function scoreColour(score: number): string {
  if (score >= 80) return '#22c55e'
  if (score >= 60) return '#f59e0b'
  return '#ef4444'
}

// ── Truncate ──────────────────────────────────────────────
export function truncate(str: string, max = 40): string {
  return str.length > max ? str.slice(0, max) + '…' : str
}

// ── Error message extraction ──────────────────────────────
export function getErrorMessage(err: unknown): string {
  if (typeof err === 'object' && err !== null) {
    const e = err as Record<string, unknown>

    if (e.response) {
      const r = e.response as Record<string, unknown>
      const d = r.data as Record<string, unknown> | undefined

      if (d?.error && typeof d.error === 'object') {
        const error = d.error as Record<string, unknown>
        if (typeof error.message === 'string' && error.message) return error.message
        if (typeof error.detail === 'string' && error.detail) return error.detail
      }

      if (typeof d?.message === 'string' && d.message) return d.message
    }

    if (e.code === 'ERR_NETWORK') {
      return 'Unable to reach the server. Please check your connection and try again.'
    }

    if (typeof e.message === 'string' && e.message && e.message !== 'Network Error') {
      return e.message
    }
  }
  return 'Something went wrong. Please try again.'
}

export type ToastType = 'success' | 'error'

export interface ToastState {
  msg: string
  type: ToastType
}

// ── Query key factory ─────────────────────────────────────
export const queryKeys = {
  auth: {
    me: ['auth', 'me'] as const,
  },
  leads: {
    all: ['leads'] as const,
    list: (filters: object) => ['leads', 'list', filters] as const,
    detail: (id: string) => ['leads', 'detail', id] as const,
  },
  dashboard: {
    summary: ['dashboard', 'summary'] as const,
    recentLeads: (limit: number, offset: number) =>
      ['dashboard', 'recent-leads', limit, offset] as const,
    statusDist: ['dashboard', 'status-dist'] as const,
    industryDist: ['dashboard', 'industry-dist'] as const,
    cityDist: ['dashboard', 'city-dist'] as const,
  },
  settings: {
    profile: ['settings', 'profile'] as const,
    preferences: ['settings', 'preferences'] as const,
    accountSummary: ['settings', 'account-summary'] as const,
  },
}
