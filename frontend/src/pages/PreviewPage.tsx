import { ExternalLink, RefreshCw, Monitor, Smartphone, Tablet, AlertCircle, ArrowLeft, Copy, Check, Download, Rocket } from 'lucide-react';
import { Skeleton } from '@/components/Loading';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { EmptyState } from '@/components/ErrorStates';
import { usePreviewStore } from '@/store';
import { generationService } from '@/services/services';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { toast } from 'sonner';

type Viewport = 'desktop' | 'tablet' | 'mobile';

const VIEWPORT_ICONS = { desktop: Monitor, tablet: Tablet, mobile: Smartphone } as const;
const VIEWPORT_WIDTHS: Record<Viewport, string> = {
  desktop: 'w-full',
  tablet: 'w-[768px]',
  mobile: 'w-[375px]',
};

function formatRelative(dateStr: string): string {
  const d = new Date(dateStr);
  const now = Date.now();
  const diff = now - d.getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function PreviewPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const { htmlContent: storeHtml } = usePreviewStore();
  const [viewport, setViewport] = useState<Viewport>('desktop');
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const { data: website, isLoading, error } = useQuery({
    queryKey: ['generated-website', websiteId],
    queryFn: () => generationService.getById(websiteId!),
    enabled: !!websiteId,
  });

  const htmlContent = website?.html ?? storeHtml;
  const hasPreview = !!htmlContent;

  const handleCopyLink = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { toast.error('Failed to copy link'); }
  };

  const handleOpenInTab = () => {
    if (htmlContent) {
      const win = window.open('', '_blank');
      if (win) { win.document.write(htmlContent); win.document.close(); }
    }
  };

  const handleReload = () => { if (websiteId) window.location.reload(); };

  const handleDownload = async () => {
    if (!websiteId) return;
    try {
      await generationService.downloadPackage(websiteId);
    } catch {
      toast.error('Download failed. The package may not be available yet.');
    }
  };

  /* ── Loading ──────────────────────────────────────────────── */
  if (websiteId && isLoading) {
    return (
      <div className="flex flex-col h-screen bg-[var(--color-bg)]">
        <div className="h-12 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center px-5 shrink-0">
          <Skeleton variant="text" width={160} height={16} />
        </div>
        <div className="h-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center px-5 gap-4 shrink-0">
          <Skeleton variant="rounded" width={200} height={28} />
          <div className="flex-1" />
          <Skeleton variant="rounded" width={100} height={28} />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="relative size-10">
              <div className="absolute inset-0 rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-brand)] animate-spin" />
            </div>
            <p className="text-[12px] font-mono text-[var(--color-text-muted)]">Loading preview…</p>
          </div>
        </div>
      </div>
    );
  }

  /* ── Error ────────────────────────────────────────────────── */
  if (websiteId && error) {
    return (
      <div className="flex flex-col h-screen bg-[var(--color-bg)]">
        <div className="h-12 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center px-5 shrink-0">
          <button
            onClick={() => navigate(-1)}
            className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
          >
            <ArrowLeft size={14} />
          </button>
          <span className="ml-3 text-[13px] font-semibold text-[var(--color-text)]">Redesign Preview</span>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="p-8 text-center max-w-sm rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)]">
            <div className="size-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="size-5 text-red-400" />
            </div>
            <h2 className="text-[15px] font-semibold text-[var(--color-text)] mb-1">Preview Unavailable</h2>
            <p className="text-[12px] text-[var(--color-text-muted)] mb-5">
              This website could not be loaded. It may have expired or been removed.
            </p>
            <Button variant="secondary" size="sm" onClick={() => navigate(-1)} leftIcon={<ArrowLeft size={13} />}>
              Go Back
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const statusTone = (s: string) => {
    if (s === 'live' || s === 'deployed') return 'success' as const;
    if (s === 'failed') return 'danger' as const;
    return 'info' as const;
  };

  return (
    <div className={cn('flex flex-col h-screen bg-[var(--color-bg)]', expanded && 'fixed inset-0 z-50')}>
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="h-12 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between px-5 shrink-0 z-30">
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={() => navigate(websiteId ? `/deployment/${websiteId}` : '/generation')}
            className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors shrink-0"
            title="Back"
          >
            <ArrowLeft size={14} />
          </button>
          <span className="text-[13px] font-semibold text-[var(--color-text)] truncate">Redesign Preview</span>
          {website?.project_name && (
            <>
              <span className="text-[var(--color-text-muted)] text-[11px] opacity-40">/</span>
              <span className="text-[12px] font-mono text-[var(--color-text-secondary)] truncate hidden sm:block">
                {website.project_name}
              </span>
            </>
          )}
          {website?.status && (
            <Badge tone={statusTone(website.status)} className="text-[10px] shrink-0">
              {website.status}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {website?.created_at && (
            <span className="text-[11px] font-mono text-[var(--color-text-muted)] hidden md:block mr-2">
              {formatRelative(website.created_at)}
            </span>
          )}
          {websiteId && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/deployment/${websiteId}`)}
              rightIcon={<Rocket size={12} />}
            >
              Continue to Deployment
            </Button>
          )}
        </div>
      </header>

      {/* ── Toolbar ─────────────────────────────────────────── */}
      {hasPreview && (
        <div className="h-10 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between px-5 shrink-0 z-20">
          {/* Left: viewport segmented control */}
          <div className="flex items-center gap-0.5 bg-[var(--color-surface-hover)] rounded-[var(--radius-md)] p-0.5 border border-[var(--color-border)]">
            {(Object.keys(VIEWPORT_ICONS) as Viewport[]).map((v) => {
              const Icon = VIEWPORT_ICONS[v];
              return (
                <button
                  key={v}
                  onClick={() => setViewport(v)}
                  title={v.charAt(0).toUpperCase() + v.slice(1)}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1 rounded-[calc(var(--radius-md)-2px)] text-[11px] font-mono capitalize font-medium transition-all duration-[var(--anim-fast)]',
                    viewport === v
                      ? 'bg-[var(--color-surface)] text-[var(--color-text)] border border-[var(--color-border)] shadow-sm'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)]',
                  )}
                >
                  <Icon size={12} />{v}
                </button>
              );
            })}
          </div>

          {/* Right: action buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={handleReload}
              className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
              title="Refresh preview"
            >
              <RefreshCw size={13} />
            </button>
            <button
              onClick={handleCopyLink}
              className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
              title="Copy preview link"
            >
              {copied ? <Check size={13} className="text-[var(--color-success)]" /> : <Copy size={13} />}
            </button>
            <button
              onClick={handleOpenInTab}
              className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
              title="Open in new tab"
            >
              <ExternalLink size={13} />
            </button>
            <div className="w-px h-4 bg-[var(--color-border)] mx-1" />
            <button
              onClick={handleDownload}
              className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
              title="Download package"
            >
              <Download size={13} />
            </button>
            <button
              onClick={() => setExpanded((e) => !e)}
              className="size-7 rounded-[var(--radius-md)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-hover)] transition-colors"
              title={expanded ? 'Exit expanded view' : 'Expand preview'}
            >
              {expanded ? <Tablet size={13} /> : <Monitor size={13} />}
            </button>
          </div>
        </div>
      )}

      {/* ── Main Preview Canvas ─────────────────────────────── */}
      <div className="flex-1 min-h-0 flex flex-col">
        {hasPreview ? (
          <div className="flex-1 flex flex-col bg-[var(--color-bg)]">
            {/* Minimal browser chrome */}
            <div className="flex items-center gap-2.5 px-4 py-2 bg-[var(--color-surface)] border-b border-[var(--color-border)] shrink-0">
              <div className="flex items-center gap-1.5">
                <span className="size-2 rounded-full bg-[var(--color-border-strong)]" />
                <span className="size-2 rounded-full bg-[var(--color-border-strong)]" />
                <span className="size-2 rounded-full bg-[var(--color-border-strong)]" />
              </div>
              <div className="flex-1 flex items-center justify-center">
                <div className="bg-[var(--color-bg)] border border-[var(--color-border)] rounded-[var(--radius-md)] px-3 py-1 text-[11px] font-mono text-[var(--color-text-muted)] truncate max-w-[360px] flex items-center gap-1.5">
                  <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--color-success)] shrink-0">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0110 0v4" />
                  </svg>
                  {website?.preview_path ? `preview/${websiteId}` : 'localhost'}
                </div>
              </div>
              <div className="w-14" />
            </div>

            {/* Responsive preview area */}
            <div className="flex-1 min-h-0 overflow-auto flex justify-center bg-[var(--color-bg)] p-4 lf-thin-scroll">
              <div
                className={cn(
                  'bg-white rounded-[var(--radius-lg)] overflow-hidden transition-all duration-[var(--anim-slow)] ease-in-out border border-[var(--color-border)] shadow-[var(--shadow-lg)]',
                  VIEWPORT_WIDTHS[viewport],
                  viewport === 'desktop' ? 'h-full' : 'h-[600px] self-center',
                )}
              >
                <iframe
                  title="Website Preview"
                  srcDoc={htmlContent}
                  style={{ width: '100%', height: '100%', border: 'none' }}
                  className="bg-white"
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center p-6">
            <EmptyState
              title="No Preview Available"
              message="Generate a website first to access the preview workspace."
              action={
                <Button variant="primary" size="sm" onClick={() => navigate('/generation')} leftIcon={<Monitor size={14} />}>
                  Go to Redesign Studio
                </Button>
              }
            />
          </div>
        )}
      </div>

      {/* ── Status bar ──────────────────────────────────────── */}
      {hasPreview && (
        <div className="h-7 border-t border-[var(--color-border)] bg-[var(--color-surface)] flex items-center justify-between px-5 shrink-0 text-[10px] font-mono text-[var(--color-text-muted)]">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5">
              <span className="size-1.5 rounded-full bg-[var(--color-success)]" />
              {viewport}
            </span>
            {website?.framework && <span>{website.framework}</span>}
          </div>
          <div className="flex items-center gap-3">
            {website?.package_id && <span>Package ready</span>}
            <span>LeadForge</span>
          </div>
        </div>
      )}
    </div>
  );
}
