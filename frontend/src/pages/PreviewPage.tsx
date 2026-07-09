import { ExternalLink, RefreshCw, Monitor, Smartphone, Tablet, AlertCircle, Rocket, Copy, ArrowLeft, Check } from 'lucide-react';
import { Skeleton } from '@/components/Loading';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { EmptyState } from '@/components/ErrorStates';
import { usePreviewStore } from '@/store';
import { generationService } from '@/services/services';
import { PremiumCard } from '@/components/PremiumCard';
import { toast } from 'sonner';

type Viewport = 'desktop' | 'tablet' | 'mobile';

const VIEWPORT_ICONS = { desktop: Monitor, tablet: Tablet, mobile: Smartphone } as const;
const VIEWPORT_WIDTHS: Record<Viewport, string> = {
  desktop: 'w-full',
  tablet: 'w-[768px]',
  mobile: 'w-[375px]',
};

export function PreviewPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const { htmlContent: storeHtml } = usePreviewStore();
  const [viewport, setViewport] = useState<Viewport>('desktop');
  const [copied, setCopied] = useState(false);

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

  /* ── Loading ──────────────────────────────────────────────── */
  if (websiteId && isLoading) {
    return (
      <div className="flex flex-col h-screen bg-[#040810]">
        <div className="p-6 border-b border-[var(--color-border)]">
          <Skeleton variant="text" width={200} height={28} />
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="relative size-16">
              <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-[#0ea5e9] border-r-[#8b5cf6] animate-spin" style={{ animationDuration: '1s' }} />
              <div className="absolute inset-2 rounded-full border border-transparent border-b-[#06b6d4] border-l-[#06b6d4] animate-spin" style={{ animationDuration: '1.5s', animationDirection: 'reverse' }} />
            </div>
            <p className="text-[13px] font-mono text-[var(--color-text-muted)] uppercase tracking-widest">Loading preview environment...</p>
          </div>
        </div>
      </div>
    );
  }

  /* ── Error ────────────────────────────────────────────────── */
  if (websiteId && error) {
    return (
      <div className="flex flex-col h-screen bg-[#040810]">
        <div className="p-6 border-b border-[var(--color-border)]">
          <h1 className="text-[20px] font-extrabold text-white">Preview Studio</h1>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <PremiumCard variant="danger" innerClassName="p-10 text-center max-w-lg">
            <AlertCircle className="size-16 text-red-400 mx-auto mb-6" />
            <h2 className="text-[20px] font-bold text-white mb-2">Preview Unavailable</h2>
            <p className="text-[13px] font-mono text-[var(--color-text-muted)] mb-6">Asset could not be loaded. It may have expired or been removed.</p>
            <button onClick={() => navigate('/generation')} className="px-6 py-2.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] text-white font-mono uppercase tracking-widest text-[12px] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] transition-all">
              Return to Lab
            </button>
          </PremiumCard>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-[#040810]">
      {/* ── Floating control toolbar ─────────────────────────── */}
      <div className="sticky top-0 z-30 border-b border-[var(--color-border)] bg-[rgba(4,8,16,0.95)] backdrop-blur-xl">
        <div className="flex items-center justify-between px-4 lg:px-6 py-3">
          {/* Left: back + title */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(websiteId ? `/deployment/${websiteId}` : '/generation')}
              className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] transition-all"
            >
              <ArrowLeft size={16} />
            </button>
            <div>
              <h1 className="text-[14px] font-bold text-white">Preview Studio</h1>
              <p className="text-[10px] font-mono text-[var(--color-text-muted)]">{website?.project_name || 'Generated Website'}</p>
            </div>
          </div>

          {/* Center: viewport controls */}
          {hasPreview && (
            <div className="hidden md:flex items-center gap-1 bg-[var(--color-surface-hover)] rounded-[var(--radius-md)] p-1 border border-[var(--color-border)]">
              {(Object.keys(VIEWPORT_ICONS) as Viewport[]).map((v) => {
                const Icon = VIEWPORT_ICONS[v];
                return (
                  <button
                    key={v}
                    onClick={() => setViewport(v)}
                    className={cn(
                      'flex items-center gap-2 px-4 py-1.5 rounded-[calc(var(--radius-md)-2px)] text-[11px] font-mono uppercase tracking-wider font-semibold transition-all',
                      viewport === v
                        ? 'bg-gradient-to-r from-[#0ea5e9]/20 to-[#8b5cf6]/20 text-white shadow-[0_0_10px_rgba(14,165,233,0.15)]'
                        : 'text-[var(--color-text-muted)] hover:text-white',
                    )}
                  >
                    <Icon size={13} />{v}
                  </button>
                );
              })}
            </div>
          )}

          {/* Right: actions */}
          {hasPreview && (
            <div className="flex items-center gap-2">
              <button onClick={handleReload} className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all" title="Refresh">
                <RefreshCw size={15} />
              </button>
              <button onClick={handleCopyLink} className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all relative" title="Copy preview link">
                {copied ? <Check size={15} className="text-emerald-400" /> : <Copy size={15} />}
              </button>
              <button onClick={handleOpenInTab} className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all" title="Open in new tab">
                <ExternalLink size={15} />
              </button>
              {websiteId && (
                <button
                  onClick={() => navigate(`/deployment/${websiteId}`)}
                  className="flex items-center gap-2 px-4 py-2 rounded-[var(--radius-md)] bg-gradient-to-r from-[#10b981] to-[#059669] text-white font-mono uppercase tracking-wider text-[11px] font-bold shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] hover:-translate-y-0.5 transition-all"
                >
                  <Rocket size={14} /> Deploy
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Main preview area ────────────────────────────────── */}
      <div className="flex-1 min-h-0 flex flex-col p-4 lg:p-6">
        {hasPreview ? (
          <PremiumCard variant="featured" innerClassName="flex-1 flex flex-col relative overflow-hidden bg-[#0a0a0a] p-0">
            {/* Browser chrome */}
            <div className="flex items-center gap-3 px-4 py-3 bg-[#1a1a1a] border-b border-[#2a2a2a] shrink-0">
              <div className="flex gap-1.5">
                <span className="size-3 rounded-full bg-red-500/70" />
                <span className="size-3 rounded-full bg-amber-500/70" />
                <span className="size-3 rounded-full bg-emerald-500/70" />
              </div>
              <div className="flex-1 flex items-center justify-center">
                <div className="bg-[#2a2a2a] rounded-full px-4 py-1.5 text-[11px] font-mono text-[var(--color-text-muted)] truncate max-w-[400px] flex items-center gap-2">
                  <LockIcon />
                  {website?.preview_path ? `${window.location.origin}/preview/${websiteId}` : 'localhost'}
                </div>
              </div>
              {/* Mobile viewport selector inline */}
              <div className="flex md:hidden items-center gap-1">
                {(Object.keys(VIEWPORT_ICONS) as Viewport[]).map((v) => {
                  const Icon = VIEWPORT_ICONS[v];
                  return (
                    <button
                      key={v}
                      onClick={() => setViewport(v)}
                      className={cn(
                        'size-8 rounded-md flex items-center justify-center text-[10px] transition-all',
                        viewport === v ? 'bg-[#0ea5e9]/20 text-[#0ea5e9]' : 'text-[var(--color-text-muted)]',
                      )}
                    >
                      <Icon size={13} />
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Preview iframe */}
            <div className="flex-1 w-full flex justify-center bg-[#0a0a0a] p-4 overflow-y-auto lf-thin-scroll">
              <div
                className={cn(
                  'h-full bg-white rounded-[8px] overflow-hidden shadow-2xl transition-all duration-500 ease-in-out border border-[#2a2a2a]',
                  VIEWPORT_WIDTHS[viewport],
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
          </PremiumCard>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <EmptyState
              title="No Preview Available"
              message="Generate a website first to access the preview studio."
              action={
                <button onClick={() => navigate('/generation')} className="px-6 py-2.5 rounded-[var(--radius-md)] bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white font-mono text-[12px] font-bold uppercase tracking-wider shadow-[0_0_15px_rgba(14,165,233,0.3)] hover:shadow-[0_0_25px_rgba(14,165,233,0.5)] transition-all">
                  Go to Lab
                </button>
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Lock icon for URL bar ──────────────────────────────────── */
function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500 shrink-0">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0110 0v4" />
    </svg>
  );
}
