import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '@/services/settingsService'
import { queryKeys, getErrorMessage } from '@/utils'
import { Loader, User, Lock, Sliders, BarChart2 } from 'lucide-react'
import type { UserProfileUpdate, ChangePasswordRequest, UserPreferencesUpdate } from '@/types'

type Tab = 'profile' | 'password' | 'preferences' | 'summary'

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('profile')
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)
  const qc = useQueryClient()

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const { data: profileData, isLoading: profileLoading } = useQuery({
    queryKey: queryKeys.settings.profile,
    queryFn: settingsApi.getProfile,
  })
  const { data: prefsData, isLoading: prefsLoading } = useQuery({
    queryKey: queryKeys.settings.preferences,
    queryFn: settingsApi.getPreferences,
  })
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: queryKeys.settings.accountSummary,
    queryFn: settingsApi.getAccountSummary,
    enabled: activeTab === 'summary',
  })

  const user = profileData?.data
  const prefs = prefsData?.data
  const summary = summaryData?.data

  // ── Profile form state ─────────────────────────────────
  const [profile, setProfile] = useState<UserProfileUpdate>({})
  const profileMut = useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.settings.profile }); showToast('Profile updated') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })

  // ── Password form state ────────────────────────────────
  const [pwForm, setPwForm] = useState<ChangePasswordRequest>({ current_password: '', new_password: '' })
  const [confirmPw, setConfirmPw] = useState('')
  const pwMut = useMutation({
    mutationFn: settingsApi.changePassword,
    onSuccess: () => { showToast('Password changed'); setPwForm({ current_password: '', new_password: '' }); setConfirmPw('') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const handlePwSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (pwForm.new_password !== confirmPw) { showToast('Passwords do not match', 'error'); return }
    if (pwForm.new_password.length < 8) { showToast('Password must be at least 8 characters', 'error'); return }
    pwMut.mutate(pwForm)
  }

  // ── Preferences ────────────────────────────────────────
  const prefsMut = useMutation({
    mutationFn: settingsApi.updatePreferences,
    onSuccess: () => { qc.invalidateQueries({ queryKey: queryKeys.settings.preferences }); showToast('Preferences saved') },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })
  const [prefsForm, setPrefsForm] = useState<UserPreferencesUpdate>({})

  const TABS = [
    { id: 'profile' as Tab, label: 'Profile', icon: User },
    { id: 'password' as Tab, label: 'Password', icon: Lock },
    { id: 'preferences' as Tab, label: 'Preferences', icon: Sliders },
    { id: 'summary' as Tab, label: 'Account', icon: BarChart2 },
  ]

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 800 }}>
      {toast && (
        <div className={`toast toast-${toast.type}`}>{toast.msg}</div>
      )}

      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Settings</h1>

      <div className="settings-layout">
        {/* Sidebar nav */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {TABS.map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => setActiveTab(id)} className={`nav-item${activeTab === id ? ' active' : ''}`}>
              <Icon size={15} /> {label}
            </button>
          ))}
        </nav>

        {/* Content */}
        <div>
          {/* Profile */}
          {activeTab === 'profile' && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 20 }}>Profile Information</div>
              {profileLoading ? <div className="spinner" /> : (
                <form onSubmit={(e) => {
                  e.preventDefault()
                  const payload = Object.fromEntries(
                    Object.entries(profile).filter(([, v]) => v !== undefined && v !== '')
                  ) as UserProfileUpdate
                  if (Object.keys(payload).length === 0) {
                    showToast('No changes to save', 'error')
                    return
                  }
                  profileMut.mutate(payload)
                }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {[
                    { label: 'Full Name', key: 'full_name', placeholder: user?.full_name ?? 'Your name', type: 'text' },
                    { label: 'Company', key: 'company_name', placeholder: user?.company_name ?? 'Your agency', type: 'text' },
                    { label: 'Phone', key: 'phone', placeholder: user?.phone ?? '+1 234 567 890', type: 'tel' },
                    { label: 'Country', key: 'country', placeholder: user?.country ?? 'United States', type: 'text' },
                    { label: 'Timezone', key: 'timezone', placeholder: user?.timezone ?? 'UTC', type: 'text' },
                  ].map(({ label, key, placeholder, type }) => (
                    <div key={key}>
                      <label className="label">{label}</label>
                      <input className="input" type={type} placeholder={placeholder}
                        value={(profile as Record<string, string>)[key] ?? ''}
                        onChange={(e) => setProfile((p) => ({ ...p, [key]: e.target.value }))} />
                    </div>
                  ))}
                  <div>
                    <label className="label">Email</label>
                    <input className="input" value={user?.email ?? ''} disabled style={{ opacity: 0.6 }} />
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4 }}>Email cannot be changed</div>
                  </div>
                  <button className="btn btn-primary" type="submit" disabled={profileMut.isPending} style={{ alignSelf: 'flex-start' }}>
                    {profileMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : null}
                    Save Changes
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Password */}
          {activeTab === 'password' && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 20 }}>Change Password</div>
              <form onSubmit={handlePwSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                  <label className="label">Current Password</label>
                  <input className="input" type="password" placeholder="••••••••" required value={pwForm.current_password}
                    onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))} />
                </div>
                <div>
                  <label className="label">New Password</label>
                  <input className="input" type="password" placeholder="Min. 8 characters" required value={pwForm.new_password}
                    onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))} />
                </div>
                <div>
                  <label className="label">Confirm New Password</label>
                  <input className="input" type="password" placeholder="Repeat new password" required value={confirmPw}
                    onChange={(e) => setConfirmPw(e.target.value)} />
                </div>
                <button className="btn btn-primary" type="submit" disabled={pwMut.isPending} style={{ alignSelf: 'flex-start' }}>
                  {pwMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : null}
                  Update Password
                </button>
              </form>
            </div>
          )}

          {/* Preferences */}
          {activeTab === 'preferences' && (
            <div className="card">
              <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 20 }}>Display Preferences</div>
              {prefsLoading ? <div className="spinner" /> : (
                <form onSubmit={(e) => { e.preventDefault(); prefsMut.mutate(prefsForm) }} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <label className="label">Language</label>
                    <select className="select" value={prefsForm.language ?? prefs?.language ?? 'en'}
                      onChange={(e) => setPrefsForm((p) => ({ ...p, language: e.target.value }))}>
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                      <option value="de">German</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Default Page Size</label>
                    <select className="select" value={prefsForm.default_page_size ?? prefs?.default_page_size ?? 10}
                      onChange={(e) => setPrefsForm((p) => ({ ...p, default_page_size: +e.target.value }))}>
                      {[10, 15, 25, 50].map((n) => <option key={n} value={n}>{n} rows</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input type="checkbox" id="email_notif" checked={prefsForm.email_notifications ?? prefs?.email_notifications ?? true}
                      onChange={(e) => setPrefsForm((p) => ({ ...p, email_notifications: e.target.checked }))} />
                    <label htmlFor="email_notif" style={{ fontSize: 13, cursor: 'pointer' }}>Email notifications</label>
                  </div>
                  <button className="btn btn-primary" type="submit" disabled={prefsMut.isPending} style={{ alignSelf: 'flex-start' }}>
                    {prefsMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : null}
                    Save Preferences
                  </button>
                </form>
              )}
            </div>
          )}

          {/* Account Summary */}
          {activeTab === 'summary' && (
            <div>
              {summaryLoading ? (
                <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 48 }}>
                  <div className="spinner" />
                </div>
              ) : summary ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div className="card">
                    <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>Account Overview</div>
                    <div style={{ display: 'flex', gap: 20 }}>
                      {[
                        { label: 'Total Leads', value: summary.total_leads },
                        { label: 'Audited', value: summary.total_audits },
                        { label: 'Outreach', value: summary.total_outreach },
                      ].map(({ label, value }) => (
                        <div key={label} style={{ flex: 1, textAlign: 'center', padding: 16, background: 'var(--color-surface-raised)', borderRadius: 10 }}>
                          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--color-brand)' }}>{value}</div>
                          <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 4 }}>{label}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="card">
                    <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 15 }}>Account Details</div>
                    {[
                      { label: 'Email', value: summary.user_info.email },
                      { label: 'Role', value: summary.user_info.role },
                      { label: 'Account Created', value: new Date(summary.account_created_at).toLocaleDateString() },
                      { label: 'Status', value: summary.user_info.is_active ? '✅ Active' : '❌ Inactive' },
                    ].map(({ label, value }) => (
                      <div key={label} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--color-border)', fontSize: 13 }}>
                        <span style={{ color: 'var(--color-text-muted)' }}>{label}</span>
                        <span style={{ fontWeight: 500 }}>{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
