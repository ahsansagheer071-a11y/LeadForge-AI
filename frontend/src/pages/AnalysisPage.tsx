import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Globe, Search, Loader, AlertCircle, CheckCircle } from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { analysisApi } from '@/services/apiServices'
import { queryKeys, getErrorMessage } from '@/utils'
import type { LeadResponse, WebsiteAnalysisResponse } from '@/types'

export default function AnalysisPage() {
  const [search, setSearch] = useState('')
  const [selectedLead, setSelectedLead] = useState<LeadResponse | null>(null)
  const [result, setResult] = useState<WebsiteAnalysisResponse | null>(null)
  const [error, setError] = useState('')

  const { data: leadsData, isLoading: leadsLoading } = useQuery({
    queryKey: queryKeys.leads.list({ name: search, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
    queryFn: () => leadsApi.list({ name: search || undefined, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
    enabled: true,
  })

  const leads = leadsData?.data?.items ?? []

  const analysisMut = useMutation({
    mutationFn: analysisApi.analyze,
    onSuccess: (data) => { setResult(data?.data ?? null); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })

  const handleRun = () => {
    if (!selectedLead) return
    setError(''); setResult(null)
    analysisMut.mutate(selectedLead.id)
  }

  const boolBadge = (v: boolean | null) => v
    ? <span style={{ color: 'var(--color-success)', fontSize: 12 }}>✅ Yes</span>
    : <span style={{ color: 'var(--color-text-muted)', fontSize: 12 }}>❌ No</span>

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <Globe size={20} color="var(--color-brand)" />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Website Analysis</h1>
      </div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 28, marginLeft: 30 }}>
        Crawl and analyze any lead's website for SEO, UX, and content insights
      </p>

      {/* Lead picker */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ marginBottom: 12, fontWeight: 600, fontSize: 14 }}>Select a Lead</div>
        <div style={{ position: 'relative', marginBottom: 12 }}>
          <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input className="input" style={{ paddingLeft: 30 }} placeholder="Search leads…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {leadsLoading ? <div className="spinner" /> : (
          <div style={{ maxHeight: 200, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
            {leads.length === 0 ? (
              <div className="empty-state" style={{ padding: '24px 8px' }}>
                <div className="empty-state-title">No leads found</div>
                <div className="empty-state-desc">
                  <Link to="/discover" className="link-brand">Discover leads →</Link> to run website analysis.
                </div>
              </div>
            ) : leads.map((lead) => (
              <button key={lead.id} onClick={() => setSelectedLead(lead)} style={{
                padding: '8px 12px', borderRadius: 8, background: selectedLead?.id === lead.id ? 'var(--color-brand-subtle)' : 'transparent',
                border: `1px solid ${selectedLead?.id === lead.id ? 'var(--color-brand-border)' : 'transparent'}`,
                cursor: 'pointer', textAlign: 'left', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <span style={{ fontSize: 13, fontWeight: 500, color: selectedLead?.id === lead.id ? 'var(--color-brand)' : 'var(--color-text-primary)' }}>{lead.name}</span>
                <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{lead.city}</span>
              </button>
            ))}
          </div>
        )}
        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--color-border)' }}>
          <button className="btn btn-primary" onClick={handleRun} disabled={!selectedLead || analysisMut.isPending}>
            {analysisMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : <Globe size={14} />}
            {analysisMut.isPending ? 'Analyzing…' : selectedLead ? `Analyze ${selectedLead.name}` : 'Select a lead first'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-error">
          <AlertCircle size={14} style={{ flexShrink: 0 }} /> {error}
        </div>
      )}

      {result && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--color-success)', fontSize: 13, fontWeight: 500 }}>
            <CheckCircle size={16} /> Analysis complete for {selectedLead?.name}
          </div>

          {/* Overview */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>Page Overview</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {[
                { label: 'Title', value: result.page_title ?? '—' },
                { label: 'Language', value: result.website_language ?? '—' },
                { label: 'HTTP Status', value: result.http_status_code ?? '—' },
                { label: 'Load Time', value: result.response_time_ms ? `${result.response_time_ms}ms` : '—' },
                { label: 'HTTPS', value: boolBadge(result.https_enabled) },
                { label: 'HTML Size', value: result.html_size_kb ? `${result.html_size_kb} KB` : '—' },
              ].map(({ label, value }) => (
                <div key={label} style={{ padding: '8px 0', borderBottom: '1px solid var(--color-border)' }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 13 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Content structure */}
          <div className="card">
            <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>Content Structure</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'H1 Tags', value: result.h1_count ?? 0 },
                { label: 'H2 Tags', value: result.h2_count ?? 0 },
                { label: 'Paragraphs', value: result.total_paragraphs ?? 0 },
                { label: 'Images', value: result.total_images ?? 0 },
                { label: 'Forms', value: result.total_forms ?? 0 },
                { label: 'Contact Page', value: boolBadge(result.contact_page_exists) },
                { label: 'About Page', value: boolBadge(result.about_page_exists) },
                { label: 'Missing H1', value: boolBadge(result.missing_h1) },
              ].map(({ label, value }) => (
                <div key={label} style={{ textAlign: 'center', padding: 12, background: 'var(--color-surface-raised)', borderRadius: 8 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text-primary)' }}>{value}</div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>{label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Contact info */}
          {(result.emails?.length || result.phone_numbers?.length) ? (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>Contact Information Found</div>
              {result.emails?.length ? (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Emails</div>
                  {result.emails.map((e) => <div key={e} style={{ fontSize: 13, color: 'var(--color-brand)' }}>{e}</div>)}
                </div>
              ) : null}
              {result.phone_numbers?.length ? (
                <div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 4 }}>Phone Numbers</div>
                  {result.phone_numbers.map((p) => <div key={p} style={{ fontSize: 13 }}>{p}</div>)}
                </div>
              ) : null}
            </div>
          ) : null}

          {/* Meta description */}
          {result.meta_description && (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 14 }}>Meta Description</div>
              <p style={{ fontSize: 13, color: 'var(--color-text-secondary)', lineHeight: 1.6, margin: 0 }}>{result.meta_description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
