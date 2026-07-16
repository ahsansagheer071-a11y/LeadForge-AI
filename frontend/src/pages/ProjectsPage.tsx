import { useState } from 'react';
import { Search, Globe, MapPin, ArrowRight, ChevronLeft, ChevronRight, X, Filter, Star, Plus, AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Input, Label } from '@/components/Input';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { projectsService, leadDiscoveryService } from '@/services/services';
import { getApiErrorMessage } from '@/services/apiClient';
import { formatRelative, scoreTier, cn } from '@/utils';
import type { LeadDiscoveryRequest } from '@/types';
import { toast } from 'sonner';

/* ── Constants ───────────────────────────────────────────────── */
const STATUS_OPTIONS = ['NEW', 'SCRAPED', 'ANALYZED', 'OUTREACH_READY', 'CONTACTED', 'CLOSED', 'draft', 'archived', 'failed'] as const;

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info',
  SCRAPED: 'brand',
  ANALYZED: 'warning',
  OUTREACH_READY: 'success',
  CONTACTED: 'brand',
  CLOSED: 'success',
  draft: 'muted',
  queued: 'info',
  generating: 'info',
  previewing: 'warning',
  deployed: 'success',
  failed: 'danger',
  archived: 'neutral',
};

/* ── Filter state ────────────────────────────────────────────── */
interface Filters {
  search: string;
  status: string;
  minScore: string;
}

const defaultFilters: Filters = { search: '', status: '', minScore: '' };

/* ── Score cell ──────────────────────────────────────────────── */
function ScoreCell({ score }: { score: number | null | undefined }) {
  if (score == null) {
    return <span className="text-[12px] text-[var(--color-text-muted)]">&mdash;</span>;
  }
  const tier = scoreTier(score);
  const toneClass = tier === 'hot'
    ? 'text-[var(--color-success)]'
    : tier === 'warm'
      ? 'text-[var(--color-warning)]'
      : 'text-[var(--color-text-muted)]';
  return (
    <span className={cn('text-[13px] font-semibold tabular-nums', toneClass)}>
      {Math.round(score)}
    </span>
  );
}

/* ── Status badge ────────────────────────────────────────────── */
function StatusBadge({ status }: { status: string }) {
  return (
    <Badge tone={statusTone[status] ?? 'muted'} className="text-[11px]">
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}

/* ── Pipeline dots ───────────────────────────────────────────── */
function PipelineDots({ status }: { status: string }) {
  const stages = ['NEW', 'SCRAPED', 'ANALYZED', 'OUTREACH_READY', 'CONTACTED', 'CLOSED'];
  const idx = stages.indexOf(status);
  if (idx === -1) return null;
  return (
    <div className="flex items-center gap-0.5">
      {stages.map((_, i) => (
        <div
          key={i}
          className={cn(
            'size-1.5 rounded-full transition-colors duration-150',
            i <= idx ? 'bg-[var(--color-brand)]' : 'bg-[var(--color-border)]',
          )}
        />
      ))}
    </div>
  );
}

/* ── Initials helper ─────────────────────────────────────────── */
function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?';
}

/* ── Table skeleton ──────────────────────────────────────────── */
function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-px">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3.5">
          <Skeleton variant="circular" width={32} height={32} />
          <div className="flex-1 grid grid-cols-6 gap-4">
            {Array.from({ length: 6 }).map((_, j) => (
              <Skeleton key={j} variant="text" width="100%" height={12} delay={j * 20} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Card skeleton (mobile) ──────────────────────────────────── */
function CardSkeletonMobile({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] p-4 space-y-3">
          <div className="flex items-center gap-3">
            <Skeleton variant="circular" width={36} height={36} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="55%" height={14} />
              <Skeleton variant="text" width="35%" height={11} />
            </div>
            <Skeleton variant="text" width={28} height={14} />
          </div>
          <div className="flex items-center gap-3">
            <Skeleton variant="rounded" width={60} height={20} />
            <Skeleton variant="text" width={48} height={11} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN PAGE
   ══════════════════════════════════════════════════════════════ */
export function ProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const pageSize = 15;

  const { data: paginated, isLoading, error, refetch } = useQuery({
    queryKey: ['projects', page],
    queryFn: () => projectsService.list(page, pageSize),
  });

  const projects = paginated?.items ?? [];
  const totalItems = paginated?.total ?? 0;
  const totalPages = paginated?.pages ?? 1;

  /* ── Client-side filtering ──────────────────────────────── */
  const filtered = projects.filter((p) => {
    const q = filters.search.toLowerCase();
    if (q && !p.name.toLowerCase().includes(q) && !p.industry?.toLowerCase().includes(q) && !p.city?.toLowerCase().includes(q)) return false;
    if (filters.status && p.status !== filters.status) return false;
    if (filters.minScore && (p.rating == null || p.rating < Number(filters.minScore))) return false;
    return true;
  });

  const hasActiveFilters = filters.search || filters.status || filters.minScore;

  /* ── Discovery mutation ──────────────────────────────────── */
  const discoveryMutation = useMutation({
    mutationFn: (data: LeadDiscoveryRequest) => leadDiscoveryService.discover(data),
    onSuccess: (data) => {
      toast.success(`Discovered ${data.created} lead(s), skipped ${data.skipped_duplicates} duplicate(s).`);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (err) => {
      const apiErr = err as { category?: string; message?: string };
      if (apiErr?.category === 'provider' || (apiErr?.message && apiErr.message.includes('SerpAPI'))) {
        toast.error('Lead discovery is temporarily unavailable. Check the discovery provider configuration and try again.');
      } else {
        toast.error(getApiErrorMessage(err, 'Discovery failed'));
      }
    },
  });

  const [discoveryForm, setDiscoveryForm] = useState<LeadDiscoveryRequest>({
    business_type: '',
    city: '',
    country: '',
  });

  const handleDiscoveryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDiscoveryForm(prev => ({ ...prev, [name]: value }));
  };

  const handleDiscoverySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!discoveryForm.business_type || !discoveryForm.city || !discoveryForm.country) {
      toast.error('Please fill in all discovery fields');
      return;
    }
    discoveryMutation.mutate(discoveryForm);
  };

  const handlePageChange = (p: number) => {
    setPage(p);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const clearFilters = () => setFilters(defaultFilters);

  /* ── Empty state (no leads at all) ────────────────────────── */
  if (!isLoading && !error && totalItems === 0) {
    return (
      <div className="space-y-6 lf-fade-in">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <p className="text-[13px] text-[var(--color-text-muted)] font-mono mb-1">Lead Pipeline</p>
            <h1 className="lf-display text-[var(--color-text)]">Leads</h1>
          </div>
        </div>

        <PremiumCard innerClassName="p-12 text-center max-w-xl mx-auto">
          <div className="size-14 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center mx-auto mb-5">
            <Plus className="size-6 text-[var(--color-brand)]" />
          </div>
          <h2 className="text-[18px] font-bold text-[var(--color-text)] mb-2">No leads yet</h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto leading-relaxed">
            Discover businesses, run AI audits, generate websites, and convert leads — all from one workspace.
          </p>
          <Button
            variant="primary"
            size="md"
            onClick={() => document.getElementById('discovery-section')?.scrollIntoView({ behavior: 'smooth' })}
            leftIcon={<Search size={15} />}
          >
            Discover Leads
          </Button>
        </PremiumCard>

        <div id="discovery-section">
          <DiscoveryPanel
            discoveryForm={discoveryForm}
            handleDiscoveryChange={handleDiscoveryChange}
            handleDiscoverySubmit={handleDiscoverySubmit}
            discoveryMutation={discoveryMutation}
          />
        </div>
      </div>
    );
  }

  /* ── Error state ──────────────────────────────────────────── */
  if (error && !isLoading && totalItems === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full lf-fade-in">
        <PremiumCard innerClassName="p-10 text-center max-w-lg">
          <div className="size-14 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5">
            <AlertTriangle className="size-6 text-red-500" />
          </div>
          <h2 className="text-[18px] font-bold text-[var(--color-text)] mb-2">Unable to load leads</h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 max-w-sm mx-auto">
            Something went wrong while fetching your leads. Check your connection and try again.
          </p>
          <Button variant="outline" onClick={() => refetch()}>Retry</Button>
        </PremiumCard>
      </div>
    );
  }

  /* ═════════════════════════════════════════════════════════════
     MAIN RENDER
     ════════════════════════════════════════════════════════════ */
  return (
    <div className="space-y-6 lf-fade-in">
      {/* ── Page header ──────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="text-[13px] text-[var(--color-text-muted)] font-mono mb-1">Lead Pipeline</p>
          <h1 className="lf-display text-[var(--color-text)]">
            Leads
            {!isLoading && totalItems > 0 && (
              <span className="text-[16px] font-normal text-[var(--color-text-muted)] ml-3">{totalItems}</span>
            )}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => document.getElementById('discovery-section')?.scrollIntoView({ behavior: 'smooth' })}
            leftIcon={<Search size={14} />}
          >
            Discover Leads
          </Button>
        </div>
      </div>

      {/* ── Discovery panel ──────────────────────────────────── */}
      <div id="discovery-section">
        <DiscoveryPanel
          discoveryForm={discoveryForm}
          handleDiscoveryChange={handleDiscoveryChange}
          handleDiscoverySubmit={handleDiscoverySubmit}
          discoveryMutation={discoveryMutation}
        />
      </div>

      {/* ── Filter toolbar ───────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-2.5">
        <div className="relative flex-1 min-w-[180px] max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-[var(--color-text-muted)]" />
          <Input
            placeholder="Search leads..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="pl-8 h-8 text-[12px]"
          />
          {filters.search && (
            <button
              onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 size-5 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            >
              <X size={11} />
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Filter size={13} className="text-[var(--color-text-muted)]" />
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="h-8 rounded-[var(--radius-md)] px-2.5 text-[12px] bg-[var(--color-input-bg)] text-[var(--color-text)] border border-[var(--color-input-border)] outline-none focus:border-[var(--color-brand)] transition-colors"
          >
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <Star size={13} className="text-[var(--color-text-muted)]" />
          <select
            value={filters.minScore}
            onChange={(e) => setFilters(prev => ({ ...prev, minScore: e.target.value }))}
            className="h-8 rounded-[var(--radius-md)] px-2.5 text-[12px] bg-[var(--color-input-bg)] text-[var(--color-text)] border border-[var(--color-input-border)] outline-none focus:border-[var(--color-brand)] transition-colors"
          >
            <option value="">Any score</option>
            <option value="80">80+ hot</option>
            <option value="60">60+ warm</option>
            <option value="40">40+ moderate</option>
          </select>
        </div>

        {hasActiveFilters && (
          <Button variant="ghost" size="xs" onClick={clearFilters}>
            <X size={12} /> Clear
          </Button>
        )}

        <div className="ml-auto text-[11px] font-mono text-[var(--color-text-muted)]">
          {!isLoading && (
            <span>{filtered.length} of {totalItems}</span>
          )}
        </div>
      </div>

      {/* ── Desktop table ────────────────────────────────────── */}
      <div className="hidden lg:block">
        {isLoading ? (
          <TableSkeleton rows={6} />
        ) : error ? (
          <PremiumCard innerClassName="p-6 text-center">
            <p className="text-[13px] text-[var(--color-text-secondary)] mb-3">Failed to load leads.</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>Retry</Button>
          </PremiumCard>
        ) : filtered.length === 0 ? (
          <PremiumCard innerClassName="p-10">
            <EmptyState
              title="No leads match your filters"
              message="Try adjusting your search or clear filters to see all leads."
              icon={Search}
              action={hasActiveFilters ? <Button variant="outline" size="sm" onClick={clearFilters}>Clear filters</Button> : undefined}
            />
          </PremiumCard>
        ) : (
          <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface-hover)]">
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)]">Business</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)]">Website</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)]">Location</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)] hidden xl:table-cell">Industry</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)] text-right">Score</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)] hidden xl:table-cell">Pipeline</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)]">Status</th>
                  <th className="py-2.5 px-4 text-[11px] font-medium text-[var(--color-text-muted)] text-right hidden md:table-cell">Activity</th>
                  <th className="py-2.5 px-4 w-10" />
                </tr>
              </thead>
              <tbody>
                {filtered.map((lead) => (
                  <tr
                    key={lead.id}
                    onClick={() => navigate(`/project/${lead.id}`)}
                    className="border-b border-[var(--color-border)] last:border-b-0 transition-colors duration-[var(--anim-fast)] hover:bg-[var(--color-surface-hover)] cursor-pointer group"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="size-8 rounded-[var(--radius-md)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center text-[11px] font-semibold text-[var(--color-brand)] shrink-0">
                          {getInitials(lead.name)}
                        </div>
                        <span className="text-[13px] font-medium text-[var(--color-text)] truncate max-w-[180px] group-hover:text-[var(--color-brand)] transition-colors">
                          {lead.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {lead.website ? (
                        <a
                          href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-[12px] text-[var(--color-brand)] hover:underline inline-flex items-center gap-1 truncate max-w-[160px]"
                        >
                          <Globe size={11} className="shrink-0" />
                          <span className="truncate">{lead.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}</span>
                        </a>
                      ) : (
                        <span className="text-[12px] text-[var(--color-text-muted)]">&mdash;</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-[12px] text-[var(--color-text-secondary)] inline-flex items-center gap-1 truncate max-w-[140px]">
                        <MapPin size={11} className="text-[var(--color-text-muted)] shrink-0" />
                        {lead.city || lead.country
                          ? `${lead.city || ''}${lead.city && lead.country ? ', ' : ''}${lead.country || ''}`
                          : '\u2014'}
                      </span>
                    </td>
                    <td className="py-3 px-4 hidden xl:table-cell">
                      {lead.industry ? (
                        <Badge tone="neutral" className="text-[11px]">{lead.industry}</Badge>
                      ) : (
                        <span className="text-[12px] text-[var(--color-text-muted)]">&mdash;</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <ScoreCell score={lead.rating} />
                    </td>
                    <td className="py-3 px-4 hidden xl:table-cell">
                      <PipelineDots status={lead.status} />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={lead.status} />
                    </td>
                    <td className="py-3 px-4 text-right hidden md:table-cell">
                      <span className="text-[11px] font-mono text-[var(--color-text-muted)]">{formatRelative(lead.updated_at)}</span>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={(e) => { e.stopPropagation(); navigate(`/project/${lead.id}`); }}
                        className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-all duration-[var(--anim-fast)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-brand)]"
                      >
                        <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Mobile cards ─────────────────────────────────────── */}
      <div className="block lg:hidden">
        {isLoading ? (
          <CardSkeletonMobile rows={4} />
        ) : error ? (
          <PremiumCard innerClassName="p-6 text-center">
            <p className="text-[13px] text-[var(--color-text-secondary)] mb-3">Failed to load leads.</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>Retry</Button>
          </PremiumCard>
        ) : filtered.length === 0 ? (
          <PremiumCard innerClassName="p-8">
            <EmptyState
              title="No leads match your filters"
              message="Try adjusting your search or clear filters."
              icon={Search}
              action={hasActiveFilters ? <Button variant="outline" size="sm" onClick={clearFilters}>Clear filters</Button> : undefined}
            />
          </PremiumCard>
        ) : (
          <div className="space-y-2">
            {filtered.map((lead) => (
              <div
                key={lead.id}
                onClick={() => navigate(`/project/${lead.id}`)}
                className="rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] p-4 cursor-pointer transition-colors duration-[var(--anim-fast)] hover:border-[var(--color-border-strong)]"
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="size-9 rounded-[var(--radius-md)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center text-[12px] font-semibold text-[var(--color-brand)] shrink-0">
                      {getInitials(lead.name)}
                    </div>
                    <div className="min-w-0">
                      <p className="text-[14px] font-medium text-[var(--color-text)] truncate">{lead.name}</p>
                      {(lead.city || lead.country) && (
                        <p className="text-[11px] text-[var(--color-text-muted)] truncate">
                          {lead.city || ''}{lead.city && lead.country ? ', ' : ''}{lead.country || ''}
                        </p>
                      )}
                    </div>
                  </div>
                  <ScoreCell score={lead.rating} />
                </div>

                <div className="flex items-center justify-between gap-2 mt-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <StatusBadge status={lead.status} />
                    {lead.industry && (
                      <Badge tone="neutral" className="text-[10px] hidden sm:inline-flex">{lead.industry}</Badge>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-[var(--color-text-muted)] shrink-0">
                    {formatRelative(lead.updated_at)}
                  </span>
                </div>

                {lead.website && (
                  <a
                    href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-[11px] text-[var(--color-brand)] hover:underline inline-flex items-center gap-1 mt-2.5 truncate max-w-full"
                  >
                    <Globe size={10} className="shrink-0" />
                    <span className="truncate">{lead.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}</span>
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Pagination ───────────────────────────────────────── */}
      {totalPages > 1 && !isLoading && !error && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
            Page {page} of {totalPages} &middot; {totalItems} leads
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1}
              className={cn(
                'size-8 rounded-[var(--radius-md)] flex items-center justify-center transition-colors duration-[var(--anim-fast)]',
                page <= 1
                  ? 'text-[var(--color-text-muted)] opacity-40 cursor-not-allowed'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
              )}
            >
              <ChevronLeft size={15} />
            </button>

            {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
              let pageNum: number;
              if (totalPages <= 7) {
                pageNum = i + 1;
              } else if (page <= 4) {
                pageNum = i + 1;
              } else if (page >= totalPages - 3) {
                pageNum = totalPages - 6 + i;
              } else {
                pageNum = page - 3 + i;
              }
              const isActive = pageNum === page;
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={cn(
                    'size-8 rounded-[var(--radius-md)] flex items-center justify-center transition-colors duration-[var(--anim-fast)] text-[12px] font-mono font-medium',
                    isActive
                      ? 'bg-[var(--color-brand)] text-white'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
                  )}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages}
              className={cn(
                'size-8 rounded-[var(--radius-md)] flex items-center justify-center transition-colors duration-[var(--anim-fast)]',
                page >= totalPages
                  ? 'text-[var(--color-text-muted)] opacity-40 cursor-not-allowed'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
              )}
            >
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   DISCOVERY PANEL
   ══════════════════════════════════════════════════════════════ */
function DiscoveryPanel({
  discoveryForm,
  handleDiscoveryChange,
  handleDiscoverySubmit,
  discoveryMutation,
}: {
  discoveryForm: LeadDiscoveryRequest;
  handleDiscoveryChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  handleDiscoverySubmit: (e: React.FormEvent) => void;
  discoveryMutation: { isPending: boolean; mutate: (data: LeadDiscoveryRequest) => void; error: Error | null; data?: { created: number; skipped_duplicates: number } | undefined };
}) {
  return (
    <PremiumCard innerClassName="p-5 lg:p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="size-9 rounded-[var(--radius-lg)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center">
          <Search className="size-4 text-[var(--color-brand)]" />
        </div>
        <div>
          <h2 className="text-[14px] font-semibold text-[var(--color-text)]">Discover Leads</h2>
          <p className="text-[12px] text-[var(--color-text-muted)]">Search Google Maps for businesses to audit and convert</p>
        </div>
      </div>

      <form onSubmit={handleDiscoverySubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <Label htmlFor="business_type" className="mb-1.5 block">Business type</Label>
            <Input
              id="business_type"
              name="business_type"
              value={discoveryForm.business_type}
              onChange={handleDiscoveryChange}
              placeholder="e.g. Dental clinic"
              required
              className="h-9 text-[13px]"
            />
          </div>
          <div>
            <Label htmlFor="city" className="mb-1.5 block">City</Label>
            <Input
              id="city"
              name="city"
              value={discoveryForm.city}
              onChange={handleDiscoveryChange}
              placeholder="e.g. New York"
              required
              className="h-9 text-[13px]"
            />
          </div>
          <div>
            <Label htmlFor="country" className="mb-1.5 block">Country</Label>
            <Input
              id="country"
              name="country"
              value={discoveryForm.country}
              onChange={handleDiscoveryChange}
              placeholder="e.g. USA"
              required
              className="h-9 text-[13px]"
            />
          </div>
          <div className="flex items-end">
            <Button
              type="submit"
              variant="primary"
              size="md"
              fullWidth
              disabled={discoveryMutation.isPending}
              loading={discoveryMutation.isPending}
            >
              {discoveryMutation.isPending ? 'Searching...' : 'Search'}
            </Button>
          </div>
        </div>
      </form>

      {discoveryMutation.isPending && (
        <div className="mt-4 p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center gap-3">
          <div className="size-5 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
          <p className="text-[12px] text-[var(--color-text-secondary)]">
            Searching for {discoveryForm.business_type} in {discoveryForm.city}, {discoveryForm.country}...
          </p>
        </div>
      )}

      {discoveryMutation.data && (
        <div className="mt-4 p-3 rounded-[var(--radius-md)] bg-emerald-500/5 border border-emerald-500/15 flex items-center gap-2.5">
          <div className="size-5 rounded-full bg-emerald-500/10 flex items-center justify-center">
            <span className="text-[10px] text-emerald-600 dark:text-emerald-400">&#10003;</span>
          </div>
          <p className="text-[12px] text-emerald-600 dark:text-emerald-400">
            Discovered {discoveryMutation.data.created} lead(s), skipped {discoveryMutation.data.skipped_duplicates} duplicate(s).
          </p>
        </div>
      )}

      {discoveryMutation.error && (
        <div className="mt-4 p-3 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/15 flex items-center gap-2.5">
          <AlertTriangle size={14} className="text-red-500 shrink-0" />
          <p className="text-[12px] text-red-600 dark:text-red-400">{getApiErrorMessage(discoveryMutation.error, 'Discovery failed')}</p>
        </div>
      )}
    </PremiumCard>
  );
}
