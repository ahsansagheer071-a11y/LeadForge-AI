import { User, Building2, Palette, Shield, Info, Calendar, Hash } from 'lucide-react';
import { useAuthStore } from '@/store';
import { PremiumCard } from '@/components/PremiumCard';
import { Badge } from '@/components/Badge';
import { Label, Input } from '@/components/Input';

export function SettingsPage() {
  const user = useAuthStore((s) => s.user);

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    : '—';

  return (
    <div className="space-y-8 lf-fade-in">
      {/* Header */}
      <div>
        <h1 className="lf-display text-white mb-1">Workspace <span className="lf-display-gradient">Settings</span></h1>
        <p className="text-[13px] text-[var(--color-text-secondary)] font-mono">Manage your account and workspace preferences</p>
      </div>

      {/* Profile Section */}
      <PremiumCard innerClassName="p-6 lg:p-8">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--color-border)]">
          <div className="size-10 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center">
            <User size={18} className="text-[#0ea5e9]" />
          </div>
          <div>
            <h2 className="text-[15px] font-bold text-white">Profile</h2>
            <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Your account information</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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
      </PremiumCard>

      {/* Company Section */}
      <PremiumCard innerClassName="p-6 lg:p-8">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--color-border)]">
          <div className="size-10 rounded-full bg-gradient-to-br from-[#06b6d4]/20 to-[#0ea5e9]/20 border border-[#06b6d4]/30 flex items-center justify-center">
            <Building2 size={18} className="text-[#06b6d4]" />
          </div>
          <div>
            <h2 className="text-[15px] font-bold text-white">Company</h2>
            <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Organization details</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
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
      </PremiumCard>

      {/* Theme Section */}
      <PremiumCard innerClassName="p-6 lg:p-8">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--color-border)]">
          <div className="size-10 rounded-full bg-gradient-to-br from-[#8b5cf6]/20 to-[#a78bfa]/20 border border-[#8b5cf6]/30 flex items-center justify-center">
            <Palette size={18} className="text-[#8b5cf6]" />
          </div>
          <div>
            <h2 className="text-[15px] font-bold text-white">Theme</h2>
            <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Visual preferences</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
            <div className="size-4 rounded-full bg-gradient-to-br from-[#0f172a] to-[#1e293b] border border-slate-600" />
            <span className="text-[13px] font-medium text-white">Dark</span>
          </div>
          <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Dark mode is the default theme.</p>
        </div>
      </PremiumCard>

      {/* Account Section */}
      <PremiumCard innerClassName="p-6 lg:p-8">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-[var(--color-border)]">
          <div className="size-10 rounded-full bg-gradient-to-br from-[#10b981]/20 to-[#059669]/20 border border-[#10b981]/30 flex items-center justify-center">
            <Shield size={18} className="text-[#10b981]" />
          </div>
          <div>
            <h2 className="text-[15px] font-bold text-white">Account</h2>
            <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Account details and metadata</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div>
            <Label>Role</Label>
            <div className="flex items-center gap-2">
              <span className="text-[13px] text-white font-medium capitalize">{user?.role ?? 'member'}</span>
              <Badge tone="info" className="text-[9px]">Current</Badge>
            </div>
          </div>
          <div>
            <Label>Member Since</Label>
            <div className="flex items-center gap-1.5 text-[13px] text-white font-medium">
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
      </PremiumCard>

      {/* Disclaimer */}
      <PremiumCard variant="subtle" innerClassName="p-5 flex items-center gap-3">
        <Info size={16} className="text-[#0ea5e9] shrink-0" />
        <p className="text-[12px] text-[var(--color-text-secondary)]">
          Profile and company settings display your current account data. Edit functionality will be available in a future update.
        </p>
      </PremiumCard>
    </div>
  );
}
