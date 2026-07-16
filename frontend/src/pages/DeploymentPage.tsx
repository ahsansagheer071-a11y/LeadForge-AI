import { Download, Loader2, AlertCircle, CheckCircle2, Play, Copy, Check, ArrowLeft, Send } from 'lucide-react';
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
      <div className="space-y-5 lf-fade-in">
        <div>
          <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Deployment</h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Package and distribute your generated website</p>
        </div>
        <EmptyState title="No target selected" message="Generate a website first to create deployment artifacts." action={<Button variant="primary" onClick={() => navigate('/generation')}>Open Generation</Button>} />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-5 lf-fade-in">
        <div className="flex items-center gap-4">
          <Skeleton variant="rounded" width={36} height={36} />
          <div><Skeleton variant="text" width={240} height={28} /><Skeleton variant="text" width={300} height={14} className="mt-1.5" /></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-5">
            <Panel><div className="p-6 space-y-4">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} variant="rounded" width="100%" height={48} delay={i * 60} />)}</div></Panel>
            <Panel><div className="p-6"><Skeleton variant="rounded" width="100%" height={100} /></div></Panel>
          </div>
          <Panel><div className="p-6 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} variant="rounded" width="100%" height={40} delay={i * 60} />)}</div></Panel>
        </div>
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="space-y-5 lf-fade-in">
        <div>
          <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Deployment</h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5">Package and distribute your generated website</p>
        </div>
        <EmptyState title="Website not found" message="The requested deployment package does not exist or access is restricted." action={<Button variant="outline" onClick={() => navigate('/generation')}>Return to Generation</Button>} />
      </div>
    );
  }

  return (
    <div className="space-y-5 lf-fade-in">
      {/* ── Header ──────────────────────────────────────────── */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(`/preview/${websiteId}`)}
          className="size-9 rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-border-strong)] transition-colors"
          aria-label="Back to preview"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="min-w-0">
          <h1 className="text-[24px] md:text-[28px] font-semibold tracking-tight text-[var(--color-text)]">Deployment</h1>
          <p className="text-[13px] text-[var(--color-text-secondary)] mt-0.5 truncate">
            {website.project_name || 'Generated Website'}
            <span className="mx-1.5 text-[var(--color-text-muted)]">&middot;</span>
            <span className="font-mono text-[11px]">{website.id.slice(0, 8)}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* ── Main content ────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          {/* Website info */}
          <Panel>
            <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between">
              <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">Website</h3>
              <Badge tone={statusTone[website.status] ?? 'muted'} className="text-[10px]">{website.status}</Badge>
            </div>
            <div className="p-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
              <MetaItem label="Framework" value={website.framework} />
              <MetaItem label="Generated" value={formatRelative(website.created_at)} />
              <MetaItem label="Filename" value={`leadforge-${website.id.slice(0, 8)}.zip`} mono />
              <MetaItem label="Status" value={
                <Badge tone={statusTone[website.status] ?? 'muted'} className="text-[10px]">{website.status}</Badge>
              } />
            </div>
          </Panel>

          {/* Status panel */}
          {isPackageReady ? (
            <div className="rounded-[var(--radius-xl)] bg-emerald-500/5 border border-emerald-500/20 p-5 flex items-start gap-4">
              <div className="size-10 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
                <CheckCircle2 className="size-5 text-emerald-500" />
              </div>
              <div>
                <p className="text-[14px] font-semibold text-[var(--color-text)] mb-0.5">Package Ready</p>
                <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed">
                  The website has been compiled into a downloadable ZIP archive. Download and host manually, or connect a deployment provider.
                </p>
              </div>
            </div>
          ) : website.status === 'failed' || website.status === 'error' ? (
            <div className="rounded-[var(--radius-xl)] bg-red-500/5 border border-red-500/20 p-5 flex items-start gap-4">
              <div className="size-10 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center shrink-0">
                <AlertCircle className="size-5 text-red-500" />
              </div>
              <div>
                <p className="text-[14px] font-semibold text-[var(--color-text)] mb-0.5">Compilation Failed</p>
                <p className="text-[12px] text-[var(--color-text-secondary)]">An error occurred during asset synthesis. Regenerate the website.</p>
              </div>
            </div>
          ) : (
            <div className="rounded-[var(--radius-xl)] bg-[var(--color-brand-soft)] border border-[var(--color-brand-border)] p-5 flex items-start gap-4">
              <div className="size-10 rounded-full bg-[var(--color-brand-subtle)] border border-[var(--color-brand-border)] flex items-center justify-center shrink-0">
                <Loader2 className="size-5 text-[var(--color-brand)] lf-spin" />
              </div>
              <div>
                <p className="text-[14px] font-semibold text-[var(--color-text)] mb-0.5">Processing Package</p>
                <p className="text-[12px] text-[var(--color-text-secondary)]">Compilation in progress. Please wait.</p>
              </div>
            </div>
          )}
        </div>

        {/* ── Sidebar actions ──────────────────────────────── */}
        <div className="space-y-5 lg:sticky lg:top-24">
          <Panel>
            <div className="px-4 py-3 border-b border-[var(--color-border)]">
              <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">Actions</h3>
            </div>
            <div className="p-4 space-y-2.5">
              {/* Download */}
              <Button
                variant="primary"
                fullWidth
                size="md"
                leftIcon={downloadLoading ? <Loader2 size={15} className="lf-spin" /> : <Download size={15} />}
                disabled={!hasArtifacts || downloadLoading}
                loading={downloadLoading}
                onClick={handleDownload}
              >
                {downloadLoading ? 'Extracting...' : 'Download ZIP Package'}
              </Button>

              {/* Preview */}
              <Button
                variant="outline"
                fullWidth
                size="md"
                leftIcon={<Play size={14} />}
                onClick={() => navigate(`/preview/${websiteId}`)}
              >
                Open Preview
              </Button>

              {/* Copy link */}
              <button
                onClick={handleCopyLink}
                className={cn(
                  'w-full flex items-center justify-center gap-2 py-2.5 rounded-[var(--radius-md)] border text-[12px] font-medium transition-colors',
                  copied
                    ? 'bg-emerald-500/5 border-emerald-500/20 text-emerald-500'
                    : 'bg-[var(--color-surface-hover)] border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-border-strong)] hover:text-[var(--color-text)]',
                )}
              >
                {copied ? <Check size={13} /> : <Copy size={13} />}
                {copied ? 'Link Copied' : 'Copy Link'}
              </button>
            </div>
          </Panel>

          {/* Next step */}
          <Panel>
            <div className="px-4 py-3 border-b border-[var(--color-border)]">
              <h3 className="text-[12px] font-bold text-[var(--color-text)] font-mono uppercase tracking-wider">Next Step</h3>
            </div>
            <div className="p-4">
              <Button
                variant="outline"
                fullWidth
                size="md"
                leftIcon={<Send size={14} />}
                onClick={() => navigate('/projects')}
              >
                Generate Outreach
              </Button>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

/* ── Sub-components ─────────────────────────────────────────── */

function Panel({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-[var(--radius-xl)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden">
      {children}
    </div>
  );
}

function MetaItem({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div>
      <p className="text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider mb-1">{label}</p>
      <div className={cn('text-[13px] text-[var(--color-text)] font-medium', mono && 'font-mono text-[12px] truncate')}>
        {value}
      </div>
    </div>
  );
}
