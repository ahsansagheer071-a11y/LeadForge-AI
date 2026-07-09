import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Globe, Loader2, CheckCircle2, AlertCircle, Camera, Search, Shield, Zap } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { projectsService, createGenerationJob, pollGenerationJob } from '@/services/services';
import type { GenerationJobResult } from '@/services/services';
import { usePreviewStore } from '@/store';
import { cn } from '@/utils';
import { toast } from 'sonner';

const statusBadgeTone = (status: string): 'success' | 'info' | 'brand' | 'muted' => {
  if (status.includes('READY')) return 'success';
  if (status.includes('ANALYZED') || status.includes('SCORED')) return 'info';
  if (status.includes('SCRAPED') || status.includes('DISCOVERED') || status.includes('NEW')) return 'brand';
  return 'muted';
};

/* ── Prerequisite check items ────────────────────────────────── */
interface Prereq {
  id: string;
  label: string;
  icon: typeof Camera;
  color: string;
  check: (lead: { screenshot?: unknown; audit?: unknown; score?: unknown } | null) => boolean;
}

const PREREQS: Prereq[] = [
  { id: 'screenshot', label: 'Screenshot Captured', icon: Camera, color: '#06b6d4', check: (l) => !!l?.screenshot },
  { id: 'analysis', label: 'Website Analyzed', icon: Search, color: '#8b5cf6', check: () => true },
  { id: 'audit', label: 'Audit Complete', icon: Shield, color: '#f59e0b', check: (l) => !!l?.audit && !!l?.score },
];

// Progress messages to rotate through during generation
const PROGRESS_LABELS: Record<string, string> = {
  Queued: 'Queued — waiting to start…',
  'Loading lead data': 'Loading lead data…',
  'Crawling website': 'Crawling website (this may take 30–60 s)…',
  'Crawling website (fresh)': 'Crawling website — fresh scan…',
  'Building markdown context': 'Building AI context from site data…',
  'Generating HTML with AI': 'Generating HTML with AI (this may take 60–120 s)…',
  'Saving result': 'Saving generated website…',
  Complete: 'Complete!',
};

function friendlyProgress(raw: string): string {
  return PROGRESS_LABELS[raw] ?? raw;
}

/* ── Poll interval (ms) ─────────────────────────────────────── */
const POLL_INTERVAL_MS = 3000;

export function GenerationPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [selectedId, setSelectedId] = useState('');

  // Async job state
  const [_, setJobId] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<GenerationJobResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobError, setJobError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  // ── Job polling ──────────────────────────────────────────────
  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = (id: string) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const result = await pollGenerationJob(id);
        setJobResult(result);
        if (result.status === 'succeeded') {
          stopPolling();
          if (result.html) setHtmlContent(result.html);
          if (result.website_id) {
            toast.success('Website generated successfully!');
            queryClient.invalidateQueries({ queryKey: ['lead', selectedId] });
            queryClient.invalidateQueries({ queryKey: ['generated-website-latest', selectedId] });
          }
        } else if (result.status === 'failed') {
          stopPolling();
          const msg = result.error || 'Generation failed. Please try again.';
          setJobError(msg);
          toast.error(msg);
        }
      } catch (err: unknown) {
        console.warn('Poll error (will retry):', err);
        // Don't stop polling on transient network errors
      }
    }, POLL_INTERVAL_MS);
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  // ── Submit generation job ────────────────────────────────────
  const handleGenerate = async () => {
    if (!selectedId || isSubmitting) return;
    setIsSubmitting(true);
    setJobId(null);
    setJobResult(null);
    setJobError(null);

    try {
      const { job_id } = await createGenerationJob(selectedId);
      setJobId(job_id);
      // Set initial pending state immediately
      setJobResult({
        job_id,
        lead_id: selectedId,
        status: 'pending',
        progress: 'Queued',
        generation_time: 0,
      });
      startPolling(job_id);
    } catch (err: unknown) {
      const msg = (() => {
        if (err && typeof err === 'object') {
          const e = err as Record<string, unknown>;
          if (e.category === 'network') return 'Cannot connect to the LeadForge API. Please check your connection.';
          if (e.category === 'timeout') return 'Request timed out queuing the job. Please retry.';
          if (e.category === 'authentication') return 'Your session expired. Please sign in again.';
          if (typeof e.message === 'string') return e.message;
        }
        return 'Failed to queue generation job. Please retry.';
      })();
      setJobError(msg);
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    stopPolling();
    setJobId(null);
    setJobResult(null);
    setJobError(null);
  };

  const isRunning = jobResult?.status === 'pending' || jobResult?.status === 'running' || isSubmitting;
  const isSuccess = jobResult?.status === 'succeeded';
  const isError = !!jobError || jobResult?.status === 'failed';

  const prereqsMet = PREREQS.every((p) => p.check(leadDetail ?? null));
  const canGenerate = !!selectedId && prereqsMet && !isRunning && !isSuccess;

  return (
    <div className="space-y-8 lf-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">AI Synthesis Lab</h1>
        <p className="text-[13px] font-mono text-[var(--color-text-secondary)] uppercase tracking-widest">Generate premium websites from intelligence profiles</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Lead selector + prerequisites ────────────────────── */}
        <PremiumCard innerClassName="p-6 flex flex-col" className="lg:col-span-1">
          <div className="mb-4 pb-4 border-b border-[var(--color-border)]">
            <h3 className="text-[14px] font-mono uppercase tracking-widest text-[#0ea5e9]">Target Selection</h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 lf-thin-scroll pr-2 min-h-0">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} variant="rounded" width="100%" height={64} delay={i * 60} />
                ))}
              </div>
            ) : leads.length > 0 ? (
              leads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => { setSelectedId(lead.id); handleReset(); }}
                  className={cn(
                    'w-full text-left px-4 py-3 rounded-[var(--radius-md)] transition-all duration-200 group border',
                    selectedId === lead.id
                      ? 'bg-gradient-to-r from-[#0ea5e9]/15 to-[#8b5cf6]/15 border-[#0ea5e9]/30 shadow-[0_0_15px_rgba(14,165,233,0.1)]'
                      : 'bg-[var(--color-surface-hover)] border-transparent hover:border-[var(--color-border-strong)]',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={cn("font-bold truncate text-[14px]", selectedId === lead.id ? "text-white" : "text-[var(--color-text)]")}>{lead.name}</span>
                    <Badge tone={statusBadgeTone(lead.status)} className="scale-90 font-mono origin-right shrink-0">{lead.status.replace(/_/g, ' ')}</Badge>
                  </div>
                  <div className="flex items-center gap-2 mt-1">
                    {lead.website && <span className="text-[11px] font-mono text-[var(--color-text-muted)] truncate">{lead.website}</span>}
                    {lead.rating != null && <span className="text-[11px] font-mono text-amber-400 shrink-0">★ {lead.rating.toFixed(1)}</span>}
                  </div>
                </button>
              ))
            ) : (
              <EmptyState title="No active targets" message="Discover and process targets first." />
            )}
          </div>

          {/* Prerequisite checklist */}
          {selectedId && (
            <div className="pt-5 mt-4 border-t border-[var(--color-border)] space-y-3">
              <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--color-text-muted)]">Prerequisites</p>
              {PREREQS.map((p) => {
                const met = p.check(leadDetail ?? null);
                const Icon = p.icon;
                return (
                  <div key={p.id} className="flex items-center gap-3">
                    <div className={cn(
                      'size-7 rounded-md flex items-center justify-center shrink-0 transition-all',
                      met ? 'bg-emerald-500/15 border border-emerald-500/30' : 'bg-[var(--color-surface-hover)] border border-[var(--color-border)]',
                    )}>
                      {met ? <CheckCircle2 size={13} className="text-emerald-400" /> : <Icon size={13} className="text-[var(--color-text-muted)]" />}
                    </div>
                    <span className={cn('text-[12px] font-mono', met ? 'text-emerald-400' : 'text-[var(--color-text-muted)]')}>{p.label}</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Generate button */}
          {leads.length > 0 && (
            <div className="pt-5 mt-4 border-t border-[var(--color-border)]">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-mono text-[var(--color-text-muted)] truncate">{selectedLead?.name || 'Awaiting Selection'}</span>
              </div>
              <button
                disabled={!canGenerate}
                onClick={handleGenerate}
                className={cn(
                  'w-full flex items-center justify-center gap-2 py-3.5 rounded-[var(--radius-md)] text-[13px] font-mono uppercase tracking-widest font-bold transition-all duration-300',
                  canGenerate
                    ? 'bg-gradient-to-r from-[#8b5cf6] to-[#d946ef] text-white shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] hover:-translate-y-0.5'
                    : 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] cursor-not-allowed',
                )}
              >
                {isRunning ? (
                  <><Loader2 className="size-4 lf-spin" /> Synthesizing...</>
                ) : (
                  <><Sparkles className="size-4" /> Initiate Generation</>
                )}
              </button>
              {isError && !isRunning && (
                <button
                  onClick={handleReset}
                  className="w-full mt-2 py-2 text-[11px] font-mono text-[var(--color-text-muted)] hover:text-white transition-colors"
                >
                  Reset &amp; try again
                </button>
              )}
              {selectedId && !prereqsMet && (
                <p className="text-[10px] font-mono text-[var(--color-text-muted)] text-center mt-2">Complete prerequisites above to enable generation</p>
              )}
            </div>
          )}
        </PremiumCard>

        {/* ── AI Processing Core ──────────────────────────────── */}
        <PremiumCard
          variant={isRunning ? 'featured' : isSuccess ? 'standard' : 'standard'}
          className="lg:col-span-2"
          innerClassName="relative overflow-hidden p-8 flex flex-col items-center justify-center min-h-[500px] lg:min-h-[600px]"
        >
          {/* Background effects */}
          {isRunning && (
            <>
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(139,92,246,0.12),transparent_60%)] pointer-events-none" />
              <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.03) 39px, rgba(255,255,255,0.03) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.03) 39px, rgba(255,255,255,0.03) 40px)' }} />
              {/* Animated data lines */}
              <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-20">
                <div className="absolute top-1/4 left-0 w-full h-px bg-gradient-to-r from-transparent via-[#8b5cf6] to-transparent animate-[lf-slide-right_2s_linear_infinite]" />
                <div className="absolute top-2/4 left-0 w-full h-px bg-gradient-to-r from-transparent via-[#0ea5e9] to-transparent animate-[lf-slide-right_2.5s_linear_infinite]" />
                <div className="absolute top-3/4 left-0 w-full h-px bg-gradient-to-r from-transparent via-[#d946ef] to-transparent animate-[lf-slide-right_3s_linear_infinite]" />
              </div>
            </>
          )}

          <div className="relative z-10 w-full flex flex-col items-center justify-center text-center">
            {/* ── Idle state ──────────────────────────────────── */}
            {!selectedId && (
              <div className="flex flex-col items-center lf-fade-in">
                <div className="size-20 rounded-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] flex items-center justify-center mb-6">
                  <Globe className="size-10 text-[var(--color-text-muted)]" />
                </div>
                <p className="text-[13px] font-mono text-[var(--color-text-muted)] uppercase tracking-widest max-w-xs leading-relaxed">
                  Select a target profile to initiate AI web synthesis.
                </p>
              </div>
            )}

            {/* ── Pre-flight (selected, prerequisites shown) ──── */}
            {selectedId && !isRunning && !isSuccess && !isError && (
              <div className="flex flex-col items-center lf-fade-in">
                <div className="relative mb-8">
                  <div className="size-24 rounded-full bg-gradient-to-br from-[#8b5cf6]/20 to-[#d946ef]/20 border border-[#8b5cf6]/30 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.15)]">
                    <Zap className="size-10 text-[#8b5cf6]" />
                  </div>
                </div>
                <h3 className="text-[22px] font-bold text-white mb-2">{selectedLead?.name || 'Target Selected'}</h3>
                <p className="text-[12px] font-mono text-[var(--color-text-secondary)] mb-6 max-w-md">
                  {prereqsMet
                    ? 'All prerequisites verified. Ready to synthesize a premium website from intelligence data.'
                    : 'Complete the prerequisite checklist on the left panel to enable generation.'}
                </p>
                {prereqsMet && (
                  <button
                    onClick={handleGenerate}
                    className="bg-gradient-to-r from-[#8b5cf6] to-[#d946ef] text-white px-8 py-3.5 rounded-[var(--radius-md)] font-bold font-mono uppercase tracking-widest text-[13px] shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.5)] hover:-translate-y-0.5 transition-all flex items-center gap-2"
                  >
                    <Sparkles size={16} /> Generate Website
                  </button>
                )}
              </div>
            )}

            {/* ── Loading/generating state ────────────────────── */}
            {isRunning && (
              <div className="flex flex-col items-center">
                <div className="relative mb-8">
                  <div className="absolute inset-0 rounded-full bg-[#8b5cf6]/20 blur-2xl animate-pulse" />
                  <div className="absolute inset-0 border-t-2 border-[#d946ef] rounded-full animate-spin" style={{ animationDuration: '3s' }} />
                  <div className="absolute inset-2 border-b-2 border-[#0ea5e9] rounded-full animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
                  <div className="relative size-24 rounded-full bg-[var(--color-glass-strong)] border border-[var(--color-border-strong)] flex items-center justify-center backdrop-blur-md">
                    <Loader2 className="size-8 text-white lf-spin" />
                  </div>
                </div>
                <h3 className="text-[20px] font-bold text-white mb-2">Synthesizing Digital Presence</h3>
                <p className="text-[12px] font-mono text-[#0ea5e9] uppercase tracking-widest animate-pulse mb-1">
                  {jobResult ? friendlyProgress(jobResult.progress) : 'Queuing job…'}
                </p>
                <p className="text-[10px] font-mono text-[var(--color-text-muted)]">
                  Generation takes 60–180 s. You can safely leave this page.
                </p>
              </div>
            )}

            {/* ── Success state ───────────────────────────────── */}
            {isSuccess && (
              <div className="flex flex-col items-center lf-fade-in">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-full bg-emerald-500/20 blur-xl" />
                  <div className="relative size-20 rounded-full bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.2)]">
                    <CheckCircle2 className="size-10 text-emerald-400" />
                  </div>
                </div>
                <h3 className="text-[24px] font-bold text-white mb-2">Synthesis Complete</h3>
                <p className="text-[13px] font-mono text-[var(--color-text-secondary)] mb-8 uppercase tracking-widest">Web property generated successfully</p>
                <div className="flex flex-wrap gap-3 justify-center">
                  <button
                    onClick={() => { if (jobResult?.website_id) navigate(`/preview/${jobResult.website_id}`); }}
                    className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-8 py-3 rounded-[var(--radius-md)] font-mono uppercase tracking-widest text-[13px] font-bold hover:bg-emerald-500/20 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all flex items-center gap-2"
                  >
                    <CheckCircle2 size={15} /> Enter Preview Studio
                  </button>
                  {jobResult?.package_id && (
                    <button
                      onClick={() => { if (jobResult?.website_id) navigate(`/deployment/${jobResult.website_id}`); }}
                      className="bg-[#0ea5e9]/10 text-[#0ea5e9] border border-[#0ea5e9]/30 px-8 py-3 rounded-[var(--radius-md)] font-mono uppercase tracking-widest text-[13px] font-bold hover:bg-[#0ea5e9]/20 hover:shadow-[0_0_20px_rgba(14,165,233,0.3)] transition-all flex items-center gap-2"
                    >
                      Open Package
                    </button>
                  )}
                  <button
                    onClick={() => navigate('/projects')}
                    className="bg-[var(--color-glass)] backdrop-blur-md text-[var(--color-text)] border border-[var(--color-glass-border)] px-6 py-3 rounded-[var(--radius-md)] font-medium hover:bg-[var(--color-glass-strong)] transition-all font-mono text-[12px]"
                  >
                    Back to Pipeline
                  </button>
                </div>
              </div>
            )}

            {/* ── Error state ─────────────────────────────────── */}
            {isError && !isRunning && (
              <div className="flex flex-col items-center lf-fade-in">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-full bg-red-500/20 blur-xl" />
                  <div className="relative size-20 rounded-full bg-red-500/15 border border-red-500/40 flex items-center justify-center">
                    <AlertCircle className="size-10 text-red-400" />
                  </div>
                </div>
                <h3 className="text-[20px] font-bold text-white mb-2">Synthesis Failed</h3>
                <p className="text-[13px] text-[var(--color-text-secondary)] mb-6 font-mono text-center max-w-sm">
                  {jobError || jobResult?.error || 'An unexpected error occurred.'}
                </p>
                <div className="flex flex-wrap gap-3 justify-center">
                  <button
                    onClick={() => { handleReset(); handleGenerate(); }}
                    className="bg-red-500/10 text-red-400 border border-red-500/30 px-6 py-2.5 rounded-[var(--radius-md)] font-mono uppercase tracking-widest text-[12px] font-bold hover:bg-red-500/20 transition-all flex items-center gap-2"
                  >
                    <Loader2 size={14} /> Retry Generation
                  </button>
                  <button
                    onClick={() => { handleReset(); setSelectedId(''); }}
                    className="bg-[var(--color-glass)] text-[var(--color-text)] border border-[var(--color-glass-border)] px-6 py-2.5 rounded-[var(--radius-md)] font-mono text-[12px] hover:bg-[var(--color-glass-strong)] transition-all"
                  >
                    Select Different Target
                  </button>
                </div>
              </div>
            )}
          </div>
        </PremiumCard>
      </div>

      {/* ═══════════════════════════════════════════════════════════
         PREREQUISITE DETAIL (mobile/secondary)
      ════════════════════════════════════════════════════════════ */}
      {selectedId && !isRunning && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {PREREQS.map((p) => {
            const met = p.check(leadDetail ?? null);
            const Icon = p.icon;
            return (
              <PremiumCard key={p.id} variant={met ? 'standard' : 'subtle'} innerClassName="p-4 flex items-center gap-4">
                <div className={cn(
                  'size-10 rounded-[var(--radius-md)] flex items-center justify-center shrink-0',
                  met ? 'bg-emerald-500/10 border border-emerald-500/25' : 'bg-[var(--color-surface-hover)] border border-[var(--color-border)]',
                )}>
                  {met ? <CheckCircle2 size={18} className="text-emerald-400" /> : <Icon size={18} className="text-[var(--color-text-muted)]" />}
                </div>
                <div>
                  <p className={cn('text-[13px] font-semibold', met ? 'text-emerald-400' : 'text-[var(--color-text-secondary)]')}>
                    {met ? 'Completed' : p.label}
                  </p>
                  <p className="text-[10px] font-mono text-[var(--color-text-muted)]">{met ? 'Ready' : 'Required'}</p>
                </div>
              </PremiumCard>
            );
          })}
        </div>
      )}
    </div>
  );
}
