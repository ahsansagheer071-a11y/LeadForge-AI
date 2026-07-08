import { Download, Loader2, AlertCircle, CheckCircle2, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { formatRelative } from '@/utils';
import { generationService } from '@/services/services';
import { toast } from 'sonner';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  generated: 'success',
  building: 'warning',
  failed: 'danger',
  pending: 'info',
  error: 'danger',
};

export function DeploymentPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const [downloadLoading, setDownloadLoading] = useState(false);

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
      toast.success('Download started');
    } catch (err) {
      const msg = (err as { message?: string })?.message || 'Download failed';
      toast.error(msg);
    } finally {
      setDownloadLoading(false);
    }
  };

  if (!websiteId) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Deployment</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Download deployment packages for generated websites.</p>
        </div>
        <EmptyState
          title="No website selected"
          message="Generate a website first, then return here to download the deployment package."
          action={<Button variant="brand" onClick={() => navigate('/generation')}>Go to Generation</Button>}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton variant="text" width={200} height={24} />
        <Card variant="glass">
          <CardContent className="p-8 space-y-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} variant="text" width="100%" height={20} />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Deployment</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Download deployment packages for generated websites.</p>
        </div>
        <EmptyState
          title="Website not found"
          message="This generated website does not exist or you do not have access to it."
          action={<Button variant="outline" onClick={() => navigate('/generation')}>Back to Generation</Button>}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Deployment</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Download deployment packages for generated websites.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Package status */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>{website.project_name || 'Generated Website'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge tone={statusTone[website.status] ?? 'muted'}>{website.status}</Badge>
                <span className="text-[12px] text-[var(--color-text-muted)]">
                  Generated {formatRelative(website.created_at)}
                </span>
              </div>
            </div>

            {website.status === 'generated' || website.status === 'ready' ? (
              <div className="flex items-center gap-3 p-3 rounded-[10px] bg-[var(--color-success)]/5 border border-[var(--color-success)]/20">
                <CheckCircle2 className="size-5 text-[var(--color-success)] flex-shrink-0" />
                <div>
                  <p className="text-[13px] font-medium">Package ready</p>
                  <p className="text-[11.5px] text-[var(--color-text-muted)]">
                    The deployment package is ready for download.
                  </p>
                </div>
              </div>
            ) : website.status === 'failed' || website.status === 'error' ? (
              <div className="flex items-center gap-3 p-3 rounded-[10px] bg-[var(--color-danger)]/5 border border-[var(--color-danger)]/20">
                <AlertCircle className="size-5 text-[var(--color-danger)] flex-shrink-0" />
                <div>
                  <p className="text-[13px] font-medium">Generation failed</p>
                  <p className="text-[11.5px] text-[var(--color-text-muted)]">
                    The website generation did not complete successfully.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 p-3 rounded-[10px] bg-[var(--color-brand-soft)] border border-[var(--color-brand-border)]">
                <Loader2 className="size-5 text-[var(--color-brand)] lf-spin flex-shrink-0" />
                <div>
                  <p className="text-[13px] font-medium">Processing</p>
                  <p className="text-[11.5px] text-[var(--color-text-muted)]">
                    The website generation is in progress.
                  </p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4 pt-3 border-t border-[var(--color-border)]">
              <div>
                <p className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wider font-medium">Framework</p>
                <p className="text-[13px] mt-0.5">{website.framework}</p>
              </div>
              <div>
                <p className="text-[11px] text-[var(--color-text-muted)] uppercase tracking-wider font-medium">Package ID</p>
                <p className="text-[13px] mt-0.5 font-mono">{website.package_id || '—'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <Card variant="glass">
          <CardHeader>
            <CardTitle>Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              fullWidth
              variant="brand"
              leftIcon={<Download className="size-4" />}
              disabled={!hasArtifacts || downloadLoading}
              loading={downloadLoading}
              onClick={handleDownload}
            >
              {downloadLoading ? 'Starting...' : 'Download Package'}
            </Button>

            {!hasArtifacts && website.status !== 'failed' && website.status !== 'error' && (
              <p className="text-[11.5px] text-[var(--color-text-muted)] text-center">
                Package will be available once generation completes.
              </p>
            )}

            {website.status === 'failed' && (
              <p className="text-[11.5px] text-[var(--color-text-danger)] text-center">
                The generation failed. Please regenerate the website.
              </p>
            )}

            <div className="pt-3 border-t border-[var(--color-border)]">
              <Button
                fullWidth
                variant="outline"
                leftIcon={<ExternalLink className="size-4" />}
                onClick={() => navigate(`/preview/${websiteId}`)}
              >
                View Preview
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
