import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle2, AlertTriangle, Camera, Search, Shield, Zap, Eye, Download, ExternalLink } from 'lucide-react';
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

  const { data: page, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: () => projectsService.list(1, 50),
  });

  const leads = page?.items ?? [];
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
    onSuccess: (websiteId, htmlContent) => {
      if (htmlContent) setHtmlContent(htmlContent);
      queryClient.invalidateQueries({ queryKey: ['lead', selectedId] });
      queryClient.invalidateQueries({ queryKey: ['generated-website-latest', selectedId] });
      toast.success('Website generated successfully');
    },
    onError: (msg) => { toast.error(msg); },
  });

  const handleGenerate = () => generate();
  const handleReset = () => reset();

  const prereqsMet = PREREQS.every((p) => p.check(leadDetail ?? null));

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Back nav ──────────────────────────────────────────── */}
      <button
        onClick={() => navigate(selectedId ? `/project/${selectedId}` : '/projects')}
        className="inline-flex items-center gap-1.5 text-[12px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        <ArrowLeft size={14} /> {selectedId ? 'Lead Workspace' : 'Leads'}
      </button>

      {/* ── Page header ───────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <p className="text-[13px] text-[var(--color-text-muted)] font-mono mb-1">Generation</p>
          <h1 className="lf-display text-[var(--color-text)]">Redesign Studio</h1>
          {selectedLead && (
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-[13px] font-medium text-[var(--color-text-secondary)]">{selectedLead.name}</span>
              {selectedLead.website && (
                <span className="text-[12px] text-[var(--color-text-muted)]">
                  {'\u00B7'} {selectedLead.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                </span>
              )}
              <Badge tone={statusBadgeTone(selectedLead.status)} className="text-[10px]">{selectedLead.status.replace(/_/g, ' ')}</Badge>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isSuccess && jobResult?.website_id && (
            <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${jobResult.website_id}`)}>
              <Eye size={14} className="mr-1" /> Open Preview
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* ═══════════════════════════════════════════════════════
           MAIN COLUMN
           ══════════════════════════════════════════════════════ */}
        <div className="lg:col-span-2 space-y-5">
          {/* ── Source section ─────────────────────────────────── */}
          <SectionCard title="Source">
            {isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} variant="rounded" width="100%" height={52} delay={i * 40} />
                ))}
              </div>
            ) : leads.length > 0 ? (
              <div className="space-y-1.5">
                {leads.map((lead) => (
                  <button
                    key={lead.id}
                    onClick={() => { setSelectedId(lead.id); handleReset(); }}
                    className={cn(
                      'w-full text-left px-3.5 py-2.5 rounded-[var(--radius-md)] transition-colors duration-[var(--anim-fast)] border group',
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
                      {lead.website && <span className="text-[11px] text-[var(--color-text-muted)] truncate">{lead.website.replace(/^https?:\/\//, '')}</span>}
                      {lead.rating != null && <span className="text-[11px] text-[var(--color-text-muted)] tabular-nums shrink-0">{lead.rating.toFixed(1)}</span>}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title="No leads available" message="Discover and process leads first." />
            )}
          </SectionCard>

          {/* ── Direction / prompt section ─────────────────────── */}
          {selectedId && (
            <SectionCard
              title="Direction"
              action={
                prereqsMet ? (
                  <Badge tone="success" className="text-[10px]">Prerequisites met</Badge>
                ) : (
                  <Badge tone="warning" className="text-[10px]">Missing prerequisites</Badge>
                )
              }
            >
              <div className="space-y-4">
                {/* Prerequisites */}
                <div className="space-y-2">
                  <p className="text-[11px] text-[var(--color-text-muted)]">Prerequisites</p>
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
                </div>

                {/* Business context */}
                {leadDetail && (
                  <div className="pt-3 border-t border-[var(--color-border)]">
                    <p className="text-[11px] text-[var(--color-text-muted)] mb-2">Business context</p>
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
            </SectionCard>
          )}

          {/* ── Generation / job progress section ──────────────── */}
          {selectedId && (
            <SectionCard title="Generation">
              {/* Idle state */}
              {!isRunning && !isSuccess && !isError && (
                <div className="space-y-4">
                  {prereqsMet ? (
                    <div className="flex flex-col items-center py-8 text-center">
                      <div className="size-14 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center mb-4">
                        <Zap className="size-6 text-[var(--color-brand)]" />
                      </div>
                      <p className="text-[14px] font-medium text-[var(--color-text)] mb-1">Ready to generate</p>
                      <p className="text-[12px] text-[var(--color-text-muted)] mb-5 max-w-sm">
                        All prerequisites are met. Start the AI generation to create a premium website redesign.
                      </p>
                      <Button variant="primary" size="md" onClick={handleGenerate} leftIcon={<Zap size={15} />}>
                        Generate Redesign
                      </Button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center py-8 text-center">
                      <div className="size-14 rounded-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center justify-center mb-4">
                        <AlertTriangle className="size-6 text-[var(--color-text-muted)]" />
                      </div>
                      <p className="text-[14px] font-medium text-[var(--color-text)] mb-1">Prerequisites required</p>
                      <p className="text-[12px] text-[var(--color-text-muted)] max-w-sm">
                        Complete the screenshot, analysis, and audit steps before generating a redesign.
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Running state */}
              {isRunning && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                    <div className="size-5 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-[var(--color-text)]">Generating website</p>
                      <p className="text-[12px] text-[var(--color-text-muted)] truncate">
                        {jobResult ? friendlyProgress(jobResult.progress) : 'Queuing job\u2026'}
                      </p>
                    </div>
                  </div>
                  <p className="text-[11px] text-[var(--color-text-muted)]">
                    Generation takes 60\u2013180 s. You can safely leave this page.
                  </p>
                </div>
              )}

              {/* Success state */}
              {isSuccess && (
                <div className="space-y-4">
                  <div className="p-4 rounded-[var(--radius-md)] bg-emerald-500/5 border border-emerald-500/15">
                    <div className="flex items-start gap-3">
                      <CheckCircle2 size={16} className="text-[var(--color-success)] shrink-0 mt-0.5" />
                      <div>
                        <p className="text-[13px] font-medium text-[var(--color-text)]">Generation complete</p>
                        <p className="text-[12px] text-[var(--color-text-muted)] mt-0.5">Website generated successfully</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button variant="primary" size="sm" onClick={() => { if (jobResult?.website_id) navigate(`/preview/${jobResult.website_id}`); }}>
                      <Eye size={14} className="mr-1.5" /> Open Preview
                    </Button>
                    {jobResult?.package_id && jobResult?.website_id && (
                      <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${jobResult.website_id}`)}>
                        <Download size={14} className="mr-1.5" /> Open Package
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => navigate(selectedId ? `/project/${selectedId}` : '/projects')}>
                      Back to Lead
                    </Button>
                  </div>
                </div>
              )}

              {/* Error state */}
              {isError && !isRunning && (
                <div className="space-y-4">
                  <div className="p-4 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/15">
                    <div className="flex items-start gap-3">
                      <AlertTriangle size={16} className="text-red-500 shrink-0 mt-0.5" />
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
            </SectionCard>
          )}

          {/* ── Completed website result ───────────────────────── */}
          {isSuccess && existingWebsite && (
            <SectionCard title="Generated Website">
              <div className="space-y-4">
                <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[14px] font-medium text-[var(--color-text)]">{existingWebsite.project_name || 'Generated Website'}</p>
                      <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">ID: {existingWebsite.id}</p>
                    </div>
                    <Badge tone="success" className="text-[10px] shrink-0">{existingWebsite.status}</Badge>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${existingWebsite.id}`)}>
                    <Eye size={14} className="mr-1.5" /> Open Preview
                  </Button>
                  {existingWebsite.package_id && (
                    <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${existingWebsite.id}`)}>
                      <Download size={14} className="mr-1.5" /> Open Package
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
              </div>
            </SectionCard>
          )}
        </div>

        {/* ═══════════════════════════════════════════════════════
           SIDEBAR
           ══════════════════════════════════════════════════════ */}
        <div className="space-y-4 lg:sticky lg:top-24">
          {/* Context */}
          {selectedLead && (
            <SectionCard title="Context">
              <div className="space-y-3">
                <InfoRow label="Business" value={selectedLead.name} />
                <InfoRow label="Industry" value={selectedLead.industry} />
                <InfoRow label="Location" value={selectedLead.city || selectedLead.country || null} />
                <InfoRow label="Website" value={selectedLead.website?.replace(/^https?:\/\//, '').replace(/\/$/, '')} href={selectedLead.website?.startsWith('http') ? selectedLead.website : selectedLead.website ? `https://${selectedLead.website}` : undefined} />
                <InfoRow label="Status" value={<Badge tone={statusBadgeTone(selectedLead.status)} className="text-[10px]">{selectedLead.status.replace(/_/g, ' ')}</Badge>} />
                <InfoRow label="Audit Score" value={selectedLead.rating != null ? `${selectedLead.rating.toFixed(1)}` : null} />
              </div>
            </SectionCard>
          )}

          {/* Job details */}
          {jobResult && (
            <SectionCard title="Job">
              <div className="space-y-3">
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
            </SectionCard>
          )}

          {/* Workflow steps */}
          <SectionCard title="Workflow">
            <div className="space-y-1.5">
              <WorkflowStep label="Select lead" done={!!selectedId} active={!selectedId} />
              <WorkflowStep label="Prerequisites" done={prereqsMet && !!selectedId} active={!!selectedId && !prereqsMet} />
              <WorkflowStep label="Generate" done={isSuccess} active={isRunning} />
              <WorkflowStep label="Preview" done={false} active={isSuccess} />
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   SUB-COMPONENTS
   ══════════════════════════════════════════════════════════════ */

function SectionCard({ title, action, children }: { title: string; action?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)]">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-[var(--color-border)]">
        <h3 className="text-[13px] font-semibold text-[var(--color-text)]">{title}</h3>
        {action}
      </div>
      <div className="p-5">{children}</div>
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
        {active && <div className="size-1.5 rounded-full bg-white lf-pulse" />}
      </div>
      <span className={cn('text-[12px]', done ? 'text-[var(--color-text)]' : active ? 'text-[var(--color-text)] font-medium' : 'text-[var(--color-text-muted)]')}>
        {label}
      </span>
    </div>
  );
}
