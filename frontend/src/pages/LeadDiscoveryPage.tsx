import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Search, MapPin, Building2, Loader, CheckCircle, AlertCircle, Zap } from 'lucide-react'
import { leadsApi } from '@/services/leadsService'
import { getErrorMessage, queryKeys, statusBadgeClass } from '@/utils'
import type { LeadStatus } from '@/types'

export default function LeadDiscoveryPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [businessType, setBusinessType] = useState('')
  const [city, setCity] = useState('')
  const [country, setCountry] = useState('')
  const [result, setResult] = useState<{ created: number; skipped_duplicates: number; leads: Array<{ id: string; name: string; city: string; country: string; industry: string; status: LeadStatus; website: string | null; phone: string | null }> } | null>(null)

  const mutation = useMutation({
    mutationFn: leadsApi.discover,
    onSuccess: (data) => {
      if (data.data) setResult(data.data as typeof result)
      qc.invalidateQueries({ queryKey: queryKeys.leads.all })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!businessType.trim() || !city.trim() || !country.trim()) return
    setResult(null)
    mutation.mutate({ business_type: businessType.trim(), city: city.trim(), country: country.trim() })
  }

  const presets = [
    { label: 'Restaurants', icon: '🍽️' },
    { label: 'Dentists', icon: '🦷' },
    { label: 'Gyms', icon: '💪' },
    { label: 'Law Firms', icon: '⚖️' },
    { label: 'Real Estate', icon: '🏠' },
    { label: 'Marketing Agencies', icon: '📣' },
  ]

  return (
    <div className="page-container animate-fade-in" style={{ maxWidth: 900 }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <div style={{ width: 34, height: 34, borderRadius: 8, background: 'var(--color-brand-subtle)', border: '1px solid var(--color-brand-border)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Zap size={16} color="var(--color-brand)" />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Lead Discovery</h1>
        </div>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 13, marginLeft: 44 }}>
          Search Google Maps via SerpAPI to find and import real business leads
        </p>
      </div>

      {/* Form */}
      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={handleSubmit}>
          <div className="discover-form-grid">
            <div>
              <label className="label">Business Type</label>
              <div style={{ position: 'relative' }}>
                <Building2 size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
                <input className="input" style={{ paddingLeft: 32 }} placeholder="e.g. Restaurant" value={businessType} onChange={(e) => setBusinessType(e.target.value)} required />
              </div>
            </div>
            <div>
              <label className="label">City</label>
              <div style={{ position: 'relative' }}>
                <MapPin size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
                <input className="input" style={{ paddingLeft: 32 }} placeholder="e.g. New York" value={city} onChange={(e) => setCity(e.target.value)} required />
              </div>
            </div>
            <div>
              <label className="label">Country</label>
              <div style={{ position: 'relative' }}>
                <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
                <input className="input" style={{ paddingLeft: 32 }} placeholder="e.g. United States" value={country} onChange={(e) => setCountry(e.target.value)} required />
              </div>
            </div>
            <button className="btn btn-primary" type="submit" disabled={mutation.isPending} style={{ height: 36 }}>
              {mutation.isPending ? <Loader size={14} style={{ animation: 'spin 0.6s linear infinite' }} /> : <Search size={14} />}
              {mutation.isPending ? 'Searching…' : 'Search'}
            </button>
          </div>
        </form>

        {/* Quick presets */}
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>Quick presets</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {presets.map((p) => (
              <button key={p.label} className="btn btn-secondary btn-sm" onClick={() => setBusinessType(p.label)}>
                {p.icon} {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Error */}
      {mutation.isError && (
        <div className="alert-error">
          <AlertCircle size={15} style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{getErrorMessage(mutation.error)}</span>
        </div>
      )}

      {/* Loading state */}
      {mutation.isPending && (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <div className="spinner" style={{ margin: '0 auto 16px', width: 28, height: 28 }} />
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Searching Google Maps…</div>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>This may take 10–20 seconds</div>
        </div>
      )}

      {/* Results */}
      {result && !mutation.isPending && (
        <div className="animate-fade-in">
          {/* Summary */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <div style={{ flex: 1, background: 'var(--color-success-subtle)', border: '1px solid #22c55e20', borderRadius: 10, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <CheckCircle size={18} color="var(--color-success)" />
              <div>
                <div style={{ fontWeight: 700, fontSize: 20, color: 'var(--color-success)' }}>{result.created}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>New leads created</div>
              </div>
            </div>
            <div style={{ flex: 1, background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 10, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 20 }}>{result.skipped_duplicates}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Duplicates skipped</div>
              </div>
            </div>
            <div style={{ flex: 1, background: 'var(--color-brand-subtle)', border: '1px solid var(--color-brand-border)', borderRadius: 10, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 10 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 20, color: 'var(--color-brand)' }}>{result.leads.length}</div>
                <div style={{ fontSize: 12, color: 'var(--color-text-secondary)' }}>Total returned</div>
              </div>
            </div>
          </div>

          {/* Leads grid */}
          {result.leads.length > 0 && (
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--color-border)', fontWeight: 600, fontSize: 14 }}>
                Discovered Leads
              </div>
              <div className="table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
                <table>
                  <thead>
                    <tr>
                      <th>Business</th>
                      <th>Industry</th>
                      <th>Location</th>
                      <th>Phone</th>
                      <th>Website</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.leads.map((lead) => (
                      <tr key={lead.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/leads/${lead.id}`)}>
                        <td style={{ fontWeight: 500, color: 'var(--color-text-primary)' }}>{lead.name}</td>
                        <td>{lead.industry}</td>
                        <td>{lead.city}, {lead.country}</td>
                        <td>{lead.phone ?? '—'}</td>
                        <td>
                          {lead.website
                            ? <a href={lead.website} target="_blank" rel="noreferrer" style={{ color: 'var(--color-brand)', fontSize: 12 }} onClick={(e) => e.stopPropagation()}>Visit ↗</a>
                            : '—'}
                        </td>
                        <td><span className={statusBadgeClass(lead.status)}>{lead.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
