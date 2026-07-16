import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe, MapPin, Phone, Building, Shield, AlertTriangle, CheckCircle, Search, Camera, Send, Copy, ExternalLink, ChevronDown, Eye, Download, X, Maximize2, Rocket } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { ScoreGauge } from '@/components/ScoreGauge';
import { projectsService, auditService, analysisService, screenshotService, outreachService, generationService } from '@/services/services';
import { getApiErrorMessage } from '@/services/apiClient';
import { usePreviewStore } from '@/store';
import { useGenerationJob } from '@/hooks/useGenerationJob';
import { formatRelative, cn } from '@/utils';
import { toast } from 'sonner';
import type { AuditAndScoreResult, WebsiteAnalysisResponse, CaptureScreenshotResponse, OutreachResponse } from '@/types';

/* ── Constants ───────────────────────────────────────────────── */
const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info', SCRAPED: 'brand', ANALYZED: 'warning', OUTREACH_READY: 'success', CONTACTED: 'brand', CLOSED: 'success',
};

type StageId = 'lead' | 'screenshot' | 'analysis' | 'audit' | 'generation' | 'preview' | 'package' | 'outreach';
type StageState = 'completed' | 'active' | 'pending' | 'blocked' | 'failed';
type TabId = 'overview' | 'audit' | 'redesign' | 'website';

const STAGES: { id: StageId; label: string }[] = [
  { id: 'lead', label: 'Lead' },
  { id: 'screenshot', label: 'Screenshot' },
  { id: 'analysis', label: 'Analysis' },
  { id: 'audit', label: 'Audit' },
  { id: 'generation', label: 'Generation' },
  { id: 'preview', label: 'Preview' },
  { id: 'package', label: 'Package' },
  { id: 'outreach', label: 'Outreach' },
];

/* ── Stage logic ─────────────────────────────────────────────── */
function stageDirect(
  sid: StageId,
  screenshot: CaptureScreenshotResponse | null,
  analysis: WebsiteAnalysisResponse | null,
  audit: AuditAndScoreResult | null,
  website: unknown | null,
  outreach: OutreachResponse | null,
  mutations: Record<string, { isPending: boolean; error: unknown }>,
): StageState {
  if (sid === 'lead') return 'completed';
  const err = mutations[sid]?.error;
  if (err) return 'failed';
  if (mutations[sid]?.isPending) return 'active';
  switch (sid) {
    case 'screenshot': return (screenshot?.desktop_url || screenshot?.mobile_url) ? 'completed' : 'pending';
    case 'analysis': return analysis ? 'completed' : 'pending';
    case 'audit': return audit ? 'completed' : 'pending';
    case 'generation': return website ? 'completed' : 'pending';
    case 'preview': return website ? 'completed' : 'pending';
    case 'package': return (website && typeof website === 'object' && 'package_id' in website) ? 'completed' : 'pending';
    case 'outreach': return outreach ? 'completed' : 'pending';
    default: return 'pending';
  }
}

function getActiveStage(
  screenshot: CaptureScreenshotResponse | null,
  analysis: WebsiteAnalysisResponse | null,
  audit: AuditAndScoreResult | null,
  website: unknown | null,
  outreach: OutreachResponse | null,
  mutations: Record<string, { isPending: boolean; error: unknown }>,
): { id: StageId; label: string } | null {
  const states = STAGES.map(s => stageDirect(s.id, screenshot, analysis, audit, website, outreach, mutations));
  for (let i = 0; i < STAGES.length; i++) {
    if (states[i] === 'completed') continue;
    if (states[i] === 'active' || states[i] === 'pending') return STAGES[i];
    break;
  }
  return null;
}

/* ── Score bar ───────────────────────────────────────────────── */
function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, value));
  const tone = pct >= 80 ? 'success' : pct >= 60 ? 'warning' : 'danger';
  const barClass = tone === 'success' ? 'bg-[var(--color-success)]' : tone === 'warning' ? 'bg-[var(--color-warning)]' : 'bg-[var(--color-danger)]';
  const textClass = tone === 'success' ? 'text-[var(--color-success)]' : tone === 'warning' ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]';
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[11px]">
        <span className="text-[var(--color-text-secondary)]">{label}</span>
        <span className={cn('font-semibold tabular-nums', textClass)}>{Math.round(pct)}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--color-surface-hover)] overflow-hidden">
        <div className={cn('h-full rounded-full transition-all duration-500', barClass)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ══════════════════════════════════════════════════════════════ */
export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [activeTab, setActiveTab] = useState<TabId>('overview');
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
      if (lead.outreach) setOutreachResult(lead.outreach);
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

  const { jobResult, jobError, isRunning: isGenerationRunning, generate } = useGenerationJob({
    leadId: id!,
    onSuccess: (websiteId, htmlContent) => {
      if (htmlContent) setHtmlContent(htmlContent);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      queryClient.invalidateQueries({ queryKey: ['generated-website-latest', id] });
      toast.success('Website generated successfully');
    },
    onError: (msg) => { toast.error(msg); },
  });

  const analysisMutation = useMutation({
    mutationFn: () => analysisService.analyzeWebsite(id!),
    onSuccess: (result) => { setAnalysisResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('Website analyzed successfully'); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Analysis failed')); },
  });

  const auditMutation = useMutation({
    mutationFn: () => auditService.run({ lead_id: id! }),
    onSuccess: (result) => { setAuditResult(result); toast.success(`Audit complete — Score: ${result.score.overall_score}/100 (${result.score.category})`); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Audit failed')); },
  });

  const screenshotMutation = useMutation({
    mutationFn: () => screenshotService.capture({ lead_id: id! }),
    onSuccess: (result) => { setScreenshotResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('Screenshots captured successfully'); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Screenshot capture failed')); },
  });

  const outreachMutation = useMutation({
    mutationFn: () => outreachService.generate({ lead_id: id! }),
    onSuccess: (result) => { setOutreachResult(result); queryClient.invalidateQueries({ queryKey: ['lead', id] }); toast.success('Outreach generated successfully'); },
    onError: (err) => { toast.error(getApiErrorMessage(err, 'Outreach generation failed')); },
  });

  const copyToClipboard = async (text: string, label: string) => {
    try { await navigator.clipboard.writeText(text); toast.success(`${label} copied`); }
    catch { toast.error('Failed to copy'); }
  };

  const mutations = {
    screenshot: screenshotMutation, analysis: analysisMutation, audit: auditMutation,
    generation: { isPending: isGenerationRunning, error: jobError },
    outreach: outreachMutation,
  };
  const activeStage = getActiveStage(screenshotResult, analysisResult, auditResult, existingWebsite, outreachResult, mutations);

  /* ── Loading ──────────────────────────────────────────────── */
  if (isLoading) {
    return (
      <div className="space-y-6 lf-fade-in">
        <Skeleton variant="text" width={140} height={20} />
        <div className="rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] p-6 space-y-4">
          <Skeleton variant="text" width="40%" height={28} />
          <Skeleton variant="text" width="60%" height={14} />
          <div className="flex gap-2"><Skeleton variant="rounded" width={60} height={22} /><Skeleton variant="rounded" width={80} height={22} /></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} variant="rounded" width="100%" height={180} />)}
          </div>
          <div className="space-y-4">
            <Skeleton variant="rounded" width="100%" height={260} />
          </div>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="lf-fade-in">
        <EmptyState
          title="Lead not found"
          message="This lead does not exist or has been removed."
          action={<Button variant="outline" onClick={() => navigate('/projects')}>Back to Leads</Button>}
        />
      </div>
    );
  }

  const hasAudit = !!auditResult;
  const hasWebsite = !!existingWebsite;
  const hasScreenshot = !!(screenshotResult?.desktop_url || screenshotResult?.mobile_url);

  const tabs: { id: TabId; label: string; show: boolean }[] = [
    { id: 'overview', label: 'Overview', show: true },
    { id: 'audit', label: 'Audit', show: true },
    { id: 'redesign', label: 'Redesign', show: true },
    { id: 'website', label: 'Website', show: hasWebsite },
  ];

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Back nav ──────────────────────────────────────────── */}
      <button
        onClick={() => navigate('/projects')}
        className="inline-flex items-center gap-1.5 text-[12px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        <ArrowLeft size={14} /> Leads
      </button>

      {/* ── Record header ─────────────────────────────────────── */}
      <div className="rounded-[var(--radius-lg)] bg-[var(--color-surface)] border border-[var(--color-border)] p-5 lg:p-6">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2.5 mb-2 flex-wrap">
              <Badge tone={statusTone[lead.status] ?? 'muted'} className="text-[11px]">{lead.status.replace(/_/g, ' ')}</Badge>
              {lead.industry && <Badge tone="neutral" className="text-[11px]">{lead.industry}</Badge>}
              {lead.rating != null && (
                <Badge tone={lead.rating >= 4 ? 'success' : lead.rating >= 3 ? 'warning' : 'muted'} className="text-[11px] tabular-nums">
                  {lead.rating.toFixed(1)}
                </Badge>
              )}
            </div>
            <h1 className="text-[22px] font-bold text-[var(--color-text)] tracking-tight mb-1.5 truncate">{lead.name}</h1>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] text-[var(--color-text-secondary)]">
              {lead.industry && (
                <span className="inline-flex items-center gap-1"><Building size={12} className="text-[var(--color-text-muted)]" />{lead.industry}</span>
              )}
              {(lead.city || lead.country) && (
                <span className="inline-flex items-center gap-1"><MapPin size={12} className="text-[var(--color-text-muted)]" />{lead.city}{lead.city && lead.country ? ', ' : ''}{lead.country}</span>
              )}
              {lead.website && (
                <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-[var(--color-brand)] hover:underline">
                  <Globe size={12} />{lead.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                </a>
              )}
              {lead.phone && (
                <a href={`tel:${lead.phone}`} className="inline-flex items-center gap-1 hover:text-[var(--color-brand)] transition-colors">
                  <Phone size={12} className="text-[var(--color-text-muted)]" />{lead.phone}
                </a>
              )}
            </div>
            {lead.address && (
              <p className="text-[11px] text-[var(--color-text-muted)] mt-1.5">{lead.address}</p>
            )}
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {lead.score?.overall_score != null && (
              <div className="text-right mr-2">
                <p className={cn(
                  'text-[28px] font-bold leading-none tabular-nums',
                  lead.score.overall_score >= 80 ? 'text-[var(--color-success)]' : lead.score.overall_score >= 60 ? 'text-[var(--color-warning)]' : 'text-[var(--color-danger)]',
                )}>{lead.score.overall_score}</p>
                <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">Audit score</p>
              </div>
            )}
            {activeStage ? (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  if (activeStage.id === 'screenshot') screenshotMutation.mutate();
                  else if (activeStage.id === 'analysis') analysisMutation.mutate();
                  else if (activeStage.id === 'audit') auditMutation.mutate();
                  else if (activeStage.id === 'generation') {
                    if (existingWebsite) navigate(`/preview/${existingWebsite.id}`);
                    else generate();
                  }
                  else if (activeStage.id === 'outreach') outreachMutation.mutate();
                }}
                loading={
                  (activeStage.id === 'screenshot' && screenshotMutation.isPending) ||
                  (activeStage.id === 'analysis' && analysisMutation.isPending) ||
                  (activeStage.id === 'audit' && auditMutation.isPending) ||
                  (activeStage.id === 'generation' && isGenerationRunning) ||
                  (activeStage.id === 'outreach' && outreachMutation.isPending)
                }
              >
                {activeStage.id === 'generation' && existingWebsite
                  ? 'View Website'
                  : activeStage.id === 'generation' && isGenerationRunning
                    ? `Generating...`
                    : activeStage.label}
              </Button>
            ) : (
              <Button variant="secondary" size="sm" disabled>All complete</Button>
            )}
          </div>
        </div>
      </div>

      {/* ── Workspace tabs ────────────────────────────────────── */}
      <div className="flex items-center gap-0.5 border-b border-[var(--color-border)] -mb-px">
        {tabs.filter(t => t.show).map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'px-4 py-2.5 text-[13px] font-medium transition-colors duration-[var(--anim-fast)] border-b-2 -mb-px',
              activeTab === tab.id
                ? 'text-[var(--color-text)] border-[var(--color-brand)]'
                : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text-secondary)]',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab content ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-5">
          {activeTab === 'overview' && (
            <>
              {/* Business info */}
              <SectionCard title="Business Information">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                  <InfoRow label="Name" value={lead.name} />
                  <InfoRow label="Industry" value={lead.industry} />
                  <InfoRow label="City" value={lead.city} />
                  <InfoRow label="Country" value={lead.country} />
                  <InfoRow label="Address" value={lead.address} />
                  <InfoRow label="Phone" value={lead.phone} href={lead.phone ? `tel:${lead.phone}` : undefined} />
                  <InfoRow label="Website" value={lead.website?.replace(/^https?:\/\//, '').replace(/\/$/, '')} href={lead.website?.startsWith('http') ? lead.website : lead.website ? `https://${lead.website}` : undefined} isLink />
                </div>
              </SectionCard>

              {/* Lead metadata */}
              <SectionCard title="Lead Details">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-4">
                  <InfoRow label="Status" value={<Badge tone={statusTone[lead.status] ?? 'muted'} className="text-[11px]">{lead.status.replace(/_/g, ' ')}</Badge>} />
                  <InfoRow label="Audit Score" value={lead.score?.overall_score != null ? `${lead.score.overall_score}/100` : null} />
                  <InfoRow label="Reviews" value={lead.reviews_count != null ? String(lead.reviews_count) : null} />
                  <InfoRow label="Created" value={lead.created_at ? formatRelative(lead.created_at) : null} />
                  <InfoRow label="Updated" value={lead.updated_at ? formatRelative(lead.updated_at) : null} />
                </div>
              </SectionCard>

              {/* Screenshot */}
              <SectionCard
                title="Website Screenshot"
                action={
                  <div className="flex items-center gap-2">
                    {hasScreenshot && <Badge tone="success" className="text-[10px]">Captured</Badge>}
                    <Button size="xs" variant={hasScreenshot ? 'outline' : 'primary'} loading={screenshotMutation.isPending} onClick={() => screenshotMutation.mutate()}>
                      {hasScreenshot ? 'Recapture' : 'Capture'}
                    </Button>
                  </div>
                }
              >
                {screenshotMutation.isPending ? (
                  <div className="flex flex-col items-center justify-center py-10 gap-3">
                    <div className="size-8 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
                    <p className="text-[12px] text-[var(--color-text-muted)]">Capturing screenshots...</p>
                  </div>
                ) : hasScreenshot ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {screenshotResult!.desktop_url && (
                      <ScreenshotFrame label="Desktop" url={screenshotResult!.desktop_url} onClick={() => setFullScreenImg(screenshotResult!.desktop_url!)} />
                    )}
                    {screenshotResult!.mobile_url && (
                      <ScreenshotFrame label="Mobile" url={screenshotResult!.mobile_url} onClick={() => setFullScreenImg(screenshotResult!.mobile_url!)} />
                    )}
                  </div>
                ) : screenshotMutation.error ? (
                  <div className="flex flex-col items-center py-8 gap-2 text-center">
                    <AlertTriangle size={20} className="text-red-500" />
                    <p className="text-[12px] text-[var(--color-text-secondary)]">Capture failed</p>
                    <Button size="xs" variant="outline" onClick={() => screenshotMutation.mutate()}>Retry</Button>
                  </div>
                ) : (
                  <EmptyState
                    title="No screenshots yet"
                    message="Capture website screenshots to inspect the current design."
                    icon={Camera}
                    action={<Button size="sm" variant="primary" onClick={() => screenshotMutation.mutate()}>Capture</Button>}
                  />
                )}
              </SectionCard>

              {/* Technical analysis */}
              <SectionCard
                title="Technical Analysis"
                action={
                  <div className="flex items-center gap-2">
                    {analysisResult && <Badge tone="success" className="text-[10px]">Done</Badge>}
                    <Button size="xs" variant={analysisResult ? 'outline' : 'primary'} loading={analysisMutation.isPending} onClick={() => analysisMutation.mutate()}>
                      {analysisResult ? 'Re-run' : 'Analyze'}
                    </Button>
                  </div>
                }
              >
                {analysisMutation.isPending ? (
                  <div className="flex flex-col items-center justify-center py-10 gap-3">
                    <div className="size-8 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
                    <p className="text-[12px] text-[var(--color-text-muted)]">Analyzing website...</p>
                  </div>
                ) : analysisResult ? (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      <MetricBox label="HTTP Status" value={String(analysisResult.http_status_code ?? '\u2014')} />
                      <MetricBox label="Response" value={`${analysisResult.response_time_ms ?? '\u2014'}ms`} />
                      <MetricBox label="Page Weight" value={`${analysisResult.html_size_kb?.toFixed(1) ?? '\u2014'} KB`} />
                      <MetricBox label="Security" value={analysisResult.https_enabled ? 'HTTPS' : 'HTTP'} tone={analysisResult.https_enabled ? 'success' : 'danger'} />
                    </div>
                    <div className="grid grid-cols-5 gap-2">
                      <MiniMetric label="H1" value={analysisResult.h1_count} />
                      <MiniMetric label="H2" value={analysisResult.h2_count} />
                      <MiniMetric label="Paragraphs" value={analysisResult.total_paragraphs} />
                      <MiniMetric label="Images" value={analysisResult.total_images} />
                      <MiniMetric label="Forms" value={analysisResult.total_forms} />
                    </div>
                    {lead.website && (
                      <div className="pt-3 border-t border-[var(--color-border)]">
                        <a href={lead.website.startsWith('http') ? lead.website : `https://${lead.website}`} target="_blank" rel="noopener noreferrer" className="text-[12px] text-[var(--color-brand)] hover:underline inline-flex items-center gap-1">
                          <ExternalLink size={12} /> Visit site
                        </a>
                      </div>
                    )}
                  </div>
                ) : analysisMutation.error ? (
                  <div className="flex flex-col items-center py-8 gap-2 text-center">
                    <AlertTriangle size={20} className="text-red-500" />
                    <p className="text-[12px] text-[var(--color-text-secondary)]">Analysis failed</p>
                    <Button size="xs" variant="outline" onClick={() => analysisMutation.mutate()}>Retry</Button>
                  </div>
                ) : (
                  <EmptyState
                    title="No analysis yet"
                    message="Run a technical analysis to inspect website structure and performance."
                    icon={Search}
                    action={<Button size="sm" variant="primary" onClick={() => analysisMutation.mutate()}>Analyze</Button>}
                  />
                )}
              </SectionCard>
            </>
          )}

          {activeTab === 'audit' && (
            <SectionCard
              title="AI Audit"
              action={
                <div className="flex items-center gap-2">
                  {hasAudit && (
                    <Badge tone={auditResult!.score.category === 'Hot Lead' ? 'success' : auditResult!.score.category === 'Warm Lead' ? 'warning' : 'muted'} className="text-[10px]">
                      {auditResult!.score.category}
                    </Badge>
                  )}
                  <Button size="xs" variant={hasAudit ? 'outline' : 'primary'} loading={auditMutation.isPending} onClick={() => auditMutation.mutate()}>
                    {hasAudit ? 'Re-audit' : 'Run Audit'}
                  </Button>
                </div>
              }
            >
              {auditMutation.isPending ? (
                <div className="flex flex-col items-center justify-center py-10 gap-3">
                  <div className="size-8 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
                  <p className="text-[12px] text-[var(--color-text-muted)]">Running AI audit...</p>
                </div>
              ) : hasAudit ? (
                <div className="space-y-6">
                  {/* Score overview */}
                  <div className="flex items-center gap-6">
                    <ScoreGauge score={auditResult!.score.overall_score} size={100} strokeWidth={7} label="Score" />
                    <div className="flex-1 space-y-3">
                      <ScoreBar label="SEO" value={auditResult!.score.seo_score} />
                      <ScoreBar label="UX" value={auditResult!.score.ux_score} />
                      <ScoreBar label="Branding" value={auditResult!.score.branding_score} />
                      <ScoreBar label="Trust" value={auditResult!.score.trust_score} />
                      <ScoreBar label="Conversion" value={auditResult!.score.conversion_score} />
                    </div>
                  </div>

                  {/* Summary */}
                  {auditResult!.audit && typeof auditResult!.audit === 'object' && ('Business Summary' in auditResult!.audit || 'Overall Summary' in auditResult!.audit) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-4 border-t border-[var(--color-border)]">
                      {'Business Summary' in auditResult!.audit && (
                        <div className="p-3.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]">
                          <p className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1.5">Business Summary</p>
                          <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{String(auditResult!.audit['Business Summary'])}</p>
                        </div>
                      )}
                      {'Overall Summary' in auditResult!.audit && (
                        <div className="p-3.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)]">
                          <p className="text-[11px] font-medium text-[var(--color-text-muted)] mb-1.5">Audit Verdict</p>
                          <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">{String(auditResult!.audit['Overall Summary'])}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Weaknesses */}
                  {auditResult!.audit && typeof auditResult!.audit === 'object' && 'Top Weaknesses' in auditResult!.audit && Array.isArray(auditResult!.audit['Top Weaknesses']) && (
                    <div className="pt-4 border-t border-[var(--color-border)]">
                      <p className="text-[11px] font-medium text-[var(--color-text-muted)] mb-3">Weaknesses &amp; Recommendations</p>
                      <div className="space-y-2.5">
                        {(auditResult!.audit['Top Weaknesses'] as Array<string | { title?: string; evidence?: string; impact?: string; recommendation?: string }>).map((w, i) => {
                          if (!w) return null;
                          const weakness = typeof w === 'string' ? { title: w } : w;
                          return (
                            <div key={i} className="p-3.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                              <p className="text-[12px] font-medium text-[var(--color-text)] mb-1">{weakness.title}</p>
                              {weakness.impact && <p className="text-[11px] text-[var(--color-text-muted)] mb-1.5">{weakness.impact}</p>}
                              {weakness.recommendation && (
                                <p className="text-[11px] text-[var(--color-success)] inline-flex items-start gap-1.5"><CheckCircle size={11} className="shrink-0 mt-0.5" />{weakness.recommendation}</p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              ) : auditMutation.error ? (
                <div className="flex flex-col items-center py-8 gap-2 text-center">
                  <AlertTriangle size={20} className="text-red-500" />
                  <p className="text-[12px] text-[var(--color-text-secondary)]">Audit failed</p>
                  <Button size="xs" variant="outline" onClick={() => auditMutation.mutate()}>Retry</Button>
                </div>
              ) : (
                <EmptyState
                  title="No audit yet"
                  message="Run an AI audit to score this lead and identify improvement opportunities."
                  icon={Shield}
                  action={<Button size="sm" variant="primary" onClick={() => auditMutation.mutate()}>Run Audit</Button>}
                />
              )}
            </SectionCard>
          )}

          {activeTab === 'redesign' && (
            <SectionCard title="Website Generation">
              {isGenerationRunning ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                    <div className="size-5 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
                    <div>
                      <p className="text-[13px] font-medium text-[var(--color-text)]">Generating website...</p>
                      <p className="text-[11px] text-[var(--color-text-muted)]">{jobResult?.progress || 'Queued'}</p>
                    </div>
                  </div>
                </div>
              ) : hasWebsite ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[14px] font-medium text-[var(--color-text)]">{existingWebsite!.project_name || 'Generated Website'}</p>
                        <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">Created {formatRelative(existingWebsite!.created_at)}</p>
                      </div>
                      <Badge tone="success" className="text-[10px] shrink-0">{existingWebsite!.status}</Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${existingWebsite!.id}`)}>
                      <Eye size={14} className="mr-1.5" /> Preview
                    </Button>
                    {existingWebsite!.package_id && (
                      <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${existingWebsite!.id}`)}>
                        <Download size={14} className="mr-1.5" /> Package
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(`${window.location.origin}/preview/${existingWebsite!.id}`, 'Preview link')}>
                      <Copy size={14} />
                    </Button>
                  </div>
                </div>
              ) : jobError ? (
                <div className="p-4 rounded-[var(--radius-md)] bg-red-500/5 border border-red-500/15">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle size={14} className="text-red-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[12px] font-medium text-red-600 dark:text-red-400">Generation failed</p>
                      <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{jobError}</p>
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="No website generated yet"
                  message="Generate a premium website redesign for this lead using AI."
                  icon={Rocket}
                  action={<Button size="sm" variant="primary" onClick={() => generate()}>Generate Website</Button>}
                />
              )}
            </SectionCard>
          )}

          {activeTab === 'website' && hasWebsite && (
            <SectionCard title="Generated Website">
              <div className="space-y-4">
                <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <p className="text-[14px] font-medium text-[var(--color-text)]">{existingWebsite!.project_name || 'Generated Website'}</p>
                      <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">ID: {existingWebsite!.id}</p>
                    </div>
                    <Badge tone="success" className="text-[10px] shrink-0">{existingWebsite!.status}</Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-[var(--color-text-muted)]">
                    <span>Created {formatRelative(existingWebsite!.created_at)}</span>
                    {existingWebsite!.updated_at && <span>Updated {formatRelative(existingWebsite!.updated_at)}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="primary" size="sm" onClick={() => navigate(`/preview/${existingWebsite!.id}`)}>
                    <Eye size={14} className="mr-1.5" /> Open Preview
                  </Button>
                  {existingWebsite!.package_id && (
                    <Button variant="outline" size="sm" onClick={() => navigate(`/deployment/${existingWebsite!.id}`)}>
                      <Download size={14} className="mr-1.5" /> Open Package
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => copyToClipboard(`${window.location.origin}/preview/${existingWebsite!.id}`, 'Preview link')}>
                    <Copy size={14} />
                  </Button>
                </div>
              </div>
            </SectionCard>
          )}
        </div>

        {/* ── Sidebar ──────────────────────────────────────────── */}
        <div className="space-y-4 lg:sticky lg:top-24">
          {/* Context panel */}
          <SectionCard title="Details">
            <div className="space-y-3">
              <InfoRow label="Status" value={<Badge tone={statusTone[lead.status] ?? 'muted'} className="text-[11px]">{lead.status.replace(/_/g, ' ')}</Badge>} />
              <InfoRow label="Audit Score" value={lead.score?.overall_score != null ? `${lead.score.overall_score}/100` : null} />
              <InfoRow label="Reviews" value={lead.reviews_count != null ? String(lead.reviews_count) : null} />
              <InfoRow label="Created" value={lead.created_at ? formatRelative(lead.created_at) : null} />
              <InfoRow label="Updated" value={lead.updated_at ? formatRelative(lead.updated_at) : null} />
            </div>
          </SectionCard>

          {/* Quick actions */}
          <SectionCard title="Actions">
            <div className="space-y-1.5">
              <SidebarAction icon={Camera} label="Capture Screenshot" active={hasScreenshot} loading={screenshotMutation.isPending} onClick={() => screenshotMutation.mutate()} />
              <SidebarAction icon={Search} label="Analyze Website" active={!!analysisResult} loading={analysisMutation.isPending} onClick={() => analysisMutation.mutate()} />
              <SidebarAction icon={Shield} label="Run Audit" active={hasAudit} loading={auditMutation.isPending} onClick={() => auditMutation.mutate()} />
              <SidebarAction
                icon={Rocket}
                label={hasWebsite ? 'View Website' : isGenerationRunning ? 'Generating...' : 'Generate Website'}
                active={hasWebsite}
                loading={isGenerationRunning}
                onClick={() => { if (hasWebsite) navigate(`/preview/${existingWebsite!.id}`); else generate(); }}
                highlight={!hasWebsite && !isGenerationRunning}
              />
              {hasWebsite && existingWebsite!.package_id && (
                <SidebarAction icon={Download} label="Download Package" onClick={() => generationService.downloadPackage(existingWebsite!.id)} />
              )}
              <SidebarAction icon={Send} label="Generate Outreach" active={!!outreachResult} loading={outreachMutation.isPending} onClick={() => outreachMutation.mutate()} />
            </div>
          </SectionCard>

          {/* Outreach */}
          <SectionCard
            title="Outreach"
            action={outreachResult ? <Badge tone="success" className="text-[10px]">Generated</Badge> : undefined}
          >
            {outreachMutation.isPending ? (
              <div className="flex flex-col items-center py-6 gap-2">
                <div className="size-6 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin" />
                <p className="text-[11px] text-[var(--color-text-muted)]">Generating...</p>
              </div>
            ) : outreachMutation.error ? (
              <div className="flex flex-col items-center py-6 gap-2 text-center">
                <AlertTriangle size={16} className="text-red-500" />
                <p className="text-[11px] text-[var(--color-text-secondary)]">Failed</p>
                <Button size="xs" variant="outline" onClick={() => outreachMutation.mutate()}>Retry</Button>
              </div>
            ) : outreachResult ? (
              <div className="space-y-2.5 max-h-[400px] overflow-y-auto lf-thin-scroll">
                {outreachResult.email_subject && (
                  <OutreachBlock label="Subject" content={outreachResult.email_subject} onCopy={() => copyToClipboard(outreachResult.email_subject!, 'Subject')} />
                )}
                {outreachResult.cold_email && (
                  <OutreachBlock label="Cold Email" content={outreachResult.cold_email} onCopy={() => copyToClipboard(outreachResult.cold_email!, 'Cold email')} />
                )}
                {outreachResult.linkedin_message && (
                  <OutreachBlock label="LinkedIn" content={outreachResult.linkedin_message} onCopy={() => copyToClipboard(outreachResult.linkedin_message!, 'LinkedIn message')} />
                )}
                {outreachResult.followup_email && (
                  <OutreachBlock label="Follow-up" content={outreachResult.followup_email} onCopy={() => copyToClipboard(outreachResult.followup_email!, 'Follow-up')} />
                )}
                {outreachResult.whatsapp_message && (
                  <OutreachBlock label="WhatsApp" content={outreachResult.whatsapp_message} onCopy={() => copyToClipboard(outreachResult.whatsapp_message!, 'WhatsApp')} />
                )}
                {outreachResult.short_cta && (
                  <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
                    <p className="text-[10px] font-medium text-[var(--color-text-muted)] mb-1">CTA</p>
                    <p className="text-[12px] text-[var(--color-text-secondary)]">{outreachResult.short_cta}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[12px] text-[var(--color-text-muted)] text-center py-4">No outreach generated yet.</p>
            )}
          </SectionCard>
        </div>
      </div>

      {/* ── Fullscreen screenshot overlay ──────────────────────── */}
      {fullScreenImg && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={() => setFullScreenImg(null)}>
          <button onClick={() => setFullScreenImg(null)} className="absolute top-4 right-4 size-9 rounded-full bg-white/10 flex items-center justify-center text-white hover:bg-white/20 transition-colors">
            <X size={18} />
          </button>
          <img src={fullScreenImg} alt="Full size screenshot" className="max-w-full max-h-full object-contain rounded-[var(--radius-lg)]" onClick={(e) => e.stopPropagation()} />
        </div>
      )}
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

function InfoRow({ label, value, href, isLink }: { label: string; value: React.ReactNode | null | undefined; href?: string; isLink?: boolean }) {
  if (value == null || value === '') return null;
  return (
    <div className="flex items-start justify-between gap-3">
      <span className="text-[11px] text-[var(--color-text-muted)] shrink-0">{label}</span>
      {href ? (
        <a href={href} target="_blank" rel="noopener noreferrer" className={cn('text-[12px] text-right truncate', isLink ? 'text-[var(--color-brand)] hover:underline' : 'text-[var(--color-text-secondary)]')}>
          {value}
        </a>
      ) : typeof value === 'string' ? (
        <span className="text-[12px] text-[var(--color-text-secondary)] text-right truncate">{value}</span>
      ) : (
        <span className="text-right">{value}</span>
      )}
    </div>
  );
}

function MetricBox({ label, value, tone }: { label: string; value: string; tone?: 'success' | 'danger' }) {
  return (
    <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-center">
      <p className={cn(
        'text-[18px] font-bold tabular-nums',
        tone === 'success' ? 'text-[var(--color-success)]' : tone === 'danger' ? 'text-[var(--color-danger)]' : 'text-[var(--color-text)]',
      )}>{value}</p>
      <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">{label}</p>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="text-center py-2">
      <p className="text-[16px] font-bold text-[var(--color-text)] tabular-nums">{value}</p>
      <p className="text-[10px] text-[var(--color-text-muted)]">{label}</p>
    </div>
  );
}

function ScreenshotFrame({ label, url, onClick }: { label: string; url: string; onClick: () => void }) {
  return (
    <div className="group relative rounded-[var(--radius-md)] overflow-hidden border border-[var(--color-border)] bg-[var(--color-surface-hover)]">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex gap-1"><span className="size-1.5 rounded-full bg-red-400/60" /><span className="size-1.5 rounded-full bg-amber-400/60" /><span className="size-1.5 rounded-full bg-emerald-400/60" /></div>
        <span className="text-[10px] text-[var(--color-text-muted)]">{label}</span>
      </div>
      <img src={url} alt={`${label} screenshot`} className="w-full object-cover cursor-pointer" onClick={onClick} />
      <button onClick={onClick} className="absolute top-2 right-2 size-7 rounded-[var(--radius-md)] bg-black/50 flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity">
        <Maximize2 size={12} />
      </button>
    </div>
  );
}

function SidebarAction({ icon: Icon, label, active, loading, onClick, highlight }: {
  icon: typeof Camera; label: string; active?: boolean; loading?: boolean; onClick: () => void; highlight?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={cn(
        'w-full flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-md)] transition-colors duration-[var(--anim-fast)] text-left group',
        highlight
          ? 'bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] text-[var(--color-text)] hover:bg-[var(--color-brand-soft)]'
          : active
            ? 'bg-[var(--color-surface-hover)] text-[var(--color-text)] hover:bg-[var(--color-border)]'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]',
      )}
    >
      <Icon size={14} className={cn(active ? 'text-[var(--color-success)]' : highlight ? 'text-[var(--color-brand)]' : 'text-[var(--color-text-muted)]')} />
      <span className="flex-1 text-[12px] font-medium truncate">{label}</span>
      {active && !loading && <CheckCircle size={12} className="text-[var(--color-success)] shrink-0" />}
      {loading && <div className="size-3.5 border-2 border-[var(--color-border)] border-t-[var(--color-brand)] rounded-full lf-spin shrink-0" />}
    </button>
  );
}

function OutreachBlock({ label, content, onCopy }: { label: string; content: string; onCopy: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const truncated = content.length > 200;
  return (
    <div className="p-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-medium text-[var(--color-text-muted)]">{label}</span>
        <div className="flex items-center gap-1">
          <button onClick={onCopy} className="size-5 rounded flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"><Copy size={10} /></button>
          {truncated && (
            <button onClick={() => setExpanded(!expanded)} className="size-5 rounded flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
              {expanded ? <X size={10} /> : <ChevronDown size={10} />}
            </button>
          )}
        </div>
      </div>
      <p className="text-[11px] text-[var(--color-text-secondary)] whitespace-pre-wrap leading-relaxed">
        {truncated && !expanded ? `${content.slice(0, 200)}...` : content}
      </p>
    </div>
  );
}
