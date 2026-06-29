import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Camera, Search, Loader, Monitor, Smartphone, Maximize2 } from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { screenshotsApi } from '@/services/apiServices'
import { queryKeys, getErrorMessage } from '@/utils'
import type { LeadDetailResponse } from '@/types'

export default function ScreenshotPage() {
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [result, setResult] = useState<LeadDetailResponse | null>(null)
  const [error, setError] = useState('')
  const [lightbox, setLightbox] = useState<string | null>(null)

  const { data: leadsData } = useQuery({
    queryKey: queryKeys.leads.list({ name: search, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
    queryFn: () => leadsApi.list({ name: search || undefined, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
  })

  const leads = leadsData?.data?.items ?? []

  const captureMut = useMutation({
    mutationFn: screenshotsApi.capture,
    onSuccess: async (_, leadId) => {
      const detail = await leadsApi.get(leadId)
      setResult(detail.data)
      setError('')
    },
    onError: (e) => setError(getErrorMessage(e)),
  })

  const screenshots = result?.screenshot

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 1000 }}>
      {/* Lightbox */}
      {lightbox && (
        <div onClick={() => setLightbox(null)} style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#000000cc', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'zoom-out' }}>
          <img src={lightbox} alt="Screenshot" style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: 12, objectFit: 'contain' }} onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <Camera size={20} color="var(--color-brand)" />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Screenshot Viewer</h1>
      </div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 28, marginLeft: 30 }}>
        Capture desktop, mobile, and full-page screenshots using Playwright Chromium
      </p>

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>Select a Lead</div>
        <div style={{ position: 'relative', marginBottom: 12 }}>
          <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input className="input" style={{ paddingLeft: 30 }} placeholder="Search leads…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
          {leads.length === 0 ? (
            <div className="empty-state" style={{ padding: '24px 8px' }}>
              <div className="empty-state-title">No leads yet</div>
              <div className="empty-state-desc">
                <Link to="/discover" className="link-brand">Discover leads →</Link> with websites to capture screenshots.
              </div>
            </div>
          ) : leads.map((lead) => (
            <button key={lead.id} onClick={() => setSelectedId(lead.id)} style={{
              padding: '8px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'left',
              background: selectedId === lead.id ? 'var(--color-brand-subtle)' : 'transparent',
              border: `1px solid ${selectedId === lead.id ? 'var(--color-brand-border)' : 'transparent'}`,
              display: 'flex', justifyContent: 'space-between',
            }}>
              <span style={{ fontSize: 13, fontWeight: 500, color: selectedId === lead.id ? 'var(--color-brand)' : 'var(--color-text-primary)' }}>{lead.name}</span>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{lead.website?.replace('https://', '').slice(0, 30) ?? '—'}</span>
            </button>
          ))}
        </div>
        <button className="btn btn-primary" onClick={() => { if (selectedId) { setResult(null); captureMut.mutate(selectedId) } }} disabled={!selectedId || captureMut.isPending}>
          {captureMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : <Camera size={14} />}
          {captureMut.isPending ? 'Capturing screenshots…' : 'Capture Screenshots'}
        </button>
      </div>

      {error && (
        <div className="alert-error">{error}</div>
      )}

      {captureMut.isPending && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 28, height: 28 }} />
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Launching Playwright browser…</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Capturing desktop, mobile and full-page screenshots</div>
        </div>
      )}

      {screenshots && !captureMut.isPending && (
        <div className="animate-fade-in">
          <div style={{ fontWeight: 600, marginBottom: 16, fontSize: 15 }}>Screenshots for {result?.name}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
            {[
              { label: 'Desktop', url: screenshots.desktop_cloudinary_url, icon: Monitor },
              { label: 'Mobile', url: screenshots.mobile_cloudinary_url, icon: Smartphone },
              { label: 'Full Page', url: screenshots.full_page_cloudinary_url, icon: Maximize2 },
            ].filter((s) => s.url).map(({ label, url, icon: Icon }) => (
              <div key={label} className="card" style={{ padding: 0, overflow: 'hidden', cursor: 'zoom-in' }} onClick={() => setLightbox(url!)}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 14px', borderBottom: '1px solid var(--color-border)' }}>
                  <Icon size={13} color="var(--color-text-muted)" />
                  <span style={{ fontWeight: 500, fontSize: 13 }}>{label}</span>
                </div>
                <img src={url!} alt={`${label} screenshot`} style={{ width: '100%', maxHeight: 200, objectFit: 'cover', display: 'block' }} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
