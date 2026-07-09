import { Download, Loader2, AlertCircle, CheckCircle2, Archive, Play, Copy, Check, ArrowLeft, Send } from 'lucide-react';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { formatRelative } from '@/utils';
import { generationService } from '@/services/services';
import { PremiumCard } from '@/components/PremiumCard';
import { toast } from 'sonner';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  generated: 'success', building: 'warning', failed: 'danger', pending: 'info', error: 'danger',
};

export function DeploymentPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const { data: website, isLoading, error } = useQuery({
    queryKey: ['generated-website', websiteId],
    queryFn: () => generationService.getById(websiteId!),
    enabled: !!websiteId,
  });

  const isPackageReady = website?.status === 'generated' || website?.status === 'ready';
  const hasArtifacts = isPackageReady && website?.package_metadata &&
    Array.isArray(website.package_metadata.artifacts) &&
    website.package_metadata.artifacts.length > 0;

  const handleDownload = async () => {
    if (!websiteId) return;
    setDownloadLoading(true);
    try {
      await generationService.downloadPackage(websiteId);
      toast.success('Download sequence initiated');
    } catch (err) {
      toast.error((err as { message?: string })?.message || 'Download failed');
    } finally { setDownloadLoading(false); }
  };

  const handleCopyLink = async () => {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { toast.error('Failed to copy link'); }
  };

  if (!websiteId) {
    return (
      <div className="space-y-8 lf-fade-in">
        <div><h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Delivery Vault</h1><p className="text-[13px] font-mono text-[var(--color-text-secondary)] uppercase tracking-widest">Extract and distribute synthesized assets</p></div>
        <EmptyState title="No target selected" message="Initialize generation protocols first to create deployment artifacts." action={<Button variant="brand" onClick={() => navigate('/generation')}>Go to Lab</Button>} />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-8 lf-fade-in">
        <div><Skeleton variant="text" width={240} height={32} /><Skeleton variant="text" width={340} height={16} className="mt-2" /></div>
        <PremiumCard variant="featured" innerClassName="p-10 space-y-6">
          {Array.from({ length: 4 }).map((_, i) => (<Skeleton key={i} variant="rounded" width="100%" height={60} delay={i * 60} />))}
        </PremiumCard>
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="space-y-8 lf-fade-in">
        <div><h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Delivery Vault</h1><p className="text-[13px] font-mono text-[var(--color-text-secondary)] uppercase tracking-widest">Extract and distribute synthesized assets</p></div>
        <EmptyState title="Asset not located" message="The requested deployment package does not exist or access is restricted." action={<Button variant="outline" onClick={() => navigate('/generation')}>Return to Lab</Button>} />
      </div>
    );
  }

  return (
    <div className="space-y-8 lf-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(`/preview/${websiteId}`)} className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-white transition-all">
          <ArrowLeft size={16} />
        </button>
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Delivery Vault</h1>
          <p className="text-[13px] font-mono text-[var(--color-text-secondary)] uppercase tracking-widest">Secure asset extraction &amp; distribution</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Featured Package Card ───────────────────────────── */}
        <PremiumCard variant="featured" className="lg:col-span-2" innerClassName="p-8 lg:p-10 flex flex-col">
          {/* Identity header */}
          <div className="flex items-start justify-between mb-8 pb-6 border-b border-[var(--color-border)]">
            <div>
              <h2 className="text-[22px] font-bold text-white mb-1">{website.project_name || 'Generated Website'}</h2>
              <p className="text-[11px] font-mono text-[var(--color-text-muted)]">Asset ID: {website.package_id || website.id}</p>
            </div>
            <Badge tone={statusTone[website.status] ?? 'muted'} className="font-mono px-3 py-1 text-[12px]">{website.status}</Badge>
          </div>

          {/* Status panel */}
          {isPackageReady ? (
            <div className="flex items-center gap-5 p-6 rounded-[var(--radius-lg)] bg-emerald-500/5 border border-emerald-500/20 mb-8">
              <div className="size-16 rounded-full bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center shrink-0 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
                <CheckCircle2 className="size-8 text-emerald-400" />
              </div>
              <div>
                <p className="text-[18px] font-bold text-white mb-1">ZIP Package Ready</p>
                <p className="text-[12px] font-mono text-[var(--color-text-secondary)] leading-relaxed">
                  The website has been compiled into a downloadable ZIP archive.
                  <span className="block text-[11px] text-[var(--color-text-muted)] mt-1">Note: This is a local package, not a public deployment. Download and host manually, or connect a deployment provider.</span>
                </p>
              </div>
            </div>
          ) : website.status === 'failed' || website.status === 'error' ? (
            <div className="flex items-center gap-5 p-6 rounded-[var(--radius-lg)] bg-red-500/5 border border-red-500/20 mb-8">
              <div className="size-16 rounded-full bg-red-500/15 border border-red-500/40 flex items-center justify-center shrink-0">
                <AlertCircle className="size-8 text-red-400" />
              </div>
              <div>
                <p className="text-[18px] font-bold text-white mb-1">Compilation Failed</p>
                <p className="text-[12px] font-mono text-[var(--color-text-secondary)]">An error occurred during asset synthesis. Regenerate the website.</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-5 p-6 rounded-[var(--radius-lg)] bg-[#0ea5e9]/5 border border-[#0ea5e9]/20 mb-8 relative overflow-hidden">
              <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent,rgba(14,165,233,0.08),transparent)] -translate-x-full animate-[lf-shimmer_2s_infinite]" />
              <div className="size-16 rounded-full bg-[#0ea5e9]/15 border border-[#0ea5e9]/40 flex items-center justify-center shrink-0 relative">
                <Loader2 className="size-8 text-[#0ea5e9] lf-spin" />
              </div>
              <div className="relative">
                <p className="text-[18px] font-bold text-white mb-1">Processing Package</p>
                <p className="text-[12px] font-mono text-[var(--color-text-secondary)]">Compilation in progress. Please wait.</p>
              </div>
            </div>
          )}

          {/* Metadata grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
              <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Framework</p>
              <p className="text-[15px] font-bold text-[#0ea5e9]">{website.framework}</p>
            </div>
            <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
              <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Generated</p>
              <p className="text-[13px] font-medium text-white">{formatRelative(website.created_at)}</p>
            </div>
            <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
              <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Filename</p>
              <p className="text-[13px] font-medium text-white font-mono truncate">leadforge-{website.id.slice(0, 8)}.zip</p>
            </div>
            <div className="p-4 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] border border-[var(--color-border)]">
              <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">Status</p>
              <Badge tone={statusTone[website.status] ?? 'muted'} className="font-mono text-[10px]">{website.status}</Badge>
            </div>
          </div>
        </PremiumCard>

        {/* ── Actions panel ──────────────────────────────────── */}
        <PremiumCard innerClassName="p-8 flex flex-col justify-between">
          <div>
            <h3 className="text-[14px] font-mono uppercase tracking-widest text-[#0ea5e9] mb-6 pb-3 border-b border-[var(--color-border)] flex items-center gap-2">
              <Archive size={16} /> Operations
            </h3>

            <div className="space-y-3">
              {/* Download */}
              <button
                disabled={!hasArtifacts || downloadLoading}
                onClick={handleDownload}
                className={cn(
                  'w-full flex items-center justify-center gap-3 py-4 rounded-[var(--radius-md)] text-[13px] font-mono uppercase tracking-widest font-bold transition-all duration-300 border',
                  !hasArtifacts
                    ? 'bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border-[var(--color-border)] cursor-not-allowed'
                    : downloadLoading
                      ? 'bg-[#0ea5e9]/10 text-[#0ea5e9] border-[#0ea5e9]/30 cursor-wait'
                      : 'bg-gradient-to-r from-[#0ea5e9] to-[#3b82f6] text-white border-transparent shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-0.5',
                )}
              >
                {downloadLoading ? <Loader2 size={16} className="lf-spin" /> : <Download size={16} />}
                {downloadLoading ? 'Extracting...' : 'Download ZIP Package'}
              </button>

              {/* Preview */}
              <button
                onClick={() => navigate(`/preview/${websiteId}`)}
                className="w-full flex items-center justify-center gap-3 py-3.5 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] border border-[var(--color-border)] hover:border-[#0ea5e9]/30 transition-all text-white font-mono uppercase tracking-widest text-[12px]"
              >
                <Play size={14} /> Open Preview
              </button>

              {/* Copy link */}
              <button
                onClick={handleCopyLink}
                className="w-full flex items-center justify-center gap-3 py-3 rounded-[var(--radius-md)] bg-[var(--color-surface-hover)] hover:bg-[color-mix(in_oklab,var(--color-surface-hover)_80%,#0ea5e9)] border border-[var(--color-border)] hover:border-[#0ea5e9]/30 transition-all text-white font-mono uppercase tracking-widest text-[11px]"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                {copied ? 'Link Copied' : 'Copy Vault Link'}
              </button>
            </div>
          </div>

          {/* Outreach CTA */}
          <div className="mt-8 pt-6 border-t border-[var(--color-border)] space-y-4">
            <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider text-center">Next Step</p>
            <button
              onClick={() => navigate('/projects')}
              className="w-full flex items-center justify-center gap-3 py-3.5 rounded-[var(--radius-md)] bg-gradient-to-r from-[#22d3ee]/10 to-[#06b6d4]/10 border border-[#22d3ee]/30 text-[#22d3ee] font-mono uppercase tracking-widest text-[12px] font-bold hover:from-[#22d3ee]/20 hover:to-[#06b6d4]/20 hover:-translate-y-0.5 transition-all"
            >
              <Send size={14} /> Generate Outreach
            </button>
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}
