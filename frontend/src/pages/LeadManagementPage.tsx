import { useState, useCallback, useMemo } from 'react'
import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Search,
  Filter,
  Download,
  Trash2,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  CheckSquare,
  Square,
  Eye,
  Users,
  SlidersHorizontal,
  X,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { leadsApi } from '@/services/leadsService'
import LeadPreviewDrawer, { statusPillClass, ScoreBadge } from '@/components/LeadPreviewDrawer'
import { queryKeys, formatDate, getErrorMessage } from '@/utils'
import type { LeadResponse, LeadFilters, LeadStatus } from '@/types'
import '@/styles/leads.css'

const STATUSES: LeadStatus[] = ['NEW', 'SCRAPED', 'ANALYZED', 'OUTREACH_READY', 'CONTACTED', 'CLOSED']
const DEFAULT_FILTERS: LeadFilters = { page: 1, limit: 15, sort_by: 'created_at', sort_order: 'desc' }
const PAGE_SIZES = [10, 15, 25, 50] as const

function getPageNumbers(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | 'ellipsis')[] = [1]
  if (current > 3) pages.push('ellipsis')
  for (let p = Math.max(2, current - 1); p <= Math.min(total - 1, current + 1); p++) {
    pages.push(p)
  }
  if (current < total - 2) pages.push('ellipsis')
  if (total > 1) pages.push(total)
  return pages
}

function countActiveFilters(f: LeadFilters): number {
  let n = 0
  if (f.name) n++
  if (f.city) n++
  if (f.country) n++
  if (f.status) n++
  if (f.min_score != null) n++
  if (f.max_score != null) n++
  return n
}

function TableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="lm-table-shell">
      <div className="lm-table-scroll">
        <table className="lm-table">
          <thead>
            <tr>
              <th className="lm-table__check-col" />
              <th className="lm-table__business-col">Business</th>
              <th>Industry</th>
              <th>Location</th>
              <th>Rating</th>
              <th>AI Score</th>
              <th>Status</th>
              <th>Added</th>
              <th style={{ width: 80 }} />
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, i) => (
              <tr key={i} className="lm-skeleton-row">
                <td className="lm-table__check-col"><div className="lm-skeleton" style={{ width: 16, height: 16 }} /></td>
                <td className="lm-table__business-col"><div className="lm-skeleton" style={{ width: '70%' }} /></td>
                <td><div className="lm-skeleton" style={{ width: '60%' }} /></td>
                <td><div className="lm-skeleton" style={{ width: '80%' }} /></td>
                <td><div className="lm-skeleton lm-score-skeleton" /></td>
                <td><div className="lm-skeleton lm-score-skeleton" /></td>
                <td><div className="lm-skeleton" style={{ width: 72, height: 24, borderRadius: 999 }} /></td>
                <td><div className="lm-skeleton" style={{ width: '50%' }} /></td>
                <td><div className="lm-skeleton" style={{ width: 32, height: 32 }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function LeadManagementPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [filters, setFilters] = useState<LeadFilters>(DEFAULT_FILTERS)
  const [filtersOpen, setFiltersOpen] = useState(true)
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [bulkStatusValue, setBulkStatusValue] = useState('')
  const [previewLead, setPreviewLead] = useState<LeadResponse | null>(null)
  const [toast, setToast] = useState<{ msg: string; type: 'success' | 'error' } | null>(null)

  const showToast = (msg: string, type: 'success' | 'error' = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 3500)
  }

  const { data, isLoading, isFetching } = useQuery({
    queryKey: queryKeys.leads.list(filters),
    queryFn: () => leadsApi.list(filters),
    placeholderData: (prev) => prev,
  })

  const leads: LeadResponse[] = data?.data?.items ?? []
  const total = data?.data?.total ?? 0
  const pages = data?.data?.pages ?? 1
  const activeFilterCount = countActiveFilters(filters)

  const detailQueries = useQueries({
    queries: leads.map((lead) => ({
      queryKey: queryKeys.leads.detail(lead.id),
      queryFn: () => leadsApi.get(lead.id),
      staleTime: 1000 * 60 * 5,
      enabled: leads.length > 0 && !isLoading,
    })),
  })

  const scoreByLeadId = useMemo(() => {
    const map: Record<string, number | null> = {}
    leads.forEach((lead, i) => {
      map[lead.id] = detailQueries[i]?.data?.data?.score?.overall_score ?? null
    })
    return map
  }, [leads, detailQueries])

  const bulkDeleteMutation = useMutation({
    mutationFn: leadsApi.bulkDelete,
    onSuccess: (res) => {
      showToast(`Deleted ${res.data?.processed ?? 0} lead(s)`)
      setSelected(new Set())
      setPreviewLead(null)
      qc.invalidateQueries({ queryKey: queryKeys.leads.all })
    },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })

  const bulkStatusMutation = useMutation({
    mutationFn: leadsApi.bulkStatus,
    onSuccess: (res) => {
      showToast(`Updated ${res.data?.processed ?? 0} lead(s)`)
      setSelected(new Set())
      qc.invalidateQueries({ queryKey: queryKeys.leads.all })
    },
    onError: (e) => showToast(getErrorMessage(e), 'error'),
  })

  const setFilter = useCallback((patch: Partial<LeadFilters>) => {
    setFilters((f) => ({ ...f, ...patch, page: patch.page ?? 1 }))
    setSelected(new Set())
  }, [])

  const toggleSelect = (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation()
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const allSelected = leads.length > 0 && leads.every((l) => selected.has(l.id))
  const toggleAll = () => {
    setSelected(allSelected ? new Set() : new Set(leads.map((l) => l.id)))
  }

  const handleBulkDelete = () => {
    if (!selected.size || !confirm(`Delete ${selected.size} lead(s)?`)) return
    bulkDeleteMutation.mutate({ lead_ids: Array.from(selected) })
  }

  const handleBulkStatus = (status: LeadStatus) => {
    if (!selected.size) return
    bulkStatusMutation.mutate({ lead_ids: Array.from(selected), status })
  }

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS)
    setSelected(new Set())
  }

  const pageNumbers = getPageNumbers(filters.page, pages)
  const rangeStart = total === 0 ? 0 : (filters.page - 1) * filters.limit + 1
  const rangeEnd = Math.min(filters.page * filters.limit, total)

  return (
    <div className="page-container lm-root animate-fade-in">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      <header className="lm-header">
        <div>
          <h1 className="lm-header__title">Leads</h1>
          <p className="lm-header__sub">
            <strong>{total.toLocaleString()}</strong> lead{total !== 1 ? 's' : ''} in your pipeline
            {activeFilterCount > 0 && ` · ${activeFilterCount} filter${activeFilterCount !== 1 ? 's' : ''} active`}
          </p>
        </div>
        <div className="lm-header__actions">
          <button type="button" className="btn btn-secondary btn-sm" onClick={() => leadsApi.exportCsv(filters)}>
            <Download size={14} /> Export
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setFiltersOpen((v) => !v)}
          >
            <SlidersHorizontal size={14} />
            Filters
            {activeFilterCount > 0 && (
              <span style={{
                marginLeft: 4, background: 'var(--lm-blue)', color: '#fff',
                borderRadius: 999, padding: '1px 6px', fontSize: 10, fontWeight: 700,
              }}>
                {activeFilterCount}
              </span>
            )}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => qc.invalidateQueries({ queryKey: queryKeys.leads.all })}
            aria-label="Refresh"
          >
            <RefreshCw size={14} />
          </button>
          <button type="button" className="btn btn-primary btn-sm" onClick={() => navigate('/discover')}>
            + Discover
          </button>
        </div>
      </header>

      <div className="lm-search-wrap">
        <Search size={18} className="lm-search-icon" />
        <input
          className="lm-search"
          placeholder="Search businesses by name…"
          value={filters.name ?? ''}
          onChange={(e) => setFilter({ name: e.target.value || undefined })}
        />
      </div>

      <button
        type="button"
        className="btn btn-secondary btn-sm lm-filters-toggle"
        onClick={() => setMobileFiltersOpen((v) => !v)}
      >
        <Filter size={14} /> {mobileFiltersOpen ? 'Hide' : 'Show'} Filters
      </button>

      {(filtersOpen || mobileFiltersOpen) && (
        <div className={`lm-filters ${mobileFiltersOpen ? 'lm-filters--open' : ''}`}>
          <div>
            <label className="label">City</label>
            <input className="input" placeholder="Any city" value={filters.city ?? ''} onChange={(e) => setFilter({ city: e.target.value || undefined })} />
          </div>
          <div>
            <label className="label">Country</label>
            <input className="input" placeholder="Any country" value={filters.country ?? ''} onChange={(e) => setFilter({ country: e.target.value || undefined })} />
          </div>
          <div>
            <label className="label">Status</label>
            <select className="select" value={filters.status ?? ''} onChange={(e) => setFilter({ status: e.target.value || undefined })}>
              <option value="">All statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Min AI Score</label>
            <input className="input" type="number" placeholder="0" min={0} max={100} value={filters.min_score ?? ''} onChange={(e) => setFilter({ min_score: e.target.value ? +e.target.value : undefined })} />
          </div>
          <div>
            <label className="label">Max AI Score</label>
            <input className="input" type="number" placeholder="100" min={0} max={100} value={filters.max_score ?? ''} onChange={(e) => setFilter({ max_score: e.target.value ? +e.target.value : undefined })} />
          </div>
          <div>
            <label className="label">Sort by</label>
            <select
              className="select"
              value={`${filters.sort_by}_${filters.sort_order}`}
              onChange={(e) => {
                const [sort_by, sort_order] = e.target.value.split('_') as [string, 'asc' | 'desc']
                setFilter({ sort_by, sort_order })
              }}
            >
              <option value="created_at_desc">Newest first</option>
              <option value="created_at_asc">Oldest first</option>
              <option value="name_asc">Name A→Z</option>
              <option value="name_desc">Name Z→A</option>
              <option value="score_desc">Score high→low</option>
              <option value="score_asc">Score low→high</option>
            </select>
          </div>
          <div className="lm-filters__actions">
            {activeFilterCount > 0 && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={resetFilters}>
                <X size={13} /> Clear all
              </button>
            )}
          </div>
        </div>
      )}

      {isLoading ? (
        <TableSkeleton />
      ) : leads.length === 0 ? (
        <div className="lm-table-shell">
          <div className="lm-empty">
            <div className="lm-empty__icon"><Users size={26} /></div>
            <div className="lm-empty__title">No leads match your criteria</div>
            <div className="lm-empty__desc">
              Adjust your filters or discover new businesses to start building your pipeline.
            </div>
            <button type="button" className="btn btn-primary" onClick={() => navigate('/discover')}>
              Discover Leads
            </button>
          </div>
        </div>
      ) : (
        <div className="lm-table-shell" style={{ opacity: isFetching ? 0.75 : 1 }}>
          <div className="lm-table-scroll">
            <table className="lm-table">
              <thead>
                <tr>
                  <th className="lm-table__check-col">
                    <button type="button" className="lm-icon-btn" onClick={toggleAll} aria-label="Select all">
                      {allSelected ? <CheckSquare size={16} color="var(--lm-blue)" /> : <Square size={16} />}
                    </button>
                  </th>
                  <th className="lm-table__business-col">Business</th>
                  <th>Industry</th>
                  <th>Location</th>
                  <th>Rating</th>
                  <th>AI Score</th>
                  <th>Status</th>
                  <th>Added</th>
                  <th style={{ width: 80 }} />
                </tr>
              </thead>
              <tbody>
                {leads.map((lead, rowIdx) => {
                  const score = scoreByLeadId[lead.id]
                  const scoreLoading = detailQueries[rowIdx]?.isLoading
                  return (
                    <tr
                      key={lead.id}
                      onClick={() => setPreviewLead(lead)}
                      className={previewLead?.id === lead.id ? 'lm-row--active' : undefined}
                    >
                      <td className="lm-table__check-col" onClick={(e) => toggleSelect(lead.id, e)}>
                        {selected.has(lead.id)
                          ? <CheckSquare size={16} color="var(--lm-blue)" />
                          : <Square size={16} color="var(--color-text-muted)" />}
                      </td>
                      <td className="lm-table__business-col">
                        <div className="lm-business-name">{lead.name}</div>
                        {lead.website && (
                          <a
                            href={lead.website}
                            target="_blank"
                            rel="noreferrer"
                            className="lm-website-link"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {lead.website.replace(/^https?:\/\//, '')}
                          </a>
                        )}
                      </td>
                      <td>{lead.industry}</td>
                      <td>{lead.city}, {lead.country}</td>
                      <td>
                        {lead.rating != null ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
                            ⭐ {lead.rating.toFixed(1)}
                            {lead.reviews_count != null && (
                              <span style={{ color: 'var(--color-text-muted)' }}>({lead.reviews_count})</span>
                            )}
                          </span>
                        ) : (
                          <span className="lm-score--none">—</span>
                        )}
                      </td>
                      <td>
                        {scoreLoading ? (
                          <div className="lm-skeleton lm-score-skeleton" />
                        ) : (
                          <ScoreBadge score={score} />
                        )}
                      </td>
                      <td>
                        <span className={statusPillClass(lead.status)}>
                          {lead.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>{formatDate(lead.created_at)}</td>
                      <td>
                        <div className="lm-row-actions">
                          <button
                            type="button"
                            className="lm-icon-btn"
                            title="Quick preview"
                            onClick={(e) => { e.stopPropagation(); setPreviewLead(lead) }}
                          >
                            <Eye size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!isLoading && total > 0 && (
        <footer className="lm-pagination">
          <div className="lm-pagination__info">
            Showing <strong>{rangeStart}–{rangeEnd}</strong> of <strong>{total.toLocaleString()}</strong> leads
          </div>
          <div className="lm-pagination__controls">
            <button
              type="button"
              className="lm-page-btn"
              disabled={filters.page <= 1}
              onClick={() => setFilter({ page: filters.page - 1 })}
            >
              <ChevronLeft size={14} /> Prev
            </button>
            {pageNumbers.map((p, i) =>
              p === 'ellipsis' ? (
                <span key={`e-${i}`} style={{ padding: '0 4px', color: 'var(--color-text-muted)' }}>…</span>
              ) : (
                <button
                  key={p}
                  type="button"
                  className={`lm-page-btn ${filters.page === p ? 'lm-page-btn--active' : ''}`}
                  onClick={() => setFilter({ page: p })}
                >
                  {p}
                </button>
              )
            )}
            <button
              type="button"
              className="lm-page-btn"
              disabled={filters.page >= pages}
              onClick={() => setFilter({ page: filters.page + 1 })}
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
          <div className="lm-per-page">
            <span>Rows</span>
            {PAGE_SIZES.map((n) => (
              <button
                key={n}
                type="button"
                className={filters.limit === n ? 'lm-per-page--active' : ''}
                onClick={() => setFilter({ limit: n })}
              >
                {n}
              </button>
            ))}
          </div>
        </footer>
      )}

      <div className={`lm-bulk-bar ${selected.size > 0 ? 'lm-bulk-bar--visible' : ''}`}>
        <span className="lm-bulk-bar__count">{selected.size} selected</span>
        <select
          className="select"
          style={{ width: 160, height: 36 }}
          value={bulkStatusValue}
          onChange={(e) => {
            const val = e.target.value as LeadStatus | ''
            if (val) {
              handleBulkStatus(val)
              setBulkStatusValue('')
            }
          }}
        >
          <option value="">Change status…</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s.replace('_', ' ')}</option>
          ))}
        </select>
        <button
          type="button"
          className="btn btn-danger btn-sm"
          onClick={handleBulkDelete}
          disabled={bulkDeleteMutation.isPending}
        >
          <Trash2 size={14} /> Delete
        </button>
        <button type="button" className="btn btn-ghost btn-sm" onClick={() => setSelected(new Set())}>
          Clear
        </button>
      </div>

      <LeadPreviewDrawer
        lead={previewLead}
        open={!!previewLead}
        onClose={() => setPreviewLead(null)}
        onOpenFull={(id) => navigate(`/leads/${id}`)}
      />
    </div>
  )
}
