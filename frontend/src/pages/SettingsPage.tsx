import { Info, Calendar, Hash } from 'lucide-react';
import { useAuthStore } from '@/store';
import { Badge } from '@/components/Badge';
import { Label, Input } from '@/components/Input';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    : '—';

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Header ──────────────────────────────────────────── */}
      <div>
        <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Settings</h1>
        <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Manage your account and workspace preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* ── Main content ────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Profile */}
          <Panel title="Profile" subtitle="Your account information">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Full Name</Label>
                <Input value={user?.full_name ?? '—'} readOnly />
                <p className="text-[10px] font-mono text-[var(--color-text-muted)] mt-1">Read-only in current version</p>
              </div>
              <div>
                <Label>Email</Label>
                <Input value={user?.email ?? '—'} type="email" readOnly />
                <p className="text-[10px] font-mono text-[var(--color-text-muted)] mt-1">Read-only in current version</p>
              </div>
            </div>
          </Panel>

          {/* Company */}
          <Panel title="Company" subtitle="Organization details">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label>Company Name</Label>
                <Input placeholder="Not configured" readOnly />
              </div>
              <div>
                <Label>Industry</Label>
                <Input placeholder="Not configured" readOnly />
              </div>
            </div>
            <p className="text-[11px] font-mono text-[var(--color-text-muted)] mt-4 flex items-center gap-1.5">
              <Info size={12} /> Company settings are read-only in the current version.
            </p>
          </Panel>

          {/* Account */}
          <Panel title="Account" subtitle="Account details and metadata">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <Label>Role</Label>
                <div className="flex items-center gap-2">
                  <span className="text-[13px] text-[var(--color-text)] font-medium capitalize">{user?.role ?? 'member'}</span>
                  <Badge tone="info" className="text-[9px]">Current</Badge>
                </div>
              </div>
              <div>
                <Label>Member Since</Label>
                <div className="flex items-center gap-1.5 text-[13px] text-[var(--color-text)] font-medium">
                  <Calendar size={13} className="text-[var(--color-text-muted)]" />
                  {memberSince}
                </div>
              </div>
              <div>
                <Label>User ID</Label>
                <div className="flex items-center gap-1.5 text-[12px] font-mono text-[var(--color-text-muted)]">
                  <Hash size={12} />
                  {user?.id?.slice(0, 12) ?? '—'}...
                </div>
              </div>
            </div>
          </Panel>
        </div>

        {/* ── Sidebar ─────────────────────────────────────── */}
        <div className="space-y-5 lg:sticky lg:top-24">
          {/* Appearance */}
          <Panel title="Appearance" subtitle="Visual preferences">
            <div className="space-y-3">
              <p className="text-[12px] text-[var(--color-text-secondary)]">Choose your preferred theme for the workspace.</p>
              <ThemeSwitcher />
              <p className="text-[11px] text-[var(--color-text-muted)]">
                System mode follows your operating system preference.
              </p>
            </div>
          </Panel>

          {/* System info */}
          <Panel title="System" subtitle="Technical information">
            <div className="space-y-2.5">
              <InfoRow label="Version" value="1.0.0" />
              <InfoRow label="Environment" value={import.meta.env.MODE || 'production'} />
              <InfoRow label="Frontend" value="React + Vite" />
              <InfoRow label="Backend" value="FastAPI" />
            </div>
          </Panel>

          {/* Disclaimer */}
          <div className="p-3 rounded-[var(--radius-xl)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)]">
            <div className="flex items-start gap-2">
              <Info size={14} className="text-[var(--color-brand)] shrink-0 mt-0.5" />
              <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                Profile and company settings display your current account data. Edit functionality will be available in a future update.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────── */

function Panel({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] transition-colors hover:border-[var(--color-border-strong)]">
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">{title}</h3>
        {subtitle && <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{subtitle}</p>}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string | null | undefined }) {
  if (value == null || value === '') return null;
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] text-[var(--color-text-muted)] shrink-0">{label}</span>
      <span className="text-[12px] text-[var(--color-text-secondary)] text-right font-mono truncate">{value}</span>
    </div>
  );
}
