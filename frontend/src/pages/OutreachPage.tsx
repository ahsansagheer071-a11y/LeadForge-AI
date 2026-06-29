import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { MessageSquare, Search, Loader, Copy, CheckCircle, RefreshCw } from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { outreachApi } from '@/services/apiServices'
import { queryKeys, getErrorMessage } from '@/utils'

interface OutreachResult {
  email_subject: string | null
  cold_email: string | null
  linkedin_message: string | null
  followup_email: string | null
  short_cta: string | null
}

function CopyBlock({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--color-text-secondary)' }}>{label}</div>
        <button className="btn btn-ghost btn-sm" onClick={handleCopy} style={{ gap: 4 }}>
          {copied ? <CheckCircle size={12} color="var(--color-success)" /> : <Copy size={12} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <div style={{ fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap', color: 'var(--color-text-primary)' }}>{value}</div>
    </div>
  )
}

export default function OutreachPage() {
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedName, setSelectedName] = useState('')
  const [result, setResult] = useState<OutreachResult | null>(null)
  const [error, setError] = useState('')

  const { data: leadsData } = useQuery({
    queryKey: queryKeys.leads.list({ name: search, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
    queryFn: () => leadsApi.list({ name: search || undefined, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
  })

  const leads = leadsData?.data?.items ?? []

  const outreachMut = useMutation({
    mutationFn: outreachApi.generate,
    onSuccess: (data) => { setResult(data?.data ?? null); setError('') },
    onError: (e) => setError(getErrorMessage(e)),
  })

  const outreachItems = result ? [
    { label: '📧 Email Subject', value: result.email_subject },
    { label: '✉️ Cold Email Body', value: result.cold_email },
    { label: '💼 LinkedIn Message', value: result.linkedin_message },
    { label: '🔁 Follow-up Email', value: result.followup_email },
    { label: '📣 Call-to-Action', value: result.short_cta },
  ].filter((i) => i.value) as { label: string; value: string }[] : []

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <MessageSquare size={20} color="var(--color-brand)" />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Outreach Generator</h1>
      </div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 28, marginLeft: 30 }}>
        AI-crafted personalised cold emails, LinkedIn messages, and follow-ups
      </p>

      {/* Lead picker */}
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
                <Link to="/discover" className="link-brand">Discover leads →</Link> and complete analysis before generating outreach.
              </div>
            </div>
          ) : leads.map((lead) => (
            <button key={lead.id} onClick={() => { setSelectedId(lead.id); setSelectedName(lead.name) }} style={{
              padding: '8px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'left',
              background: selectedId === lead.id ? 'var(--color-brand-subtle)' : 'transparent',
              border: `1px solid ${selectedId === lead.id ? 'var(--color-brand-border)' : 'transparent'}`,
            }}>
              <span style={{ fontSize: 13, fontWeight: 500, color: selectedId === lead.id ? 'var(--color-brand)' : 'var(--color-text-primary)' }}>
                {lead.name}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 8 }}>{lead.city}, {lead.country}</span>
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" disabled={!selectedId || outreachMut.isPending}
            onClick={() => { if (selectedId) { setResult(null); outreachMut.mutate(selectedId) } }}>
            {outreachMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : <MessageSquare size={14} />}
            {outreachMut.isPending ? 'Generating…' : selectedId ? `Generate for ${selectedName}` : 'Select a lead first'}
          </button>
          {result && (
            <button className="btn btn-secondary" onClick={() => { if (selectedId) outreachMut.mutate(selectedId) }} disabled={outreachMut.isPending}>
              <RefreshCw size={14} /> Regenerate
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="alert-error">{error}</div>
      )}

      {outreachMut.isPending && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 28, height: 28 }} />
          <div style={{ fontWeight: 600, marginBottom: 4 }}>AI is crafting your outreach…</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Writing personalized emails and messages</div>
        </div>
      )}

      {outreachItems.length > 0 && !outreachMut.isPending && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
            ✅ Outreach generated for <strong style={{ color: 'var(--color-text-primary)' }}>{selectedName}</strong> — click any section to copy
          </div>
          {outreachItems.map(({ label, value }) => (
            <CopyBlock key={label} label={label} value={value} />
          ))}
        </div>
      )}
    </div>
  )
}
