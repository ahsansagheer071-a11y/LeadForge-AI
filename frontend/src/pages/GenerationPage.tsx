import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Globe, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';

import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { projectsService, generateWebsite } from '@/services/services';
import { getApiErrorMessage } from '@/services/apiClient';
import { usePreviewStore } from '@/store';
import { cn } from '@/utils';
import { toast } from 'sonner';

export function GenerationPage() {
  const navigate = useNavigate();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [selectedId, setSelectedId] = useState('');

  const { data: page, isLoading } = useQuery({
    queryKey: ['leads'],
    queryFn: () => projectsService.list(1, 50),
  });

  const leads = page?.items ?? [];
  const selectedLead = leads.find((l) => l.id === selectedId) ?? null;

  const mutation = useMutation({
    mutationFn: () => generateWebsite(selectedId),
    onSuccess: (data) => {
      setHtmlContent(data.html);
      toast.success('Website generated successfully');
      navigate(`/preview/${data.website_id}`);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Generation failed'));
    },
  });

  const statusBadgeTone = (status: string) => {
    if (status.includes('READY')) return 'success' as const;
    if (status.includes('ANALYZED') || status.includes('SCORED')) return 'info' as const;
    if (status.includes('SCRAPED') || status.includes('DISCOVERED') || status.includes('NEW')) return 'brand' as const;
    return 'muted' as const;
  };

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      <div>
        <h1 className="text-[28px] font-extrabold tracking-tight text-white mb-1">AI Synthesis Core</h1>
        <p className="text-[13px] font-mono text-slate-400 uppercase tracking-widest">Generate immersive web properties from intelligence profiles</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lead selector */}
        <PremiumCard innerClassName="p-6 flex flex-col h-[600px]" className="lg:col-span-1">
          <div className="mb-4 pb-4 border-b border-slate-800">
            <h3 className="text-[14px] font-mono uppercase tracking-widest text-[#0ea5e9]">Target Selection</h3>
          </div>
          
          <div className="flex-1 overflow-y-auto space-y-2 lf-thin-scroll pr-2">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} variant="rounded" width="100%" height={60} delay={i * 60} className="bg-slate-800/50" />
                ))}
              </div>
            ) : leads.length > 0 ? (
              leads.map((lead) => (
                <button
                  key={lead.id}
                  onClick={() => setSelectedId(lead.id)}
                  className={cn(
                    'w-full text-left px-4 py-3 rounded-[12px] transition-all duration-200 group',
                    selectedId === lead.id
                      ? 'bg-gradient-to-r from-[#0ea5e9]/20 to-[#8b5cf6]/20 border-l-2 border-l-[#0ea5e9] shadow-[0_0_15px_rgba(14,165,233,0.1)]'
                      : 'bg-slate-900/50 border border-slate-800 hover:bg-slate-800 hover:border-slate-700',
                  )}
                >
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center justify-between">
                      <span className={cn("font-bold truncate text-[14px]", selectedId === lead.id ? "text-white" : "text-slate-300 group-hover:text-white")}>{lead.name}</span>
                      <Badge tone={statusBadgeTone(lead.status)} className="scale-90 font-mono origin-right">{lead.status.replace(/_/g, ' ')}</Badge>
                    </div>
                    {lead.website && (
                      <p className="text-[11px] font-mono text-slate-500 truncate">{lead.website}</p>
                    )}
                  </div>
                </button>
              ))
            ) : (
              <EmptyState title="No active targets" message="Discover and process targets first." />
            )}
          </div>

          {leads.length > 0 && (
            <div className="pt-5 mt-4 border-t border-slate-800">
              <div className="flex items-center justify-between text-[11px] font-mono uppercase text-slate-500 mb-3 tracking-wider">
                <span className="truncate pr-2">{selectedLead ? selectedLead.name : 'Awaiting Selection'}</span>
                {selectedLead?.rating != null && (
                  <span className="text-amber-500 flex-shrink-0">★ {selectedLead.rating.toFixed(1)}</span>
                )}
              </div>
              <button
                disabled={!selectedId || mutation.isPending}
                onClick={() => mutation.mutate()}
                className={cn(
                  "w-full flex items-center justify-center gap-2 py-3 rounded-[12px] text-[13px] font-mono uppercase tracking-widest font-bold transition-all duration-300",
                  (!selectedId || mutation.isPending) 
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                    : "bg-gradient-to-r from-[#8b5cf6] to-[#d946ef] text-white shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:shadow-[0_0_30px_rgba(139,92,246,0.5)]"
                )}
              >
                {mutation.isPending ? (
                   <><Loader2 className="size-4 animate-spin" /> Synthesizing...</>
                ) : (
                   <><Sparkles className="size-4" /> Initiate Generation</>
                )}
              </button>
            </div>
          )}
        </PremiumCard>

        {/* Status */}
        <PremiumCard featured={mutation.isPending} innerClassName="p-6 h-[600px] flex flex-col items-center justify-center relative overflow-hidden" className="lg:col-span-2">
          
          {/* Cyber background elements */}
          <div className="absolute inset-0 z-0 opacity-10 bg-[radial-gradient(circle_at_center,rgba(139,92,246,0.5)_0%,transparent_70%)] pointer-events-none" />
          
          <div className="relative z-10 w-full h-full flex flex-col items-center justify-center text-center">
            {!selectedId && (
              <div className="flex flex-col items-center animate-[lf-fade-in_0.5s_ease]">
                <Globe className="size-16 text-slate-700 mb-6 drop-shadow-[0_0_15px_rgba(255,255,255,0.05)]" />
                <p className="text-[13px] font-mono text-slate-500 uppercase tracking-widest max-w-xs leading-relaxed">
                  Select a target profile to initiate AI web synthesis protocol.
                </p>
              </div>
            )}

            {selectedId && mutation.isPending && (
              <div className="flex flex-col items-center">
                <div className="relative mb-8">
                  <div className="absolute inset-0 rounded-full bg-[#8b5cf6]/30 blur-2xl animate-pulse" />
                  <div className="absolute inset-0 border-t-2 border-[#d946ef] rounded-full animate-spin [animation-duration:3s]" />
                  <div className="absolute inset-2 border-b-2 border-[#0ea5e9] rounded-full animate-spin [animation-duration:2s] reverse" />
                  <div className="relative size-24 rounded-full bg-slate-900/80 border border-slate-700 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.3)] backdrop-blur-md">
                    <Loader2 className="size-8 text-white lf-spin" />
                  </div>
                </div>
                <h3 className="text-[20px] font-bold text-white mb-2 tracking-wide">Synthesizing Digital Presence</h3>
                <p className="text-[12px] font-mono text-[#0ea5e9] uppercase tracking-widest animate-pulse">Allocating Neural Resources...</p>
              </div>
            )}

            {selectedId && mutation.isSuccess && (
              <div className="flex flex-col items-center animate-[lf-fade-in_0.4s_ease]">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-full bg-[#10b981]/30 blur-xl" />
                  <div className="relative size-20 rounded-full bg-[#10b981]/20 border border-[#10b981]/50 flex items-center justify-center">
                    <CheckCircle2 className="size-10 text-[#10b981]" />
                  </div>
                </div>
                <h3 className="text-[24px] font-bold text-white mb-2">Synthesis Complete</h3>
                <p className="text-[13px] font-mono text-slate-400 mb-8 uppercase tracking-widest">Web property generated successfully.</p>
                <button
                  onClick={() => {
                    const data = mutation.data;
                    if (data) navigate(`/preview/${data.website_id}`);
                  }}
                  className="px-8 py-3 rounded-[12px] bg-[#10b981]/10 text-[#10b981] font-mono uppercase tracking-widest text-[13px] font-bold border border-[#10b981]/30 hover:bg-[#10b981]/20 hover:shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all"
                >
                  Enter Preview Mode
                </button>
              </div>
            )}

            {selectedId && mutation.isError && (
              <div className="flex flex-col items-center animate-[lf-fade-in_0.4s_ease]">
                <div className="relative mb-6">
                  <div className="absolute inset-0 rounded-full bg-red-500/30 blur-xl" />
                  <div className="relative size-20 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center">
                    <AlertCircle className="size-10 text-red-500" />
                  </div>
                </div>
                <h3 className="text-[20px] font-bold text-white mb-2">Synthesis Failed</h3>
                <p className="text-[13px] text-slate-400 mb-6 font-mono text-center max-w-sm">
                  {getApiErrorMessage(mutation.error, 'An unexpected error occurred.')}
                </p>
                <button 
                  onClick={() => mutation.mutate()}
                  className="px-6 py-2.5 rounded-[10px] bg-slate-800 text-white font-mono uppercase tracking-widest text-[12px] hover:bg-slate-700 transition-colors"
                >
                  Retry Generation
                </button>
              </div>
            )}
          </div>
        </PremiumCard>
      </div>
    </div>
  );
}
