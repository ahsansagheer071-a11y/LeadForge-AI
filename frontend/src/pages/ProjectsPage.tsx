import { useState } from 'react';
import { Search, Globe, MapPin, Phone, Star, ArrowRight, ChevronLeft, ChevronRight, X, Filter, Sparkles, Zap, AlertTriangle } from 'lucide-react';
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

const scoreGlow: Record<string, string> = {
  hot: 'shadow-[0_0_12px_rgba(16,185,129,0.5)] border-emerald-500/40',
  warm: 'shadow-[0_0_12px_rgba(245,158,11,0.4)] border-amber-500/40',
  cold: 'shadow-[0_0_8px_rgba(107,114,128,0.3)] border-gray-500/30',
};

function ScoreBadge({ score }: { score: number | null | undefined }) {
  if (score == null) return <span className="inline-flex items-center justify-center size-7 rounded-md text-[10px] font-bold bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]">&mdash;</span>;
  const tier = scoreTier(score);
  const cls = tier === 'hot' ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30'
    : tier === 'warm' ? 'bg-amber-500/15 text-amber-500 border-amber-500/30'
    : 'bg-gray-500/15 text-gray-500 border-gray-500/30';
  const glow = scoreGlow[tier] ?? '';
  return (
    <span className={`inline-flex items-center justify-center size-7 rounded-md text-[11px] font-bold border ${cls} ${glow}`}>
      {Math.round(score)}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  return <Badge tone={statusTone[status] ?? 'muted'} className="font-mono text-[10px] uppercase tracking-wider">{status.replace(/_/g, ' ')}</Badge>;
}

function PipelineStage({ status }: { status: string }) {
  const stages = ['NEW', 'SCRAPED', 'ANALYZED', 'OUTREACH_READY', 'CONTACTED', 'CLOSED'];
  const idx = stages.indexOf(status);
  if (idx === -1) return null;
  return (
    <div className="flex items-center gap-1">
      {stages.map((s, i) => (
        <div
          key={s}
          className={cn(
            'h-1.5 rounded-full transition-all duration-300',
            i <= idx ? 'bg-[#0ea5e9] shadow-[0_0_6px_rgba(14,165,233,0.4)]' : 'bg-[var(--color-surface-hover)]',
            i === idx ? 'w-4' : 'w-2',
          )}
        />
      ))}
    </div>
  );
}

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?';
}

/* ── Filter state ────────────────────────────────────────────── */
interface Filters {
  search: string;
  status: string;
  minScore: string;
}

const defaultFilters: Filters = { search: '', status: '', minScore: '' };

/* ── Skeleton rows ───────────────────────────────────────────── */
function TableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]/30">
          <Skeleton variant="circular" width={36} height={36} />
          <div className="flex-1 grid grid-cols-7 gap-4">
            {Array.from({ length: 7 }).map((_, j) => (
              <Skeleton key={j} variant="text" width="100%" height={14} delay={j * 30} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function CardSkeletonMobile({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: rows }).map((_, i) => (
        <PremiumCard key={i} innerClassName="p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Skeleton variant="circular" width={40} height={40} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="60%" height={16} />
              <Skeleton variant="text" width="40%" height={12} />
            </div>
            <Skeleton variant="rounded" width={36} height={28} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Skeleton variant="text" width="100%" height={12} />
            <Skeleton variant="text" width="100%" height={12} />
          </div>
          <Skeleton variant="rounded" width="100%" height={8} />
        </PremiumCard>
      ))}
    </div>
  );
}

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
      toast.error(getApiErrorMessage(err, 'Discovery failed'));
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

  const clearFilters = () => {
    setFilters(defaultFilters);
  };

  /* ── Empty state (no leads at all) ────────────────────────── */
  if (!isLoading && !error && totalItems === 0) {
    return (
      <div className="space-y-8 lf-fade-in">
        {/* Hero */}
        <PremiumCard variant="featured" innerClassName="relative overflow-hidden p-10 lg:p-14">
          <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-[rgba(14,165,233,0.06)] blur-[100px] pointer-events-none" />
          <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full bg-[rgba(139,92,246,0.05)] blur-[100px] pointer-events-none" />
          <div className="absolute inset-0 pointer-events-none opacity-[0.02]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px)' }} />
          <div className="relative z-10 text-center max-w-2xl mx-auto">
            <div className="size-20 rounded-full bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/30 flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(14,165,233,0.2)]">
              <Sparkles className="size-8 text-[#0ea5e9]" />
            </div>
            <h1 className="lf-display text-white mb-3">Lead Intelligence</h1>
            <p className="text-[14px] text-[var(--color-text-secondary)] font-mono max-w-lg mx-auto leading-relaxed mb-8">
              Your pipeline is empty. Discover businesses on Google Maps, run AI audits, and convert leads with automated outreach.
            </p>
            <Button variant="neon" size="lg" onClick={() => document.getElementById('discovery-section')?.scrollIntoView({ behavior: 'smooth' })}>
              <Search size={16} /> Initialize Discovery
            </Button>
          </div>
        </PremiumCard>

        {/* Discovery form (always visible) */}
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
        <PremiumCard variant="danger" innerClassName="p-10 text-center max-w-lg">
          <div className="size-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto mb-5">
            <AlertTriangle className="size-7 text-red-400" />
          </div>
          <h2 className="text-[20px] font-bold text-white mb-2">Connection Interrupted</h2>
          <p className="text-[13px] text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
            Unable to load the intelligence database. Verify your connection and try again.
          </p>
          <Button variant="danger" onClick={() => refetch()}>
            Re-establish Link
          </Button>
        </PremiumCard>
      </div>
    );
  }

  return (
    <div className="space-y-8 lf-fade-in">
      {/* ═══════════════════════════════════════════════════════════
         PAGE HERO
      ════════════════════════════════════════════════════════════ */}
      <PremiumCard variant="featured" innerClassName="relative overflow-hidden p-8 lg:p-10">
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-[rgba(14,165,233,0.06)] blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-[rgba(139,92,246,0.05)] blur-[80px] pointer-events-none" />
        <div className="absolute inset-0 pointer-events-none opacity-[0.015]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px)' }} />
        <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.08) 2px, rgba(255,255,255,0.08) 4px)' }} />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <span className="text-[11px] font-mono uppercase tracking-[0.2em] text-[#0ea5e9] flex items-center gap-2">
                <span className="size-1.5 rounded-full bg-[#0ea5e9] shadow-[0_0_6px_#0ea5e9]" />
                Lead Intelligence
              </span>
            </div>
            <h1 className="text-[clamp(2rem,4vw,2.5rem)] font-extrabold tracking-tight text-white mb-2">
              Target <span className="bg-gradient-to-r from-[#0ea5e9] to-[#8b5cf6] bg-clip-text text-transparent">Command Center</span>
            </h1>
            <p className="text-[14px] text-[var(--color-text-secondary)] font-mono max-w-xl leading-relaxed">
              {totalItems > 0
                ? `${totalItems} target${totalItems !== 1 ? 's' : ''} in the network. ${paginated?.items.filter(l => l.status === 'NEW').length ?? 0} new signal${paginated?.items.filter(l => l.status === 'NEW').length !== 1 ? 's' : ''} detected.`
                : 'Awaiting initial target acquisition.'}
            </p>
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <div className="flex flex-col items-end">
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Active Pipeline</span>
              <span className="text-[28px] font-bold text-white leading-none">{isLoading ? <Skeleton variant="text" width={60} height={32} /> : totalItems}</span>
            </div>
            {!isLoading && totalItems > 0 && (
              <Button variant="neon" onClick={() => document.getElementById('discovery-section')?.scrollIntoView({ behavior: 'smooth' })}>
                <Search size={14} /> New Discovery
              </Button>
            )}
          </div>
        </div>
      </PremiumCard>

      {/* ═══════════════════════════════════════════════════════════
         AI LEAD DISCOVERY CONSOLE
      ════════════════════════════════════════════════════════════ */}
      <div id="discovery-section">
        <DiscoveryPanel
          discoveryForm={discoveryForm}
          handleDiscoveryChange={handleDiscoveryChange}
          handleDiscoverySubmit={handleDiscoverySubmit}
          discoveryMutation={discoveryMutation}
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════
         FILTER & SEARCH TOOLBAR
      ════════════════════════════════════════════════════════════ */}
      <div className="sticky top-0 z-20 -mx-4 px-4 py-3 backdrop-blur-xl bg-[rgba(4,8,16,0.85)] border-y border-[var(--color-border)]">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-[var(--color-text-muted)]" />
            <Input
              placeholder="Search by name, industry, or location..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="pl-9 h-9 text-[13px]"
            />
            {filters.search && (
              <button
                onClick={() => setFilters(prev => ({ ...prev, search: '' }))}
                className="absolute right-2 top-1/2 -translate-y-1/2 size-5 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white"
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Filter size={14} className="text-[var(--color-text-muted)]" />
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="h-9 rounded-[var(--radius-md)] px-3 text-[12px] bg-[var(--color-input-bg)] text-[var(--color-text)] border border-[var(--color-input-border)] outline-none focus:border-[var(--color-brand)] font-mono"
            >
              <option value="">All Statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <Star size={14} className="text-[var(--color-text-muted)]" />
            <select
              value={filters.minScore}
              onChange={(e) => setFilters(prev => ({ ...prev, minScore: e.target.value }))}
              className="h-9 rounded-[var(--radius-md)] px-3 text-[12px] bg-[var(--color-input-bg)] text-[var(--color-text)] border border-[var(--color-input-border)] outline-none focus:border-[var(--color-brand)] font-mono"
            >
              <option value="">Any Score</option>
              <option value="80">Hot (80+)</option>
              <option value="60">Warm (60+)</option>
              <option value="40">Moderate (40+)</option>
            </select>
          </div>

          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X size={14} /> Clear
            </Button>
          )}

          <div className="ml-auto text-[11px] font-mono text-[var(--color-text-muted)]">
            {!isLoading && (
              <span>{filtered.length} of {totalItems} target{totalItems !== 1 ? 's' : ''}</span>
            )}
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
         DESKTOP LEAD TABLE
      ════════════════════════════════════════════════════════════ */}
      <div className="hidden lg:block">
        {isLoading ? (
          <TableSkeleton rows={6} />
        ) : error ? (
          <PremiumCard variant="danger" innerClassName="p-6 text-center">
            <p className="text-[13px] text-red-400 mb-4">Failed to load targets. The intelligence feed may be temporarily offline.</p>
            <Button variant="outline" onClick={() => refetch()}>Retry Connection</Button>
          </PremiumCard>
        ) : filtered.length === 0 ? (
          <PremiumCard innerClassName="p-10 text-center">
            <EmptyState
              title="No targets match your filters"
              message="Try adjusting your search or clear filters to see all targets."
              icon={Search}
              action={hasActiveFilters ? <Button variant="outline" onClick={clearFilters}>Clear Filters</Button> : undefined}
            />
          </PremiumCard>
        ) : (
          <PremiumCard innerClassName="p-0 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface-hover)]/30">
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Target</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Industry</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Location</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Website</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Contact</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Score</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Pipeline</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Status</th>
                    <th className="py-3.5 px-4 text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)] font-semibold">Updated</th>
                    <th className="py-3.5 px-4 w-10" />
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((lead) => (
                    <tr
                      key={lead.id}
                      onClick={() => navigate(`/project/${lead.id}`)}
                      className="border-b border-[var(--color-border)]/50 transition-all duration-150 hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_60%,transparent)] cursor-pointer group"
                    >
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-3">
                          <div className="size-9 rounded-lg bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/25 flex items-center justify-center text-[12px] font-bold text-[#0ea5e9] shrink-0 shadow-[0_0_8px_rgba(14,165,233,0.15)]">
                            {getInitials(lead.name)}
                          </div>
                          <span className="text-[13px] font-semibold text-white truncate max-w-[180px] group-hover:text-[#0ea5e9] transition-colors">
                            {lead.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-[12px] text-[var(--color-text-secondary)]">{lead.industry || '—'}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-[12px] text-[var(--color-text-secondary)] flex items-center gap-1.5">
                          <MapPin size={11} className="text-[var(--color-text-muted)] shrink-0" />
                          {lead.city || lead.country ? `${lead.city}${lead.city && lead.country ? ', ' : ''}${lead.country}` : '—'}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {lead.website ? (
                          <a
                            href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-[12px] text-[#0ea5e9] hover:underline flex items-center gap-1.5 truncate max-w-[160px]"
                          >
                            <Globe size={11} className="shrink-0" />
                            <span className="truncate">{lead.website.replace(/^https?:\/\//, '')}</span>
                          </a>
                        ) : <span className="text-[12px] text-[var(--color-text-muted)]">—</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        {lead.phone ? (
                          <a
                            href={`tel:${lead.phone}`}
                            onClick={(e) => e.stopPropagation()}
                            className="text-[12px] text-[var(--color-text-secondary)] flex items-center gap-1.5 hover:text-[#0ea5e9]"
                          >
                            <Phone size={11} className="text-[var(--color-text-muted)] shrink-0" />
                            {lead.phone}
                          </a>
                        ) : <span className="text-[12px] text-[var(--color-text-muted)]">—</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        <ScoreBadge score={lead.rating} />
                      </td>
                      <td className="py-3.5 px-4">
                        <PipelineStage status={lead.status} />
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusPill status={lead.status} />
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="text-[11px] font-mono text-[var(--color-text-muted)]">{formatRelative(lead.updated_at)}</span>
                      </td>
                      <td className="py-3.5 px-4">
                        <button
                          onClick={(e) => { e.stopPropagation(); navigate(`/project/${lead.id}`); }}
                          className="size-8 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] opacity-0 group-hover:opacity-100 transition-all flex items-center justify-center hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)]"
                        >
                          <ArrowRight size={14} className="text-[#0ea5e9]" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </PremiumCard>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
         MOBILE LEAD CARDS
      ════════════════════════════════════════════════════════════ */}
      <div className="block lg:hidden">
        {isLoading ? (
          <CardSkeletonMobile rows={4} />
        ) : error ? (
          <PremiumCard variant="danger" innerClassName="p-6 text-center">
            <p className="text-[13px] text-red-400 mb-4">Failed to load targets.</p>
            <Button variant="outline" onClick={() => refetch()}>Retry</Button>
          </PremiumCard>
        ) : filtered.length === 0 ? (
          <PremiumCard innerClassName="p-8 text-center">
            <EmptyState
              title="No targets match your filters"
              message="Try adjusting your search or clear filters."
              icon={Search}
              action={hasActiveFilters ? <Button variant="outline" onClick={clearFilters}>Clear Filters</Button> : undefined}
            />
          </PremiumCard>
        ) : (
          <div className="space-y-4">
            {filtered.map((lead) => (
              <PremiumCard key={lead.id} innerClassName="p-5">
                <div onClick={() => navigate(`/project/${lead.id}`)} className="cursor-pointer">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="size-10 rounded-lg bg-gradient-to-br from-[#0ea5e9]/20 to-[#8b5cf6]/20 border border-[#0ea5e9]/25 flex items-center justify-center text-[13px] font-bold text-[#0ea5e9] shrink-0">
                        {getInitials(lead.name)}
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-[15px] font-bold text-white truncate">{lead.name}</h3>
                        <p className="text-[11px] font-mono text-[var(--color-text-secondary)] truncate">{lead.industry || lead.city || '—'}</p>
                      </div>
                    </div>
                    <ScoreBadge score={lead.rating} />
                  </div>

                  {lead.website && (
                    <a
                      href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-[12px] text-[#0ea5e9] hover:underline flex items-center gap-1.5 mb-3 truncate"
                    >
                      <Globe size={12} />
                      {lead.website.replace(/^https?:\/\//, '')}
                    </a>
                  )}

                  <div className="flex items-center justify-between mb-3">
                    <StatusPill status={lead.status} />
                    <span className="text-[10px] font-mono text-[var(--color-text-muted)]">{formatRelative(lead.updated_at)}</span>
                  </div>

                  <PipelineStage status={lead.status} />
                </div>
              </PremiumCard>
            ))}
          </div>
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════════
         PAGINATION
      ════════════════════════════════════════════════════════════ */}
      {totalPages > 1 && !isLoading && !error && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <span className="text-[11px] font-mono text-[var(--color-text-muted)]">
            Showing page {page} of {totalPages} &middot; {totalItems} total target{totalItems !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1}
              className={cn(
                'size-9 rounded-[var(--radius-md)] flex items-center justify-center transition-all text-[12px]',
                page <= 1
                  ? 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] opacity-40 cursor-not-allowed'
                  : 'bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] hover:text-[#0ea5e9]',
              )}
            >
              <ChevronLeft size={16} />
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
                    'size-9 rounded-[var(--radius-md)] flex items-center justify-center transition-all text-[12px] font-mono font-semibold',
                    isActive
                      ? 'bg-gradient-to-br from-[#0ea5e9] to-[#2563eb] text-white shadow-[0_0_12px_rgba(14,165,233,0.4)]'
                      : 'bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] hover:text-[#0ea5e9]',
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
                'size-9 rounded-[var(--radius-md)] flex items-center justify-center transition-all text-[12px]',
                page >= totalPages
                  ? 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] opacity-40 cursor-not-allowed'
                  : 'bg-[var(--color-surface-hover)] text-[var(--color-text-secondary)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] hover:text-[#0ea5e9]',
              )}
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Discovery Panel Sub-component ──────────────────────────── */
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
    <PremiumCard variant="featured" innerClassName="relative overflow-hidden p-6 lg:p-8">
      {/* Rotating RGB background accent */}
      <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-[rgba(14,165,233,0.04)] blur-[60px] pointer-events-none animate-[lf-orbit_8s_linear_infinite]" />
      <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full bg-[rgba(139,92,246,0.04)] blur-[60px] pointer-events-none animate-[lf-orbit_12s_linear_infinite_reverse]" />

      <div className="relative z-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="size-11 rounded-[14px] bg-gradient-to-br from-[#0ea5e9] to-[#8b5cf6] flex items-center justify-center shadow-[0_0_20px_rgba(14,165,233,0.35)]">
            <Search className="text-white size-5" />
          </div>
          <div>
            <h2 className="text-[16px] font-bold text-white uppercase tracking-wider font-mono">AI Lead Discovery Console</h2>
            <p className="text-[12px] text-[var(--color-text-secondary)] font-mono">Configure scan parameters to locate high-value targets on Google Maps</p>
          </div>
        </div>

        <form onSubmit={handleDiscoverySubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-1">
              <Label htmlFor="business_type" className="text-[11px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">Business Vertical</Label>
              <Input
                id="business_type"
                name="business_type"
                value={discoveryForm.business_type}
                onChange={handleDiscoveryChange}
                placeholder="e.g. Cyber Security, Healthcare"
                required
                className="bg-[#0f172a] border-slate-700 h-11 text-[13px]"
              />
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="city" className="text-[11px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">City / Region</Label>
              <Input
                id="city"
                name="city"
                value={discoveryForm.city}
                onChange={handleDiscoveryChange}
                placeholder="e.g. New York"
                required
                className="bg-[#0f172a] border-slate-700 h-11 text-[13px]"
              />
            </div>
            <div className="md:col-span-1">
              <Label htmlFor="country" className="text-[11px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">Territory</Label>
              <Input
                id="country"
                name="country"
                value={discoveryForm.country}
                onChange={handleDiscoveryChange}
                placeholder="e.g. USA"
                required
                className="bg-[#0f172a] border-slate-700 h-11 text-[13px]"
              />
            </div>
            <div className="md:col-span-1 flex items-end">
              <Button
                type="submit"
                variant="neon"
                size="lg"
                fullWidth
                disabled={discoveryMutation.isPending}
                loading={discoveryMutation.isPending}
                leftIcon={discoveryMutation.isPending ? undefined : <Zap size={15} />}
              >
                {discoveryMutation.isPending ? 'Scanning...' : 'Execute Scan'}
              </Button>
            </div>
          </div>
        </form>

        {/* Loading state */}
        {discoveryMutation.isPending && (
          <div className="mt-6 p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center gap-4">
            <div className="relative size-8">
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#0ea5e9] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '1s' }} />
              <div className="absolute inset-1 rounded-full border border-transparent border-b-[#06b6d4] border-l-[#06b6d4] animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
            </div>
            <div>
              <p className="text-[13px] font-semibold text-white">Scan in progress</p>
              <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Searching Google Maps for {discoveryForm.business_type} in {discoveryForm.city}, {discoveryForm.country}...</p>
            </div>
          </div>
        )}

        {/* Success state */}
        {discoveryMutation.data && (
          <div className="mt-6 p-4 rounded-[var(--radius-md)] bg-emerald-500/5 border border-emerald-500/20 flex items-center gap-3">
            <div className="size-8 rounded-full bg-emerald-500/15 flex items-center justify-center">
              <Sparkles size={16} className="text-emerald-400" />
            </div>
            <p className="text-[13px] text-emerald-400 font-semibold">
              Discovered {discoveryMutation.data.created} lead(s), skipped {discoveryMutation.data.skipped_duplicates} duplicate(s).
            </p>
          </div>
        )}

        {/* Error state */}
        {discoveryMutation.error && (
          <div className="mt-6 p-4 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/20 flex items-center gap-3">
            <AlertTriangle size={16} className="text-red-400 shrink-0" />
            <p className="text-[13px] text-red-400">{getApiErrorMessage(discoveryMutation.error, 'Discovery failed')}</p>
          </div>
        )}
      </div>
    </PremiumCard>
  );
}
