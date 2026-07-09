import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe, MapPin, Phone, Star, Building, Shield, AlertTriangle, CheckCircle, Search, Camera, Send, Copy, ExternalLink, ChevronRight, ChevronDown, Zap, Eye, Download, X, Maximize2, Loader2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { ScoreGauge } from '@/components/ScoreGauge';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { projectsService, generateWebsite, auditService, analysisService, screenshotService, outreachService, generationService } from '@/services/services';
import { extractApiError, getApiErrorMessage } from '@/services/apiClient';
import { usePreviewStore } from '@/store';
import { formatRelative, cn } from '@/utils';
import { toast } from 'sonner';
import type { AuditAndScoreResult, WebsiteAnalysisResponse, CaptureScreenshotResponse, OutreachResponse } from '@/types';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info', SCRAPED: 'brand', ANALYZED: 'warning', OUTREACH_READY: 'success', CONTACTED: 'brand', CLOSED: 'success',
};

/* ── Workflow stages ──────────────────────────────────────────── */
type StageId = 'lead' | 'screenshot' | 'analysis' | 'audit' | 'generation' | 'preview' | 'package' | 'outreach';
type StageState = 'completed' | 'active' | 'pending' | 'blocked' | 'failed';

interface StageDef {
  id: StageId;
  label: string;
  icon: typeof Camera;
  color: string;
}

const STAGES: StageDef[] = [
  { id: 'lead', label: 'Lead', icon: Building, color: '#0ea5e9' },
  { id: 'screenshot', label: 'Screenshot', icon: Camera, color: '#06b6d4' },
  { id: 'analysis', label: 'Analysis', icon: Search, color: '#8b5cf6' },
  { id: 'audit', label: 'Audit', icon: Shield, color: '#f59e0b' },
  { id: 'generation', label: 'Generation', icon: Zap, color: '#10b981' },
  { id: 'preview', label: 'Preview', icon: Eye, color: '#6366f1' },
  { id: 'package', label: 'Package', icon: Download, color: '#ec4899' },
  { id: 'outreach', label: 'Outreach', icon: Send, color: '#22d3ee' },
];

function rawState(
  sid: StageId,
  screenshot: CaptureScreenshotResponse | null,
  analysis: WebsiteAnalysisResponse | null,
  audit: AuditAndScoreResult | null,
  website: unknown | null,
  outreach: OutreachResponse | null,
  mutations: Record<string, { isPending: boolean; error: unknown }>,
): StageState {
  if (sid === 'lead') return 'completed';

  let hasData = false;
  switch (sid) {
    case 'screenshot': hasData = !!(screenshot?.desktop_url || screenshot?.mobile_url); break;
    case 'analysis': hasData = !!analysis; break;
    case 'audit': hasData = !!audit; break;
    case 'generation': hasData = !!website; break;
    case 'preview': hasData = !!website; break;
    case 'package': hasData = !!(website && (website as { package_id?: string })?.package_id); break;
    case 'outreach': hasData = !!outreach; break;
  }

  if (mutations[sid]?.isPending) return 'active';
  if (hasData) return 'completed';
  if (mutations[sid]?.error) return 'failed';
  return 'pending';
}

function getStageState(
  id: StageId,
  screenshot: CaptureScreenshotResponse | null,
  analysis: WebsiteAnalysisResponse | null,
  audit: AuditAndScoreResult | null,
  website: unknown | null,
  outreach: OutreachResponse | null,
  mutations: Record<string, { isPending: boolean; error: unknown }>,
): StageState {
  if (id === 'lead') return 'completed';

  const states = STAGES.map(s => rawState(s.id, screenshot, analysis, audit, website, outreach, mutations));
  const targetIdx = STAGES.findIndex(s => s.id === id);
  const firstNonCompleted = states.findIndex(s => s !== 'completed');

  if (firstNonCompleted === -1) return 'completed';
  if (targetIdx < firstNonCompleted) return 'completed';
  if (targetIdx === firstNonCompleted) return states[targetIdx];
  return 'blocked';
}

function getActiveStage(
  screenshot: CaptureScreenshotResponse | null,
  analysis: WebsiteAnalysisResponse | null,
  audit: AuditAndScoreResult | null,
  website: unknown | null,
  outreach: OutreachResponse | null,
  mutations: Record<string, { isPending: boolean; error: unknown }>,
): StageDef | null {
  const states = STAGES.map(s => rawState(s.id, screenshot, analysis, audit, website, outreach, mutations));
  for (let i = 0; i < STAGES.length; i++) {
    if (states[i] === 'completed') continue;
    if (states[i] === 'active' || states[i] === 'pending' || states[i] === 'failed') return STAGES[i];
    break;
  }
  return null;
}

/* ── Score breakdown bar helper ───────────────────────────────── */
function ScoreBar({ label, value, color }: { label: string; value: number; color?: string }) {
  const pct = Math.min(100, Math.max(0, value));
  const barColor = color ?? (pct >= 80 ? '#22c55e' : pct >= 60 ? '#eab308' : pct >= 40 ? '#f97316' : '#dc2626');
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[11px] font-mono">
        <span className="uppercase tracking-wider text-[var(--color-text-secondary)]">{label}</span>
        <span className="font-semibold" style={{ color: barColor }}>{Math.round(pct)}</span>
      </div>
      <div className="h-2 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${barColor}, ${barColor}88)` }} />
      </div>
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────── */
export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [analysisResult, setAnalysisResult] = useState<WebsiteAnalysisResponse | null>(null);
  const [auditResult, setAuditResult] = useState<AuditAndScoreResult | null>(null);
  const [screenshotResult, setScreenshotResult] = useState<CaptureScreenshotResponse | null>(null);
  const [outreachResult, setOutreachResult] = useState<OutreachResponse | null>(null);
  const [fullScreenImg, setFullScreenImg] = useState<string | null>(null);

  const { data: lead, isLoading, error } = useQuery({
    queryKey: ['lead', id],
    queryFn: () => projectsService.getById(id!),
    enabled: !!id,
  });

  const { data: existingWebsite } = useQuery({
    queryKey: ['generated-website-latest', id],
    queryFn: () => generationService.getLatestByLeadId(id!),
    enabled: !!id,
    staleTime: 30_000,
    retry: false,
  });

  useEffect(() => {
    if (lead) {
      if (lead.screenshot) {
        setScreenshotResult({
          lead_id: lead.id,
          desktop_url: lead.screenshot.desktop_cloudinary_url,
          mobile_url: lead.screenshot.mobile_cloudinary_url,
          full_page_url: lead.screenshot.full_page_cloudinary_url,
        });
      }
      if (lead.outreach) {
        setOutreachResult(lead.outreach);
      }
      if (lead.audit && lead.score) {
        const reconstructed: Record<string, unknown> = {};
        if (lead.audit.executive_summary) reconstructed['Business Summary'] = lead.audit.executive_summary;
        if (lead.audit.weaknesses && Array.isArray(lead.audit.weaknesses)) reconstructed['Top Weaknesses'] = lead.audit.weaknesses;
        if (lead.audit.verdict) reconstructed['Overall Summary'] = lead.audit.verdict;
        setAuditResult({
          lead_id: lead.id,
          audit: Object.keys(reconstructed).length > 0 ? reconstructed : { 'Overall Summary': lead.audit.verdict || 'Audit data available' },
          score: lead.score,
        });
      }
    }
  }, [lead]);

  const generationMutation = useMutation({
    mutationFn: () => generateWebsite(id!),
    onSuccess: (data) => {
      if (!data?.website_id) { toast.error('Generation failed — no website ID returned'); return; }
      setHtmlContent(data.html);
      toast.success('Website generated successfully');
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      queryClient.invalidateQueries({ queryKey: ['generated-website-latest', id] });
      navigate(`/preview/${data.website_id}`);
    },
    onError: (err) => {
      const apiErr = extractApiError(err);
      if (apiErr.category === 'network') toast.error('Cannot connect to the LeadForge API. Please try again.');
      else if (apiErr.category === 'timeout') toast.error('Website generation took too long. No duplicate request was submitted; you can safely retry.');
      else if (apiErr.category === 'provider') toast.error('The AI generation provider is temporarily unavailable. Please retry.');
      else if (apiErr.category === 'authentication') toast.error('Your session expired. Please sign in again.');
      else toast.error(apiErr.message || 'Generation failed');
    },
  });

  const analysisMutation = useMutation({
    mutationFn: () => analysisService.analyzeWebsite(id!),
    onSuccess: (result) => { setAnalysisResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('Website analyzed successfully'); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Analysis failed')); },
  });

  const auditMutation = useMutation({
    mutationFn: () => auditService.run({ lead_id: id! }),
    onSuccess: (result) => { setAuditResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success(`Audit complete — Score: ${result.score.overall_score}/100 (${result.score.category})`); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Audit failed')); },
  });

  const screenshotMutation = useMutation({
    mutationFn: () => screenshotService.capture({ lead_id: id! }),
    onSuccess: (result) => { setScreenshotResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('Screenshots captured successfully'); },
    onError: (err) => {
      const msg = extractApiError(err).message || '';
      if (msg.includes('File size too large') || msg.includes('upload') || msg.includes('Cloudinary')) {
        toast.error('Screenshot was captured, but the image could not be optimized for upload. Please retry.');
      } else {
        toast.error(getApiErrorMessage(err, 'Screenshot capture failed'));
      }
    },
  });

  const outreachMutation = useMutation({
    mutationFn: () => outreachService.generate({ lead_id: id! }),
    onSuccess: (result) => { setOutreachResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('AI Outreach generated successfully'); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Outreach generation failed')); },
  });

  const copyToClipboard = async (text: string, label: string) => {
    try { await navigator.clipboard.writeText(text); toast.success(`${label} copied to clipboard`); }
    catch { toast.error('Failed to copy'); }
  };

  const mutations = {
    screenshot: screenshotMutation, analysis: analysisMutation, audit: auditMutation,
    generation: generationMutation, outreach: outreachMutation,
  };
  const activeStage = getActiveStage(screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations);

  /* ── Loading ──────────────────────────────────────────────── */
  if (isLoading) {
    return (
      <div className="space-y-6 lf-fade-in">
        <Skeleton variant="rounded" width={200} height={24} />
        <PremiumCard variant="featured" innerClassName="p-10">
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="flex-1 space-y-4"><Skeleton variant="text" width={120} height={14} /><Skeleton variant="text" width="60%" height={48} /><Skeleton variant="text" width="80%" height={14} /></div>
            <div className="text-right"><Skeleton variant="text" width={100} height={100} /></div>
          </div>
        </PremiumCard>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} variant="rounded" width="100%" height={200} />)}</div>
          <div className="space-y-6"><Skeleton variant="rounded" width="100%" height={300} /></div>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <EmptyState
        title="Lead not found"
        message="This lead does not exist or has been removed."
        action={<Button variant="outline" onClick={() => navigate('/projects')}>Back to Projects</Button>}
      />
    );
  }

  return (
    <div className="space-y-8 lf-fade-in">
      {/* ═══════════════════════════════════════════════════════════
         TOP IDENTITY AREA
      ════════════════════════════════════════════════════════════ */}
      <PremiumCard variant="featured" innerClassName="relative overflow-hidden p-8 lg:p-10">
        <div className="absolute -top-32 -right-32 w-96 h-96 rounded-full bg-[rgba(14,165,233,0.06)] blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-32 -left-32 w-96 h-96 rounded-full bg-[rgba(139,92,246,0.05)] blur-[80px] pointer-events-none" />
        <div className="absolute inset-0 pointer-events-none opacity-[0.015]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px), repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(255,255,255,0.02) 39px, rgba(255,255,255,0.02) 40px)' }} />
        <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.08) 2px, rgba(255,255,255,0.08) 4px)' }} />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-6">
            <Button variant="ghost" size="sm" onClick={() => navigate('/projects')} className="text-[var(--color-text-muted)] hover:text-white">
              <ArrowLeft className="size-4 mr-1" /> Pipeline
            </Button>
          </div>

          <div className="flex flex-col lg:flex-row justify-between gap-8">
            {/* Left: Identity */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <Badge tone={statusTone[lead.status] ?? 'muted'} className="font-mono text-[10px]">{lead.status.replace('_', ' ')}</Badge>
                <Badge tone="info" className="font-mono text-[10px]">{lead.industry || 'General'}</Badge>
                {lead.rating != null && (
                  <Badge tone={lead.rating >= 4 ? 'success' : lead.rating >= 3 ? 'warning' : 'muted'} className="font-mono text-[10px]">
                    <Star size={10} className="mr-1 fill-current" />{lead.rating.toFixed(1)}
                  </Badge>
                )}
              </div>

              <h1 className="text-[clamp(2rem,3vw,2.5rem)] font-extrabold tracking-tight text-white mb-4">{lead.name}</h1>

              <div className="flex flex-wrap gap-x-6 gap-y-2 text-[13px] font-mono text-[var(--color-text-secondary)]">
                {lead.industry && <span className="flex items-center gap-1.5"><Building size={13} className="text-[#0ea5e9]" />{lead.industry}</span>}
                {(lead.city || lead.country) && <span className="flex items-center gap-1.5"><MapPin size={13} className="text-[#0ea5e9]" />{lead.city}{lead.city && lead.country ? ', ' : ''}{lead.country}</span>}
                {lead.website && (
                  <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1.5 text-[#0ea5e9] hover:underline">
                    <Globe size={13} />{lead.website.replace(/^https?:\/\//, '')}
                  </a>
                )}
                {lead.phone && (
                  <a href={`tel:${lead.phone}`} className="flex items-center gap-1.5 hover:text-[#0ea5e9]"><Phone size={13} />{lead.phone}</a>
                )}
              </div>

              {lead.address && (
                <p className="text-[12px] font-mono text-[var(--color-text-muted)] mt-2">{lead.address}</p>
              )}

              {/* Primary next action button */}
              <div className="mt-6">
                {activeStage ? (
                  <Button
                    variant="neon"
                    onClick={() => {
                      if (activeStage.id === 'screenshot') screenshotMutation.mutate();
                      else if (activeStage.id === 'analysis') analysisMutation.mutate();
                      else if (activeStage.id === 'audit') auditMutation.mutate();
                      else if (activeStage.id === 'generation') {
                        if (existingWebsite) navigate(`/preview/${existingWebsite.id}`);
                        else generationMutation.mutate();
                      }
                      else if (activeStage.id === 'outreach') outreachMutation.mutate();
                    }}
                    loading={
                      (activeStage.id === 'screenshot' && screenshotMutation.isPending) ||
                      (activeStage.id === 'analysis' && analysisMutation.isPending) ||
                      (activeStage.id === 'audit' && auditMutation.isPending) ||
                      (activeStage.id === 'generation' && generationMutation.isPending) ||
                      (activeStage.id === 'outreach' && outreachMutation.isPending)
                    }
                    leftIcon={<activeStage.icon size={15} />}
                  >
                    {activeStage.id === 'generation' && existingWebsite ? 'View Website' : `Run ${activeStage.label}`}
                  </Button>
                ) : (
                  <Button variant="glass" disabled><CheckCircle size={15} /> All Stages Complete</Button>
                )}
              </div>
            </div>

            {/* Right: Score + metrics */}
            <div className="flex flex-col items-center lg:items-end gap-4 shrink-0">
              <ScoreGauge score={lead.score?.overall_score ?? 0} size={120} strokeWidth={8} label="Audit Score" />
              <div className="flex items-center gap-4 text-center">
                <div>
                  <p className="text-[22px] font-bold text-white"><AnimatedCounter value={lead.reviews_count ?? 0} /></p>
                  <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Reviews</p>
                </div>
                <div className="w-px h-8 bg-[var(--color-border)]" />
                <div>
                  <p className="text-[22px] font-bold text-white">{formatRelative(lead.updated_at)}</p>
                  <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Updated</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PremiumCard>

      {/* ═══════════════════════════════════════════════════════════
         WORKFLOW RAIL
      ════════════════════════════════════════════════════════════ */}
      <PremiumCard innerClassName="p-4 lg:p-5 overflow-hidden">
        <div className="hidden lg:flex items-center justify-between gap-0">
          {STAGES.map((stage, i) => {
            const state = getStageState(stage.id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations);
            const isActive = state === 'active';
            const isCompleted = state === 'completed';
            const isFailed = state === 'failed';
            const isPendingS = state === 'pending' || state === 'blocked';
            const StageIcon = stage.icon;
            return (
              <div key={stage.id} className="flex items-center flex-1">
                {/* Stage node */}
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className={cn(
                      'size-11 rounded-xl flex items-center justify-center transition-all duration-300 border-2 relative',
                      isActive && 'border-[#0ea5e9] bg-[rgba(14,165,233,0.12)] shadow-[0_0_20px_rgba(14,165,233,0.3)]',
                      isCompleted && 'border-emerald-500/40 bg-emerald-500/10 shadow-[0_0_10px_rgba(16,185,129,0.2)]',
                      isFailed && 'border-red-500/40 bg-red-500/10',
                      isPendingS && 'border-[var(--color-border)] bg-[var(--color-surface-hover)] opacity-50',
                    )}
                  >
                    {isActive && (
                      <div className="absolute inset-0 rounded-xl pointer-events-none" style={{ background: 'conic-gradient(from var(--angle), #00f5a0, #00d9ff, #2563ff, #7c3aed, #ff2bd6, #00f5a0)', animation: 'lf-conic-spin 3s linear infinite', WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', WebkitMaskComposite: 'xor', maskComposite: 'exclude', padding: '2px' }} />
                    )}
                    <StageIcon size={16} className={cn(
                      isActive && 'text-[#0ea5e9] drop-shadow-[0_0_8px_rgba(14,165,233,0.6)]',
                      isCompleted && 'text-emerald-400',
                      isFailed && 'text-red-400',
                      isPendingS && 'text-[var(--color-text-muted)]',
                    )} />
                  </div>
                  <span className={cn(
                    'text-[9px] font-mono uppercase tracking-wider whitespace-nowrap',
                    isActive && 'text-[#0ea5e9] font-bold',
                    isCompleted && 'text-emerald-400',
                    isFailed && 'text-red-400',
                    isPendingS && 'text-[var(--color-text-muted)]',
                  )}>{stage.label}</span>
                </div>
                {/* Connector line */}
                {i < STAGES.length - 1 && (
                  <div className={cn(
                    'flex-1 h-0.5 mx-2 rounded-full transition-all duration-300',
                    getStageState(STAGES[i + 1].id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations) === 'completed' || (getStageState(STAGES[i + 1].id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations) === 'active' && isCompleted)
                      ? 'bg-emerald-500/50'
                      : getStageState(STAGES[i + 1].id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations) === 'failed'
                        ? 'bg-red-500/50'
                        : 'bg-[var(--color-border)]',
                  )} />
                )}
              </div>
            );
          })}
        </div>

        {/* Mobile vertical rail */}
        <div className="flex lg:hidden flex-col gap-0">
          {STAGES.map((stage, i) => {
            const state = getStageState(stage.id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations);
            const isActive = state === 'active';
            const isCompleted = state === 'completed';
            const isFailed = state === 'failed';
            const isPendingS = state === 'pending' || state === 'blocked';
            const StageIcon = stage.icon;
            return (
              <div key={stage.id} className="flex items-stretch gap-3">
                <div className="flex flex-col items-center">
                  <div className={cn(
                    'size-9 rounded-lg flex items-center justify-center border-2 transition-all shrink-0',
                    isActive && 'border-[#0ea5e9] bg-[rgba(14,165,233,0.12)] shadow-[0_0_12px_rgba(14,165,233,0.3)]',
                    isCompleted && 'border-emerald-500/40 bg-emerald-500/10',
                    isFailed && 'border-red-500/40 bg-red-500/10',
                    isPendingS && 'border-[var(--color-border)] bg-[var(--color-surface-hover)] opacity-50',
                  )}>
                    <StageIcon size={14} className={cn(isActive && 'text-[#0ea5e9]', isCompleted && 'text-emerald-400', isFailed && 'text-red-400', isPendingS && 'text-[var(--color-text-muted)]')} />
                  </div>
                  {i < STAGES.length - 1 && (
                    <div className={cn(
                      'w-0.5 flex-1 min-h-[16px] my-1',
                      getStageState(STAGES[i + 1].id, screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations) === 'completed' ? 'bg-emerald-500/50' : 'bg-[var(--color-border)]',
                    )} />
                  )}
                </div>
                <div className={cn(
                  'py-1.5 flex-1',
                  isActive && 'text-[#0ea5e9]', isCompleted && 'text-emerald-400', isFailed && 'text-red-400', isPendingS && 'text-[var(--color-text-muted)]',
                )}>
                  <p className={cn('text-[12px] font-mono font-semibold', isActive && 'text-white')}>{stage.label}</p>
                  <p className="text-[10px] font-mono opacity-60">
                    {isActive ? 'In progress...' : isCompleted ? 'Complete' : isFailed ? 'Failed' : 'Pending'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </PremiumCard>

      {/* ═══════════════════════════════════════════════════════════
         COMMAND-CENTER LAYOUT
      ════════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* ─── MAIN COLUMN ─────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-6">

          {/* Screenshot Gallery */}
          <PremiumCard innerClassName="p-6">
            <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
              <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
                <Camera size={13} className="text-[#06b6d4]" /> Visual Capture
              </h3>
              <div className="flex items-center gap-2">
                {screenshotResult && <Badge tone="success" className="text-[9px]">Captured</Badge>}
                <Button size="xs" variant={screenshotResult ? 'outline' : 'brand'} loading={screenshotMutation.isPending} onClick={() => screenshotMutation.mutate()}>
                  {screenshotResult ? 'Recapture' : 'Capture'}
                </Button>
              </div>
            </div>

            {screenshotMutation.isPending ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <div className="relative size-12">
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#0ea5e9] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '1s' }} />
                  <div className="absolute inset-2 rounded-full border border-transparent border-b-[#06b6d4] border-l-[#06b6d4] animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
                </div>
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">Capturing screenshots...</p>
              </div>
            ) : screenshotResult?.desktop_url || screenshotResult?.mobile_url ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {screenshotResult.desktop_url && (
                  <div className="group relative">
                    <div className="rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface-hover)]">
                      <div className="flex items-center gap-2 px-3 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                        <div className="flex gap-1"><span className="size-2 rounded-full bg-red-500/60" /><span className="size-2 rounded-full bg-amber-500/60" /><span className="size-2 rounded-full bg-emerald-500/60" /></div>
                        <span className="text-[9px] font-mono text-[var(--color-text-muted)]">Desktop</span>
                      </div>
                      <img src={screenshotResult.desktop_url} alt="Desktop screenshot" className="w-full object-cover cursor-pointer" onClick={() => setFullScreenImg(screenshotResult.desktop_url!)} />
                    </div>
                    <button onClick={() => setFullScreenImg(screenshotResult.desktop_url!)} className="absolute top-3 right-3 size-7 rounded-md bg-black/50 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all text-white"><Maximize2 size={12} /></button>
                  </div>
                )}
                {screenshotResult.mobile_url && (
                  <div className="group relative">
                    <div className="rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface-hover)]">
                      <div className="flex items-center gap-2 px-3 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                        <div className="flex gap-1"><span className="size-2 rounded-full bg-red-500/60" /><span className="size-2 rounded-full bg-amber-500/60" /><span className="size-2 rounded-full bg-emerald-500/60" /></div>
                        <span className="text-[9px] font-mono text-[var(--color-text-muted)]">Mobile</span>
                      </div>
                      <img src={screenshotResult.mobile_url} alt="Mobile screenshot" className="w-full object-cover cursor-pointer" onClick={() => setFullScreenImg(screenshotResult.mobile_url!)} />
                    </div>
                    <button onClick={() => setFullScreenImg(screenshotResult.mobile_url!)} className="absolute top-3 right-3 size-7 rounded-md bg-black/50 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all text-white"><Maximize2 size={12} /></button>
                  </div>
                )}
              </div>
            ) : screenshotMutation.error ? (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <AlertTriangle size={28} className="text-red-400" />
                <p className="text-[13px] text-red-400 font-medium">Capture failed</p>
                <p className="text-[11px] font-mono text-[var(--color-text-muted)]">{getApiErrorMessage(screenshotMutation.error)}</p>
                <Button size="sm" variant="outline" onClick={() => screenshotMutation.mutate()}>Retry</Button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <Camera size={28} className="text-[var(--color-text-muted)]" />
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No screenshots captured yet. Click <span className="text-[#0ea5e9]">Capture</span> to take website screenshots.</p>
              </div>
            )}
          </PremiumCard>

          {/* Website Analysis */}
          <PremiumCard innerClassName="p-6">
            <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
              <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
                <Search size={13} className="text-[#8b5cf6]" /> Technical Analysis
              </h3>
              <div className="flex items-center gap-2">
                {analysisResult && <Badge tone="success" className="text-[9px]">Analyzed</Badge>}
                <Button size="xs" variant={analysisResult ? 'outline' : 'brand'} loading={analysisMutation.isPending} onClick={() => analysisMutation.mutate()}>
                  {analysisResult ? 'Reanalyze' : 'Analyze'}
                </Button>
              </div>
            </div>

            {analysisMutation.isPending ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <div className="relative size-12">
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#8b5cf6] border-r-[#06b6d4] animate-spin" style={{ animationDuration: '1s' }} />
                  <div className="absolute inset-2 rounded-full border border-transparent border-b-[#0ea5e9] border-l-[#8b5cf6] animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
                </div>
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">Analyzing website structure...</p>
              </div>
            ) : analysisResult ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-center">
                    <p className="text-[22px] font-bold text-white">{analysisResult.http_status_code ?? '—'}</p>
                    <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">HTTP Status</p>
                  </div>
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-center">
                    <p className="text-[22px] font-bold text-[#0ea5e9]">{analysisResult.response_time_ms ?? '—'}ms</p>
                    <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Response Time</p>
                  </div>
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-center">
                    <p className="text-[22px] font-bold text-white">{analysisResult.html_size_kb?.toFixed(1) ?? '—'} KB</p>
                    <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Page Weight</p>
                  </div>
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-center">
                    <p className={cn('text-[22px] font-bold', analysisResult.https_enabled ? 'text-emerald-400' : 'text-red-400')}>
                      {analysisResult.https_enabled ? 'HTTPS' : 'HTTP'}
                    </p>
                    <p className="text-[9px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">Security</p>
                  </div>
                </div>

                <div className="grid grid-cols-5 gap-3">
                  <div className="text-center p-2"><p className="text-[18px] font-bold text-white">{analysisResult.h1_count}</p><p className="text-[9px] font-mono text-[var(--color-text-muted)]">H1</p></div>
                  <div className="text-center p-2"><p className="text-[18px] font-bold text-white">{analysisResult.h2_count}</p><p className="text-[9px] font-mono text-[var(--color-text-muted)]">H2</p></div>
                  <div className="text-center p-2"><p className="text-[18px] font-bold text-white">{analysisResult.total_paragraphs}</p><p className="text-[9px] font-mono text-[var(--color-text-muted)]">Paras</p></div>
                  <div className="text-center p-2"><p className="text-[18px] font-bold text-white">{analysisResult.total_images}</p><p className="text-[9px] font-mono text-[var(--color-text-muted)]">Images</p></div>
                  <div className="text-center p-2"><p className="text-[18px] font-bold text-white">{analysisResult.total_forms}</p><p className="text-[9px] font-mono text-[var(--color-text-muted)]">Forms</p></div>
                </div>

                {lead.website && (
                  <div className="pt-3 border-t border-[var(--color-border)]">
                    <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noopener noreferrer" className="text-[12px] text-[#0ea5e9] hover:underline flex items-center gap-1.5 font-mono">
                      <ExternalLink size={12} /> Visit {lead.website.replace(/^https?:\/\//, '')}
                    </a>
                  </div>
                )}
              </div>
            ) : analysisMutation.error ? (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <AlertTriangle size={28} className="text-red-400" />
                <p className="text-[13px] text-red-400 font-medium">Analysis failed</p>
                <Button size="sm" variant="outline" onClick={() => analysisMutation.mutate()}>Retry</Button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <Search size={28} className="text-[var(--color-text-muted)]" />
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No analysis data. Run an analysis to inspect website structure.</p>
              </div>
            )}
          </PremiumCard>

          {/* Audit Score Breakdown */}
          <PremiumCard innerClassName="p-6">
            <div className="flex items-center justify-between mb-5 border-b border-[var(--color-border)] pb-3">
              <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
                <Shield size={13} className="text-[#f59e0b]" /> AI Intelligence Audit
              </h3>
              <div className="flex items-center gap-2">
                {auditResult && <Badge tone={auditResult.score.category === 'Hot Lead' ? 'success' : auditResult.score.category === 'Warm Lead' ? 'warning' : 'muted'} className="text-[9px]">{auditResult.score.category}</Badge>}
                <Button size="xs" variant={auditResult ? 'outline' : 'brand'} loading={auditMutation.isPending} onClick={() => auditMutation.mutate()}>
                  {auditResult ? 'Re-audit' : 'Run Audit'}
                </Button>
              </div>
            </div>

            {auditMutation.isPending ? (
              <div className="flex flex-col items-center justify-center py-12 gap-4">
                <div className="relative size-12">
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#f59e0b] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '1s' }} />
                  <div className="absolute inset-2 rounded-full border border-transparent border-b-[#0ea5e9] border-l-[#f59e0b] animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
                </div>
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">Running AI audit...</p>
              </div>
            ) : auditResult ? (
              <div className="space-y-6">
                {/* Score bars */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                  <ScoreBar label="Overall" value={auditResult.score.overall_score} color="#8b5cf6" />
                  <ScoreBar label="SEO" value={auditResult.score.seo_score} />
                  <ScoreBar label="UX" value={auditResult.score.ux_score} />
                  <ScoreBar label="Branding" value={auditResult.score.branding_score} />
                  <ScoreBar label="Trust" value={auditResult.score.trust_score} />
                  <ScoreBar label="Conversion" value={auditResult.score.conversion_score} />
                </div>

                {/* Business Summary / Verdict */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-[var(--color-border)]">
                  {auditResult.audit && typeof auditResult.audit === 'object' && 'Business Summary' in auditResult.audit && (
                    <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]">
                      <h4 className="text-[10px] font-mono uppercase tracking-wider text-[#0ea5e9] mb-2">Business Profile</h4>
                      <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed">{String(auditResult.audit['Business Summary'])}</p>
                    </div>
                  )}
                  {auditResult.audit && typeof auditResult.audit === 'object' && 'Overall Summary' in auditResult.audit && (
                    <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]">
                      <h4 className="text-[10px] font-mono uppercase tracking-wider text-[#f59e0b] mb-2">Audit Verdict</h4>
                      <p className="text-[13px] text-[var(--color-text-secondary)] leading-relaxed">{String(auditResult.audit['Overall Summary'])}</p>
                    </div>
                  )}
                </div>

                {/* Weaknesses */}
                {auditResult.audit && typeof auditResult.audit === 'object' && 'Top Weaknesses' in auditResult.audit && Array.isArray(auditResult.audit['Top Weaknesses']) && (
                  <div className="pt-4 border-t border-[var(--color-border)]">
                    <h4 className="text-[10px] font-mono uppercase tracking-wider text-red-400 mb-4 flex items-center gap-2">
                      <AlertTriangle size={12} /> Weaknesses &amp; Recommendations
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(auditResult.audit['Top Weaknesses'] as Array<string | { title?: string; evidence?: string; impact?: string; recommendation?: string }>).map((w, i) => {
                        const weakness = typeof w === 'string' ? { title: w } : w;
                        return (
                          <div key={i} className="p-4 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/15">
                            <p className="text-[13px] font-bold text-white mb-2 flex items-start gap-2">
                              <AlertTriangle size={13} className="text-red-400 shrink-0 mt-0.5" />{weakness.title}
                            </p>
                            {weakness.impact && <p className="text-[11px] text-[var(--color-text-muted)] mb-2">{weakness.impact}</p>}
                            {weakness.recommendation && (
                              <p className="text-[11px] text-emerald-400 font-mono flex items-start gap-1.5"><CheckCircle size={12} className="shrink-0 mt-0.5" />{weakness.recommendation}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            ) : auditMutation.error ? (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <AlertTriangle size={28} className="text-red-400" />
                <p className="text-[13px] text-red-400 font-medium">Audit failed</p>
                <Button size="sm" variant="outline" onClick={() => auditMutation.mutate()}>Retry</Button>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10 gap-3 text-center">
                <Shield size={28} className="text-[var(--color-text-muted)]" />
                <p className="text-[12px] font-mono text-[var(--color-text-muted)]">No audit data. Run an AI audit to score and analyze this lead.</p>
              </div>
            )}
          </PremiumCard>
        </div>

        {/* ─── ACTION COLUMN (sticky) ─────────────────────────── */}
        <div className="space-y-6 lg:sticky lg:top-24">
          {/* Quick Actions */}
          <PremiumCard innerClassName="p-5">
            <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white mb-4 border-b border-[var(--color-border)] pb-3 flex items-center gap-2">
              <Zap size={13} className="text-[#06b6d4]" /> Workflow Actions
            </h3>
            <div className="space-y-2.5">
              <ActionButton icon={Camera} label="Screenshot" active={!!screenshotResult} loading={screenshotMutation.isPending} onClick={() => screenshotMutation.mutate()} />
              <ActionButton icon={Search} label="Analyze Website" active={!!analysisResult} loading={analysisMutation.isPending} onClick={() => analysisMutation.mutate()} />
              <ActionButton icon={Shield} label="AI Audit" active={!!auditResult} loading={auditMutation.isPending} onClick={() => auditMutation.mutate()} />
              <ActionButton
                icon={Zap}
                label={existingWebsite ? 'View Website' : 'Generate Website'}
                active={!!existingWebsite}
                loading={generationMutation.isPending}
                onClick={() => { if (existingWebsite) navigate(`/preview/${existingWebsite.id}`); else generationMutation.mutate(); }}
                variant={existingWebsite ? 'preview' : 'primary'}
              />
              {existingWebsite?.package_id && (
                <ActionButton icon={Download} label="Download Package" onClick={() => generationService.downloadPackage(existingWebsite.id)} />
              )}
              <ActionButton icon={Send} label="Generate Outreach" active={!!outreachResult} loading={outreachMutation.isPending} onClick={() => outreachMutation.mutate()} />
            </div>
          </PremiumCard>

          {/* Outreach Content */}
          <PremiumCard innerClassName="p-5">
            <div className="flex items-center justify-between mb-4 border-b border-[var(--color-border)] pb-3">
              <h3 className="text-[11px] font-mono uppercase tracking-[0.2em] text-white flex items-center gap-2">
                <Send size={13} className="text-[#22d3ee]" /> Outreach
              </h3>
              {outreachResult && <Badge tone="success" className="text-[9px]">Generated</Badge>}
            </div>

            {outreachMutation.isPending ? (
              <div className="flex flex-col items-center justify-center py-8 gap-3">
                <div className="relative size-10">
                  <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#22d3ee] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '1s' }} />
                </div>
                <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Generating outreach...</p>
              </div>
            ) : outreachMutation.error ? (
              <div className="flex flex-col items-center py-6 gap-2 text-center">
                <AlertTriangle size={20} className="text-red-400" />
                <p className="text-[11px] text-red-400">Generation failed</p>
                <Button size="xs" variant="outline" onClick={() => outreachMutation.mutate()}>Retry</Button>
              </div>
            ) : outreachResult ? (
              <div className="space-y-4 max-h-[500px] overflow-y-auto lf-thin-scroll">
                {outreachResult.email_subject && (
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                    <p className="text-[9px] font-mono uppercase tracking-wider text-[var(--color-text-muted)] mb-1">Subject</p>
                    <p className="text-[12px] text-white font-medium">{outreachResult.email_subject}</p>
                  </div>
                )}
                {outreachResult.cold_email && (
                  <OutreachBlock label="Cold Email" content={outreachResult.cold_email} color="#10b981" onCopy={() => copyToClipboard(outreachResult.cold_email!, 'Cold email')} />
                )}
                {outreachResult.linkedin_message && (
                  <OutreachBlock label="LinkedIn" content={outreachResult.linkedin_message} color="#0ea5e9" onCopy={() => copyToClipboard(outreachResult.linkedin_message!, 'LinkedIn message')} />
                )}
                {outreachResult.followup_email && (
                  <OutreachBlock label="Follow-up" content={outreachResult.followup_email} color="#8b5cf6" onCopy={() => copyToClipboard(outreachResult.followup_email!, 'Follow-up email')} />
                )}
                {outreachResult.whatsapp_message && (
                  <OutreachBlock label="WhatsApp" content={outreachResult.whatsapp_message} color="#22c55e" onCopy={() => copyToClipboard(outreachResult.whatsapp_message!, 'WhatsApp message')} />
                )}
                {outreachResult.short_cta && (
                  <div className="p-3 rounded-[var(--radius-md)] bg-emerald-500/5 border border-emerald-500/15">
                    <p className="text-[9px] font-mono uppercase tracking-wider text-emerald-400 mb-1">CTA</p>
                    <p className="text-[12px] text-emerald-300">{outreachResult.short_cta}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
                <Send size={24} className="text-[var(--color-text-muted)]" />
                <p className="text-[11px] font-mono text-[var(--color-text-muted)]">No outreach generated yet. Click <span className="text-[#22d3ee]">Generate Outreach</span> to create AI-powered messaging.</p>
              </div>
            )}
          </PremiumCard>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
         FULL-SCREEN SCREENSHOT OVERLAY
      ════════════════════════════════════════════════════════════ */}
      {fullScreenImg && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-xl flex items-center justify-center" onClick={() => setFullScreenImg(null)}>
          <button onClick={() => setFullScreenImg(null)} className="absolute top-6 right-6 size-10 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center text-white hover:bg-white/20 transition-all"><X size={20} /></button>
          <img src={fullScreenImg} alt="Full size screenshot" className="max-w-[95vw] max-h-[95vh] object-contain rounded-[var(--radius-lg)]" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
    </div>
  );
}

/* ── Action button sub-component ─────────────────────────────── */
function ActionButton({ icon: Icon, label, active, loading, onClick, variant }: {
  icon: typeof Camera; label: string; active?: boolean; loading?: boolean; onClick: () => void; variant?: 'primary' | 'preview';
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={cn(
        'w-full flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)] transition-all text-left',
        variant === 'preview'
          ? 'bg-gradient-to-r from-[#8b5cf6]/20 to-[#d946ef]/20 border border-[#8b5cf6]/30 text-white hover:from-[#8b5cf6]/30 hover:to-[#d946ef]/30'
          : variant === 'primary'
            ? 'bg-gradient-to-r from-[#0ea5e9]/20 to-[#2563eb]/20 border border-[#0ea5e9]/30 text-white hover:from-[#0ea5e9]/30 hover:to-[#2563eb]/30'
            : active
              ? 'bg-emerald-500/10 border border-emerald-500/25 text-white hover:bg-emerald-500/15'
              : 'bg-[var(--color-surface-hover)] border border-transparent text-[var(--color-text-secondary)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] hover:text-white',
      )}
    >
      <div className={cn(
        'size-8 rounded-[var(--radius-sm)] flex items-center justify-center shrink-0',
        variant === 'preview' ? 'bg-[#8b5cf6]/20' : active ? 'bg-emerald-500/15' : 'bg-[var(--color-glass)]',
      )}>
        <Icon size={14} className={cn(
          variant === 'preview' && 'text-[#d946ef]',
          active && !variant && 'text-emerald-400',
          !active && !variant && 'text-[var(--color-text-muted)]',
        )} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn(
          'text-[12px] font-semibold truncate',
          active && 'text-emerald-400',
        )}>{label}</p>
        {active && !variant && <p className="text-[9px] font-mono text-emerald-400/60">Complete</p>}
      </div>
      {loading && <Loader2 size={14} className="lf-spin text-[var(--color-text-muted)]" />}
      {!loading && variant === 'primary' && <ChevronRight size={14} className="text-[#0ea5e9]" />}
      {!loading && variant === 'preview' && <ExternalLink size={14} className="text-[#d946ef]" />}
    </button>
  );
}

/* ── Outreach content block sub-component ────────────────────── */
function OutreachBlock({ label, content, color, onCopy }: { label: string; content: string; color: string; onCopy: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const truncated = content.length > 280;
  return (
    <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[9px] font-mono uppercase tracking-wider" style={{ color }}>{label}</span>
        <div className="flex items-center gap-1.5">
          <button onClick={onCopy} className="size-6 rounded-md bg-[var(--color-glass)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all"><Copy size={10} /></button>
          {truncated && (
            <button onClick={() => setExpanded(!expanded)} className="size-6 rounded-md bg-[var(--color-glass)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all">
              {expanded ? <X size={10} /> : <ChevronDown size={10} />}
            </button>
          )}
        </div>
      </div>
      <p className="text-[11px] text-[var(--color-text-secondary)] whitespace-pre-wrap leading-relaxed">
        {truncated && !expanded ? `${content.slice(0, 280)}...` : content}
      </p>
    </div>
  );
}
