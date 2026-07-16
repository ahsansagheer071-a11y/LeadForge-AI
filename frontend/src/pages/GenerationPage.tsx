import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, AlertTriangle, Camera, Search, Shield, Zap, Eye, Download, ExternalLink, Globe } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { projectsService, generationService } from '@/services/services';
import { usePreviewStore } from '@/store';
import { useGenerationJob } from '@/hooks/useGenerationJob';
import { cn } from '@/utils';
import { toast } from 'sonner';

/* ── Constants ───────────────────────────────────────────────── */
const statusBadgeTone = (status: string): 'success' | 'info' | 'brand' | 'muted' => {
  if (status.includes('READY')) return 'success';
  if (status.includes('ANALYZED') || status.includes('SCORED')) return 'info';
  if (status.includes('SCRAPED') || status.includes('DISCOVERED') || status.includes('NEW')) return 'brand';
  return 'muted';
};

interface Prereq {
  id: string;
  label: string;
  icon: typeof Camera;
  check: (lead: { screenshot?: unknown; audit?: unknown; score?: unknown } | null) => boolean;
}

const PREREQS: Prereq[] = [
  { id: 'screenshot', label: 'Screenshot captured', icon: Camera, check: (l) => !!l?.screenshot },
  { id: 'analysis', label: 'Website analyzed', icon: Search, check: () => true },
  { id: 'audit', label: 'Audit complete', icon: Shield, check: (l) => !!l?.audit && !!l?.score },
];

const PROGRESS_LABELS: Record<string, string> = {
  Queued: 'Queued \u2014 waiting to start\u2026',
  'Loading lead data': 'Loading lead data\u2026',
  'Crawling website': 'Crawling website (this may take 30\u201360 s)\u2026',
  'Crawling website (fresh)': 'Crawling website \u2014 fresh scan\u2026',
  'Building markdown context': 'Building AI context from site data\u2026',
  'Generating HTML with AI': 'Generating HTML with AI (this may take 60\u2013120 s)\u2026',
  'Saving result': 'Saving generated website\u2026',
  Complete: 'Complete!',
};

function friendlyProgress(raw: string): string {
  return PROGRESS_LABELS[raw] ?? raw;
}

/* ═══════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════ */
export function GenerationPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [selectedId, setSelectedId] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const { data: page, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: () => projectsService.list(1, 50),
  });

  const leads = page?.items ?? [];
  const filteredLeads = (() => {
    if (!searchQuery.trim()) return leads;
    const q = searchQuery.toLowerCase();
    return leads.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.industry.toLowerCase().includes(q) ||
        (l.website && l.website.toLowerCase().includes(q)),
    );
  })();

  const selectedLead = leads.find((l) => l.id === selectedId) ?? null;

  const { data: leadDetail } = useQuery({
    queryKey: ['lead', selectedId],
    queryFn: () => projectsService.getById(selectedId),
    enabled: !!selectedId,
  });

  const { data: existingWebsite } = useQuery({
    queryKey: ['generated-website-latest', selectedId],
    queryFn: () => generationService.getLatestByLeadId(selectedId),
    enabled: !!selectedId,
    staleTime: 30_000,
    retry: false,
  });

  const {
    jobResult,
    jobError,
    isRunning,
    isSuccess,
    isError,
    generate,
    reset,
  } = useGenerationJob({
    leadId: selectedId,
    onSuccess: (websiteId, html) => {
      if (html) setHtmlContent(html);
      queryClient.invalidateQueries({ queryKey: ['lead', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['generated-website-latest', selectedId] });
      toast.success('Website generated successfully');
    },
    onError: (msg) => { toast.error(msg); },
  });

  const handleGenerate = () => generate();
  const handleReset = () => reset();
  const prereqsMet = PREREQS.every((p) => p.check(leadDetail ?? null));

  /* ── Loading ──────────────────────────────────────────────── */
  if (isLoading && leads.length === 0) {
    return (
      <div className="space-y-5 lf-fade-in">
        <div className="h-8"><Skeleton variant="text" width={200} height={16} /></div>
        <div className="h-10"><Skeleton variant="text" width={300} height={24} /></div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} variant="rounded" width="100%" height={200} delay={i * 60} />
            ))}
          </div>
          <div className="space-y-4">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} variant="rounded" width="100%" height={160} delay={i * 60} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Back nav ──────────────────────────────────────────── */}
      <button
        onClick={() => navigate(selectedId ? `/project/${selectedId}` : '/projects')}
        className="inline-flex items-center gap-1.5 text-[12px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        <ArrowLeft size={14} /> {selectedId ? 'Lead Workspace' : 'Leads'}
      </button>

      {/* ── Page header (Stitch style) ────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Redesigns</h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">
            {selectedLead
              ? `Generating website redesign for ${selectedLead.name}`
              : 'Generate premium website redesigns from lead data'}
          </p>
        </div>
        {isSuccess && jobResult?.website_id && (
          <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${jobResult.website_id}`)} rightIcon={<Eye size={13} />}>
            Open Preview
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* ═══════════════════════════════════════════════════════
           MAIN COLUMN
           ══════════════════════════════════════════════════════ */}
        <div className="lg:col-span-2 space-y-5">
          {/* ── Lead selector (Attio-style dense list) ───────── */}
          <Panel title="Source">
            {/* Search */}
            <div className="relative mb-3">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search leads..."
                className="w-full h-8 pl-8 pr-3 text-[12px] bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-[var(--radius-md)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-brand-border)] transition-colors"
              />
            </div>

            {filteredLeads.length > 0 ? (
              <div className="space-y-0.5 max-h-[320px] overflow-y-auto lf-thin-scroll">
                {filteredLeads.map((lead) => (
                  <button
                    key={lead.id}
                    onClick={() => { setSelectedId(lead.id); handleReset(); }}
                    className={cn(
                      'w-full text-left px-3 py-2.5 rounded-[var(--radius-md)] transition-colors duration-[var(--anim-fast)] border group',
                      selectedId === lead.id
                        ? 'bg-[var(--color-brand-subtle)] border-[var(--color-brand-border)]'
                        : 'bg-transparent border-transparent hover:bg-[var(--color-surface-hover)] hover:border-[var(--color-border)]',
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className={cn('text-[13px] font-medium truncate', selectedId === lead.id ? 'text-[var(--color-text)]' : 'text-[var(--color-text-secondary)]')}>
                        {lead.name}
                      </span>
                      <Badge tone={statusBadgeTone(lead.status)} className="text-[10px] shrink-0">{lead.status.replace(/_/g, ' ')}</Badge>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      {lead.website && <span className="text-[11px] text-[var(--color-text-muted)] truncate flex items-center gap-1"><Globe size={10} />{lead.website.replace(/^https?:\/\//, '')}</span>}
                      {lead.rating != null && <span className="text-[11px] text-[var(--color-text-muted)] tabular-nums shrink-0">{lead.rating.toFixed(1)}</span>}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title="No leads available" message="Discover and process leads first." className="py-8" />
            )}
          </Panel>

          {/* ── Direction / prerequisites (when lead selected) ── */}
          {selectedId && (
            <Panel title="Direction">
              <div className="space-y-4">
                {/* Prerequisites */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {PREREQS.map((p) => {
                    const met = p.check(leadDetail ?? null);
                    const Icon = p.icon;
                    return (
                      <div key={p.id} className={cn(
                        'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-md)] border transition-colors',
                        met
                          ? 'bg-emerald-500/5 border-emerald-500/15'
                          : 'bg-[var(--color-surface-hover)] border-[var(--color-border)]',
                      )}>
                        {met ? (
                          <CheckCircle2 size={14} className="text-[var(--color-success)] shrink-0" />
                        ) : (
                          <Icon size={14} className="text-[var(--color-text-muted)] shrink-0" />
                        )}
                        <span className={cn('text-[12px]', met ? 'text-[var(--color-success)]' : 'text-[var(--color-text-muted)]')}>{p.label}</span>
                      </div>
                    );
                  })}
                </div>

                {/* Business context */}
                {leadDetail && (
                  <div className="pt-3 border-t border-[var(--color-border)]">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <MiniInfo label="Name" value={leadDetail.name} />
                      <MiniInfo label="Industry" value={leadDetail.industry} />
                      <MiniInfo label="Location" value={leadDetail.city || leadDetail.country || '\u2014'} />
                      <MiniInfo label="Audit Score" value={leadDetail.score?.overall_score != null ? `${leadDetail.score.overall_score}/100` : null} />
                    </div>
                  </div>
                )}

                {/* Screenshot preview */}
                {leadDetail?.screenshot?.desktop_cloudinary_url && (
                  <div className="pt-3 border-t border-[var(--color-border)]">
                    <p className="text-[11px] text-[var(--color-text-muted)] mb-2">Current website</p>
                    <div className="rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface-hover)]">
                      <div className="flex items-center gap-2 px-3 py-1.5 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                        <div className="flex gap-1"><span className="size-1.5 rounded-full bg-red-400/60" /><span className="size-1.5 rounded-full bg-amber-400/60" /><span className="size-1.5 rounded-full bg-emerald-400/60" /></div>
                        <span className="text-[10px] text-[var(--color-text-muted)] truncate">{leadDetail.website?.replace(/^https?:\/\//, '')}</span>
                      </div>
                      <img src={leadDetail.screenshot.desktop_cloudinary_url} alt="Current website" className="w-full max-h-48 object-cover object-top" />
                    </div>
                  </div>
                )}
              </div>
            </Panel>
          )}

          {/* ── Generation / job progress ─────────────────────── */}
          {selectedId && (
            <Panel title="Generation">
              {/* Idle: prerequisites not met */}
              {!isRunning && !isSuccess && !isError && !prereqsMet && (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="size-12 rounded-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center justify-center mb-3">
                    <AlertTriangle className="size-5 text-[var(--color-text-muted)]" />
                  </div>
                  <p className="text-[13px] font-medium text-[var(--color-text)] mb-1">Prerequisites required</p>
                  <p className="text-[12px] text-[var(--color-text-muted)] max-w-sm">
                    Complete the screenshot, analysis, and audit steps before generating a redesign.
                  </p>
                </div>
              )}

              {/* Idle: ready to generate */}
              {!isRunning && !isSuccess && !isError && prereqsMet && (
                <div className="flex flex-col items-center py-8 text-center">
                  <div className="size-12 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center mb-3">
                    <Zap className="size-5 text-[var(--color-brand)]" />
                  </div>
                  <p className="text-[13px] font-medium text-[var(--color-text)] mb-1">Ready to generate</p>
                  <p className="text-[12px] text-[var(--color-text-muted)] mb-5 max-w-sm">
                    All prerequisites are met. Start the AI generation to create a premium website redesign.
                  </p>
                  <Button variant="primary" size="md" onClick={handleGenerate} leftIcon={<Zap size={14} />}>
                    Generate Redesign
                  </Button>
                </div>
              )}

              {/* Running — Stitch-style signal progress */}
              {isRunning && (
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 rounded-[var(--radius-md)] bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)]">
                    <div className="size-4 border-2 border-[var(--color-brand-border)] border-t-[var(--color-brand)] rounded-full animate-spin shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-[var(--color-text)]">Generating website</p>
                      <p className="text-[11px] text-[var(--color-text-muted)] truncate font-mono">
                        {jobResult ? friendlyProgress(jobResult.progress) : 'Queuing job\u2026'}
                      </p>
                    </div>
                  </div>
                  {/* Signal progress bar */}
                  <div className="relative w-full h-[2px] bg-[var(--color-border)] rounded-full overflow-hidden">
                    <div className="absolute top-0 left-0 h-full bg-[var(--color-brand)] rounded-full animate-pulse" style={{ width: '60%' }} />
                  </div>
                  <p className="text-[11px] text-[var(--color-text-muted)]">
                    Generation takes 60\u2013180 s. You can safely leave this page.
                  </p>
                </div>
              )}

              {/* Success */}
              {isSuccess && (
                <div className="space-y-3">
                  <div className="p-3 rounded-[var(--radius-md)] bg-emerald-500/5 border border-emerald-500/15">
                    <div className="flex items-start gap-2.5">
                      <CheckCircle2 size={15} className="text-[var(--color-success)] shrink-0 mt-0.5" />
                      <div>
                        <p className="text-[13px] font-medium text-[var(--color-text)]">Generation complete</p>
                        <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">Website generated successfully</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="primary" size="sm" onClick={() => { if (jobResult?.website_id) navigate(`/preview/${jobResult.website_id}`); }} leftIcon={<Eye size={13} />}>
                      Open Preview
                    </Button>
                    {jobResult?.package_id && jobResult?.website_id && (
                      <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${jobResult.website_id}`)} leftIcon={<Download size={13} />}>
                        Open Package
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => navigate(selectedId ? `/project/${selectedId}` : '/projects')}>
                      Back to Lead
                    </Button>
                  </div>
                </div>
              )}

              {/* Error */}
              {isError && !isRunning && (
                <div className="space-y-3">
                  <div className="p-3 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/15">
                    <div className="flex items-start gap-2.5">
                      <AlertTriangle size={15} className="text-red-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-[13px] font-medium text-red-600 dark:text-red-400">Generation failed</p>
                        <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">{jobError || jobResult?.error || 'An unexpected error occurred.'}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="outline" size="sm" onClick={() => { handleReset(); handleGenerate(); }}>
                      Retry Generation
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => { handleReset(); setSelectedId(''); }}>
                      Select different lead
                    </Button>
                  </div>
                </div>
              )}
            </Panel>
          )}

          {/* ── Completed website result ───────────────────────── */}
          {isSuccess && existingWebsite && (
            <Panel title="Generated Website">
              <div className="flex items-start justify-between gap-3 p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                <div className="min-w-0">
                  <p className="text-[13px] font-medium text-[var(--color-text)] truncate">{existingWebsite.project_name || 'Generated Website'}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)] font-mono mt-0.5 truncate">ID: {existingWebsite.id}</p>
                </div>
                <Badge tone="success" className="text-[10px] shrink-0">{existingWebsite.status}</Badge>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${existingWebsite.id}`)} leftIcon={<Eye size={13} />}>
                  Open Preview
                </Button>
                {existingWebsite.package_id && (
                  <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${existingWebsite.id}`)} leftIcon={<Download size={13} />}>
                    Open Package
                  </Button>
                )}
                {leadDetail?.website && (
                  <a
                    href={leadDetail.website.startsWith('http') ? leadDetail.website : `https://${leadDetail.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-[12px] text-[var(--color-brand)] hover:underline ml-auto"
                  >
                    <ExternalLink size={12} /> Visit source
                  </a>
                )}
              </div>
            </Panel>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════
           SIDEBAR (workflow steps + context)
           ══════════════════════════════════════════════════════ */}
        <div className="space-y-4 lg:sticky lg:top-24">
          {/* Workflow steps */}
          <Panel title="Workflow">
            <div className="space-y-1">
              <WorkflowStep label="Select lead" done={!!selectedId} active={!selectedId} />
              <WorkflowStep label="Prerequisites" done={prereqsMet && !!selectedId} active={!!selectedId && !prereqsMet} />
              <WorkflowStep label="Generate" done={isSuccess} active={isRunning} />
              <WorkflowStep label="Preview" done={false} active={isSuccess} />
            </div>
          </Panel>

          {/* Context */}
          {selectedLead && (
            <Panel title="Context">
              <div className="space-y-2.5">
                <InfoRow label="Business" value={selectedLead.name} />
                <InfoRow label="Industry" value={selectedLead.industry} />
                <InfoRow label="Location" value={selectedLead.city || selectedLead.country || null} />
                <InfoRow label="Website" value={selectedLead.website?.replace(/^https?:\/\//, '').replace(/\/$/, '')} href={selectedLead.website?.startsWith('http') ? selectedLead.website : selectedLead.website ? `https://${selectedLead.website}` : undefined} />
                <InfoRow label="Status" value={<Badge tone={statusBadgeTone(selectedLead.status)} className="text-[10px]">{selectedLead.status.replace(/_/g, ' ')}</Badge>} />
                <InfoRow label="Audit Score" value={selectedLead.rating != null ? `${selectedLead.rating.toFixed(1)}` : null} />
              </div>
            </Panel>
          )}

          {/* Job details */}
          {jobResult && (
            <Panel title="Job">
              <div className="space-y-2.5">
                <InfoRow label="Status" value={
                  <Badge tone={isSuccess ? 'success' : isError ? 'danger' : isRunning ? 'info' : 'muted'} className="text-[10px]">
                    {isSuccess ? 'Completed' : isError ? 'Failed' : isRunning ? 'Running' : 'Pending'}
                  </Badge>
                } />
                <InfoRow label="Job ID" value={jobResult.job_id ? jobResult.job_id.slice(0, 8) + '\u2026' : null} mono />
                {jobResult.generation_time > 0 && (
                  <InfoRow label="Duration" value={`${jobResult.generation_time}s`} />
                )}
                {jobResult.website_id && (
                  <InfoRow label="Website ID" value={jobResult.website_id.slice(0, 8) + '\u2026'} mono />
                )}
              </div>
            </Panel>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   SUB-COMPONENTS
   ══════════════════════════════════════════════════════════════ */

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] transition-colors hover:border-[var(--color-border-strong)]">
      <div className="px-4 py-3 border-b border-[var(--color-border)]">
        <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function InfoRow({ label, value, href, mono }: { label: string; value: React.ReactNode | null | undefined; href?: string; mono?: boolean }) {
  if (value == null || value === '') return null;
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-[11px] text-[var(--color-text-muted)] shrink-0">{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noopener noreferrer" className="text-[12px] text-[var(--color-brand)] hover:underline text-right truncate">
          {value}
        </a>
      ) : typeof value === 'string' ? (
        <span className={cn('text-[12px] text-[var(--color-text-secondary)] text-right truncate', mono && 'font-mono')}>{value}</span>
      ) : (
        <span className="text-right">{value}</span>
      )}
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div>
      <p className="text-[10px] text-[var(--color-text-muted)] mb-0.5">{label}</p>
      <p className="text-[12px] text-[var(--color-text-secondary)] truncate">{value}</p>
    </div>
  );
}

function WorkflowStep({ label, done, active }: { label: string; done: boolean; active: boolean }) {
  return (
    <div className="flex items-center gap-2.5 py-1.5">
      <div className={cn(
        'size-5 rounded-full flex items-center justify-center shrink-0 transition-colors',
        done ? 'bg-[var(--color-success)]' : active ? 'bg-[var(--color-brand)]' : 'bg-[var(--color-surface-hover)] border border-[var(--color-border)]',
      )}>
        {done && <CheckCircle2 size={12} className="text-white" />}
        {active && <div className="size-1.5 rounded-full bg-white animate-pulse" />}
      </div>
      <span className={cn('text-[12px]', done ? 'text-[var(--color-text)]' : active ? 'text-[var(--color-text)] font-medium' : 'text-[var(--color-text-muted)]')}>
        {label}
      </span>
    </div>
  );
}
