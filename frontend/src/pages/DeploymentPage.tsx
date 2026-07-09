import { Download, Loader2, AlertCircle, CheckCircle2, Archive, Play } from 'lucide-react';
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
      toast.success('Download sequence initiated');
    } catch (err) {
      const msg = (err as { message?: string })?.message || 'Download failed';
      toast.error(msg);
    } finally {
      setDownloadLoading(false);
    }
  };

  if (!websiteId) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Deployment Center</h1>
          <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Extract and distribute synthesized assets</p>
        </div>
        <EmptyState
          title="No target selected"
          message="Initialize generation protocols first to create deployment artifacts."
          action={<Button variant="brand" onClick={() => navigate('/generation')}>Go to Generation</Button>}
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <Skeleton variant="text" width={240} height={32} className="bg-slate-800" />
          <Skeleton variant="text" width={340} height={16} className="mt-2 bg-slate-800" />
        </div>
        <PremiumCard innerClassName="p-8 space-y-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} variant="rounded" width="100%" height={80} className="bg-slate-800/50" />
          ))}
        </PremiumCard>
      </div>
    );
  }

  if (error || !website) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Deployment Center</h1>
          <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Extract and distribute synthesized assets</p>
        </div>
        <EmptyState
          title="Asset not located"
          message="The requested deployment package does not exist or access is restricted."
          action={<Button variant="outline" onClick={() => navigate('/generation')}>Return to Generation</Button>}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      <div>
        <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Deployment Center</h1>
        <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Extract and distribute synthesized assets</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Package status */}
        <PremiumCard featured={hasArtifacts} className="lg:col-span-2" innerClassName="p-8 flex flex-col justify-between min-h-[400px]">
          <div>
            <div className="flex items-center justify-between mb-8 pb-4 border-b border-slate-800">
               <div>
                 <h2 className="text-[20px] font-bold text-white mb-1">{website.project_name || 'Generated Website'}</h2>
                 <p className="text-[12px] font-mono text-slate-500 uppercase tracking-wider">Asset ID: {website.package_id || website.id}</p>
               </div>
               <Badge tone={statusTone[website.status] ?? 'muted'} className="font-mono px-3 py-1 text-[13px] shadow-lg">{website.status}</Badge>
            </div>

            {website.status === 'generated' || website.status === 'ready' ? (
              <div className="flex items-center gap-6 p-6 rounded-[16px] bg-[#10b981]/5 border border-[#10b981]/20">
                <div className="size-16 rounded-full bg-[#10b981]/20 border border-[#10b981]/50 flex items-center justify-center shrink-0 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 className="size-8 text-[#10b981]" />
                </div>
                <div>
                  <p className="text-[18px] font-bold text-white mb-1">Artifacts Ready</p>
                  <p className="text-[13px] font-mono text-slate-400">
                    Deployment package compiled and ready for secure extraction.
                  </p>
                </div>
              </div>
            ) : website.status === 'failed' || website.status === 'error' ? (
              <div className="flex items-center gap-6 p-6 rounded-[16px] bg-red-500/5 border border-red-500/20">
                <div className="size-16 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center shrink-0 shadow-[0_0_20px_rgba(239,68,68,0.3)]">
                  <AlertCircle className="size-8 text-red-500" />
                </div>
                <div>
                  <p className="text-[18px] font-bold text-white mb-1">Compilation Failed</p>
                  <p className="text-[13px] font-mono text-slate-400">
                    An anomaly occurred during asset synthesis. Check system logs.
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-6 p-6 rounded-[16px] bg-[#0ea5e9]/5 border border-[#0ea5e9]/20 relative overflow-hidden">
                <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent,rgba(14,165,233,0.1),transparent)] -translate-x-full animate-[lf-shimmer_2s_infinite]" />
                <div className="size-16 rounded-full bg-[#0ea5e9]/20 border border-[#0ea5e9]/50 flex items-center justify-center shrink-0 shadow-[0_0_20px_rgba(14,165,233,0.3)]">
                  <Loader2 className="size-8 text-[#0ea5e9] animate-spin" />
                </div>
                <div>
                  <p className="text-[18px] font-bold text-white mb-1">Processing Package</p>
                  <p className="text-[13px] font-mono text-slate-400">
                    Compilation and minification in progress. Please hold.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-6 pt-6 border-t border-slate-800 mt-8">
            <div className="bg-slate-900/50 rounded-[12px] p-4 border border-slate-800">
              <p className="text-[11px] font-mono text-slate-500 uppercase tracking-widest mb-1">Architecture</p>
              <p className="text-[16px] font-bold text-[#0ea5e9]">{website.framework}</p>
            </div>
            <div className="bg-slate-900/50 rounded-[12px] p-4 border border-slate-800">
              <p className="text-[11px] font-mono text-slate-500 uppercase tracking-widest mb-1">Generated</p>
              <p className="text-[14px] font-medium text-white">{formatRelative(website.created_at)}</p>
            </div>
          </div>
        </PremiumCard>

        {/* Actions */}
        <PremiumCard innerClassName="p-8 flex flex-col justify-between">
           <div>
              <h3 className="text-[14px] font-mono uppercase tracking-widest text-[#8b5cf6] mb-6 pb-2 border-b border-slate-800 flex items-center gap-2">
                 <Archive size={16} /> Operations
              </h3>

              <div className="space-y-4">
                <button
                  disabled={!hasArtifacts || downloadLoading}
                  onClick={handleDownload}
                  className={cn(
                    "w-full flex items-center justify-center gap-3 py-4 rounded-[12px] text-[13px] font-mono uppercase tracking-widest font-bold transition-all duration-300",
                    !hasArtifacts 
                      ? "bg-slate-800/50 text-slate-500 border border-slate-700 cursor-not-allowed"
                      : downloadLoading 
                        ? "bg-[#0ea5e9]/20 text-[#0ea5e9] border border-[#0ea5e9]/50 cursor-wait"
                        : "bg-gradient-to-r from-[#0ea5e9] to-[#3b82f6] text-white shadow-[0_0_20px_rgba(14,165,233,0.4)] hover:shadow-[0_0_30px_rgba(14,165,233,0.6)] hover:-translate-y-1"
                  )}
                >
                  {downloadLoading ? <Loader2 size={16} className="animate-spin"/> : <Download size={16} />}
                  {downloadLoading ? 'Extracting...' : 'Download Package'}
                </button>
                
                <button
                   onClick={() => navigate(`/preview/${websiteId}`)}
                   className="w-full flex items-center justify-center gap-3 py-3 rounded-[12px] bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 transition-all text-white font-mono uppercase tracking-widest text-[12px]"
                >
                  <Play size={14} /> Enter Preview
                </button>
              </div>
           </div>

           <div className="mt-8 pt-6 border-t border-slate-800 text-center">
             {!hasArtifacts && website.status !== 'failed' && website.status !== 'error' && (
               <p className="text-[11px] font-mono text-slate-500 uppercase tracking-widest">
                 Extraction protocols unlock upon completion.
               </p>
             )}
             {website.status === 'failed' && (
               <p className="text-[11px] font-mono text-red-500 uppercase tracking-widest">
                 Critical error. Abort operation.
               </p>
             )}
           </div>
        </PremiumCard>
      </div>
    </div>
  );
}
