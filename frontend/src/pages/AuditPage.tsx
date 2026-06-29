import { Link } from 'react-router-dom'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Bot, Search, Loader } from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { auditsApi } from '@/services/apiServices'
import { queryKeys, getErrorMessage, scoreColour } from '@/utils'

import type { AuditRunResponse } from '@/types'

export default function AuditPage() {
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [selectedName, setSelectedName] = useState('')
  const [auditResult, setAuditResult] = useState<{
    business_summary: string | null
    strengths: string[] | null
    weaknesses: string[] | null
    marketing_recommendations: string[] | null
    overall_score: number | null
  } | null>(null)
  const [error, setError] = useState('')

  const { data: leadsData } = useQuery({
    queryKey: queryKeys.leads.list({ name: search, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
    queryFn: () => leadsApi.list({ name: search || undefined, limit: 20, page: 1, sort_by: 'created_at', sort_order: 'desc' }),
  })

  const leads = leadsData?.data?.items ?? []

  const auditMut = useMutation({
    mutationFn: auditsApi.run,
    onSuccess: (data) => {
      const payload = data?.data as AuditRunResponse | undefined
      const audit = payload?.audit ?? {}
      const weaknesses = (audit['Top Weaknesses'] as Array<{ title?: string } | string> | undefined) ?? []
      setAuditResult({
        business_summary: (audit['Business Summary'] as string) ?? null,
        strengths: (audit['Top Strengths'] as string[]) ?? null,
        weaknesses: weaknesses.map((w) => (typeof w === 'string' ? w : w.title ?? '')).filter(Boolean),
        marketing_recommendations: (audit['Actionable Recommendations'] as string[]) ?? null,
        overall_score: payload?.score?.overall_score ?? (audit['Website Quality Score'] as number) ?? null,
      })
      setError('')
    },
    onError: (e) => setError(getErrorMessage(e)),
  })

  const SWOT = [
    { key: 'strengths', label: '💪 Strengths', data: auditResult?.strengths },
    { key: 'weaknesses', label: '⚠️ Weaknesses', data: auditResult?.weaknesses },
  ]

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <Bot size={20} color="var(--color-brand)" />
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>AI Website Audit</h1>
      </div>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginBottom: 28, marginLeft: 30 }}>
        Full SWOT analysis and marketing recommendations powered by AI
      </p>

      {/* Lead picker */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>Select a Lead to Audit</div>
        <div style={{ position: 'relative', marginBottom: 12 }}>
          <Search size={13} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input className="input" style={{ paddingLeft: 30 }} placeholder="Search leads…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 12 }}>
          {leads.length === 0 ? (
            <div className="empty-state" style={{ padding: '24px 8px' }}>
              <div className="empty-state-title">No leads yet</div>
              <div className="empty-state-desc">
                <Link to="/discover" className="link-brand">Discover leads →</Link> before running an audit.
              </div>
            </div>
          ) : leads.map((lead) => (
            <button key={lead.id} onClick={() => { setSelectedId(lead.id); setSelectedName(lead.name) }} style={{
              padding: '8px 12px', borderRadius: 8, cursor: 'pointer', textAlign: 'left',
              background: selectedId === lead.id ? 'var(--color-brand-subtle)' : 'transparent',
              border: `1px solid ${selectedId === lead.id ? 'var(--color-brand-border)' : 'transparent'}`,
            }}>
              <span style={{ fontSize: 13, fontWeight: 500, color: selectedId === lead.id ? 'var(--color-brand)' : 'var(--color-text-primary)' }}>{lead.name}</span>
            </button>
          ))}
        </div>
        <button className="btn btn-primary" disabled={!selectedId || auditMut.isPending}
          onClick={() => { if (selectedId) { setAuditResult(null); auditMut.mutate(selectedId) } }}>
          {auditMut.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : <Bot size={14} />}
          {auditMut.isPending ? 'Running AI Audit…' : selectedId ? `Audit ${selectedName}` : 'Select a lead first'}
        </button>
      </div>

      {error && (
        <div className="alert-error">{error}</div>
      )}

      {auditMut.isPending && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 28, height: 28 }} />
          <div style={{ fontWeight: 600, marginBottom: 4 }}>AI is analyzing the website…</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>Generating SWOT analysis and recommendations</div>
        </div>
      )}

      {auditResult && !auditMut.isPending && (
        <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Score */}
          {auditResult.overall_score !== null && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 56, fontWeight: 800, color: scoreColour(auditResult.overall_score), lineHeight: 1 }}>
                  {auditResult.overall_score}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 4 }}>Overall Score</div>
              </div>
              {auditResult.business_summary && (
                <p style={{ flex: 1, fontSize: 13, lineHeight: 1.7, color: 'var(--color-text-secondary)', margin: 0 }}>
                  {auditResult.business_summary}
                </p>
              )}
            </div>
          )}

          {/* SWOT grid */}
          <div className="grid-2">
            {SWOT.map(({ key, label, data }) => data && data.length > 0 && (
              <div key={key} className="card">
                <div style={{ fontWeight: 600, marginBottom: 10, fontSize: 14 }}>{label}</div>
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {data.map((item, i) => (
                    <li key={i} style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginBottom: 6, lineHeight: 1.5 }}>{item}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Recommendations */}
          {auditResult.marketing_recommendations && auditResult.marketing_recommendations.length > 0 && (
            <div className="card">
              <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>📋 Marketing Recommendations</div>
              <ol style={{ margin: 0, paddingLeft: 16 }}>
                {auditResult.marketing_recommendations.map((rec, i) => (
                  <li key={i} style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginBottom: 10, lineHeight: 1.6 }}>{rec}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
