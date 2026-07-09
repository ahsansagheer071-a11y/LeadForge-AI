import { ExternalLink, RefreshCw, Monitor, Smartphone, Tablet, Loader2, AlertCircle, Rocket } from 'lucide-react';
import { Skeleton } from '@/components/Loading';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { EmptyState } from '@/components/ErrorStates';
import { usePreviewStore } from '@/store';
import { generationService } from '@/services/services';
import { PremiumCard } from '@/components/PremiumCard';

type Viewport = 'desktop' | 'tablet' | 'mobile';

export function PreviewPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const { htmlContent: storeHtml } = usePreviewStore();
  const [viewport, setViewport] = useState<Viewport>('desktop');

  const { data: website, isLoading, error } = useQuery({
    queryKey: ['generated-website', websiteId],
    queryFn: () => generationService.getById(websiteId!),
    enabled: !!websiteId,
  });

  const htmlContent = website?.html ?? storeHtml;
  const hasPreview = !!htmlContent;

  const vpClasses: Record<Viewport, string> = {
    desktop: 'w-full',
    tablet: 'w-[768px]',
    mobile: 'w-[375px]',
  };

  const handleReload = () => {
    if (websiteId) {
      window.location.reload();
    }
  };

  const handleOpenInTab = () => {
    if (htmlContent) {
      const win = window.open('', '_blank');
      if (win) {
        win.document.write(htmlContent);
        win.document.close();
      }
    }
  };

  if (websiteId && isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <Skeleton variant="text" width={200} height={32} className="bg-slate-800" />
          <Skeleton variant="text" width={300} height={16} className="mt-2 bg-slate-800" />
        </div>
        <PremiumCard innerClassName="p-16 flex items-center justify-center h-[600px]">
          <div className="flex flex-col items-center justify-center text-center">
            <Loader2 className="size-10 text-[#0ea5e9] animate-spin mb-6" />
            <p className="text-[14px] font-mono uppercase tracking-widest text-slate-300">Establishing Neural Link...</p>
          </div>
        </PremiumCard>
      </div>
    );
  }

  if (websiteId && error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Preview Simulator</h1>
          <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Validate generated digital assets</p>
        </div>
        <PremiumCard innerClassName="p-16">
          <div className="flex flex-col items-center justify-center text-center">
            <AlertCircle className="size-16 text-red-500 mb-6 drop-shadow-[0_0_15px_rgba(239,68,68,0.4)]" />
            <p className="text-[18px] font-bold text-white mb-2">Simulation Failed</p>
            <p className="text-[13px] font-mono text-slate-400 mb-8 max-w-md">
              Asset could not be loaded into the simulation environment. Verify access protocols or regenerate.
            </p>
            <button onClick={() => navigate('/generation')} className="px-6 py-2.5 rounded-[10px] bg-slate-800 text-white font-mono uppercase tracking-widest text-[12px] hover:bg-slate-700 transition-colors">
              Return to Core
            </button>
          </div>
        </PremiumCard>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease] flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">Preview Simulator</h1>
          <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Validate generated digital assets</p>
        </div>
        {hasPreview && (
          <div className="flex items-center gap-3">
            <button onClick={handleReload} className="flex items-center gap-2 px-4 py-2 rounded-[10px] bg-slate-800 border border-slate-700 text-white font-mono uppercase tracking-wider text-[11px] hover:bg-slate-700 transition-colors">
              <RefreshCw size={14} /> Sync
            </button>
            <button onClick={handleOpenInTab} className="flex items-center gap-2 px-4 py-2 rounded-[10px] bg-[#0ea5e9]/10 border border-[#0ea5e9]/30 text-[#0ea5e9] font-mono uppercase tracking-wider text-[11px] hover:bg-[#0ea5e9]/20 transition-colors">
              <ExternalLink size={14} /> Fullscreen
            </button>
            {websiteId && (
               <button onClick={() => navigate(`/deployment/${websiteId}`)} className="flex items-center gap-2 px-5 py-2 rounded-[10px] bg-gradient-to-r from-[#10b981] to-[#059669] text-white font-mono uppercase tracking-widest text-[12px] font-bold shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all">
                 <Rocket size={14} /> Deploy
               </button>
            )}
          </div>
        )}
      </div>

      {hasPreview && (
        <div className="flex items-center justify-center bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-[12px] p-1.5 w-fit mx-auto">
          {(['desktop', 'tablet', 'mobile'] as const).map((v) => (
            <button
              key={v}
              onClick={() => setViewport(v)}
              className={cn(
                'flex items-center gap-2 px-6 py-2 rounded-[8px] text-[12px] font-mono uppercase tracking-widest font-bold transition-all duration-300',
                viewport === v
                  ? 'bg-gradient-to-r from-[#8b5cf6]/20 to-[#d946ef]/20 text-white shadow-[0_0_10px_rgba(139,92,246,0.2)]'
                  : 'text-slate-500 hover:text-slate-300',
              )}
            >
              {v === 'desktop' && <Monitor size={14} />}
              {v === 'tablet' && <Tablet size={14} />}
              {v === 'mobile' && <Smartphone size={14} />}
              {v}
            </button>
          ))}
        </div>
      )}

      <div className="flex-1 min-h-0">
        <PremiumCard innerClassName="p-2 h-full flex flex-col relative" featured>
           {/* Scanline overlay for cyber effect, positioned above iframe */}
           <div className="absolute inset-0 pointer-events-none z-10 opacity-[0.06]" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(255,255,255,0.06) 1px, rgba(255,255,255,0.06) 3px)' }} />
           
          {hasPreview ? (
            <div className="flex-1 w-full flex justify-center bg-black rounded-[14px] p-4 overflow-y-auto lf-thin-scroll relative z-20">
              <div className={cn('h-full bg-white rounded-[8px] overflow-hidden shadow-2xl transition-all duration-500 ease-in-out origin-top border border-slate-700', vpClasses[viewport])}>
                <iframe
                  title="Generated Asset Simulation"
                  srcDoc={htmlContent}
                  style={{ width: '100%', height: '100%', border: 'none' }}
                  className="bg-white"
                />
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 z-20">
              <EmptyState
                title="Simulation Offline"
                message="Generate a digital asset first to engage the simulation environment."
              />
            </div>
          )}
        </PremiumCard>
      </div>
    </div>
  );
}