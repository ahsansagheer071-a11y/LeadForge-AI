import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe, MapPin, Phone, Star, Building, Play, Shield, AlertTriangle, CheckCircle, Search, Camera, Send, Copy, ExternalLink } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { projectsService, generateWebsite, auditService, analysisService, screenshotService, outreachService, generationService } from '@/services/services';
import { getApiErrorMessage } from '@/services/apiClient';
import { usePreviewStore } from '@/store';
import { formatRelative } from '@/utils';
import { toast } from 'sonner';
import type { AuditAndScoreResult, WebsiteAnalysisResponse, CaptureScreenshotResponse, OutreachResponse } from '@/types';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info',
  SCRAPED: 'brand',
  ANALYZED: 'warning',
  OUTREACH_READY: 'success',
  CONTACTED: 'brand',
  CLOSED: 'success',
};

const scoreTone = (cat: string): 'success' | 'warning' | 'muted' => {
  if (cat === 'Hot Lead') return 'success';
  if (cat === 'Warm Lead') return 'warning';
  return 'muted';
};

export function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const setHtmlContent = usePreviewStore((s) => s.setHtmlContent);
  const [analysisResult, setAnalysisResult] = useState<WebsiteAnalysisResponse | null>(null);
  const [auditResult, setAuditResult] = useState<AuditAndScoreResult | null>(null);
  const [screenshotResult, setScreenshotResult] = useState<CaptureScreenshotResponse | null>(null);
  const [outreachResult, setOutreachResult] = useState<OutreachResponse | null>(null);

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
        if (lead.audit.executive_summary) {
          reconstructed['Business Summary'] = lead.audit.executive_summary;
        }
        if (lead.audit.weaknesses && Array.isArray(lead.audit.weaknesses)) {
          reconstructed['Top Weaknesses'] = lead.audit.weaknesses;
        }
        if (lead.audit.verdict) {
          reconstructed['Overall Summary'] = lead.audit.verdict;
        }
        setAuditResult({
          lead_id: lead.id,
          audit: Object.keys(reconstructed).length > 0 ? reconstructed : { 'Overall Summary': lead.audit.verdict || 'Audit data available' },
          score: lead.score,
        });
      }
    }
  }, [lead]);

  const generateMutation = useMutation({
    mutationFn: () => generateWebsite(id!),
    onSuccess: (data) => {
      if (!data?.website_id) {
        toast.error('Generation failed — no website ID returned');
        return;
      }
      setHtmlContent(data.html);
      toast.success('Website generated successfully');
      navigate(`/preview/${data.website_id}`);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Generation failed'));
    },
  });

  const analysisMutation = useMutation({
    mutationFn: () => analysisService.analyzeWebsite(id!),
    onSuccess: (result) => {
      setAnalysisResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('Website analyzed successfully');
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Analysis failed'));
    },
  });

  const auditMutation = useMutation({
    mutationFn: () => auditService.run({ lead_id: id! }),
    onSuccess: (result) => {
      setAuditResult(result);
      toast.success(`Audit complete — Score: ${result.score.overall_score}/100 (${result.score.category})`);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Audit failed'));
    },
  });

  const screenshotMutation = useMutation({
    mutationFn: () => screenshotService.capture({ lead_id: id! }),
    onSuccess: (result) => {
      setScreenshotResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('Screenshots captured successfully');
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Screenshot capture failed'));
    },
  });

  const outreachMutation = useMutation({
    mutationFn: () => outreachService.generate({ lead_id: id! }),
    onSuccess: (result) => {
      setOutreachResult(result);
      queryClient.invalidateQueries({ queryKey: ['lead', id] });
      toast.success('AI Outreach generated successfully');
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Outreach generation failed'));
    },
  });

  const copyToClipboard = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success(`${label} copied to clipboard`);
    } catch {
      toast.error('Failed to copy');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton variant="rounded" width={200} height={24} />
        <PremiumCard variant="glass">
          <div className="p-6 space-y-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} variant="text" width="100%" height={20} />
            ))}
          </div>
        </PremiumCard>
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
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/projects')} className="text-slate-400 hover:text-white">
          <ArrowLeft className="size-4 mr-1" /> Back to Pipeline
        </Button>
      </div>

      <PremiumCard featured innerClassName="p-8 bg-gradient-to-br from-[#0a0f1a] to-[#040810]">
        <div className="flex flex-col lg:flex-row justify-between gap-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Badge tone={statusTone[lead.status] ?? 'muted'} className="font-mono">{lead.status.replace('_', ' ')}</Badge>
              <span className="text-[12px] font-mono text-[#0ea5e9] tracking-wider uppercase">{lead.industry}</span>
            </div>
            <h1 className="text-[clamp(2rem,3vw,2.5rem)] font-extrabold tracking-tight text-white mb-2">{lead.name}</h1>
            <div className="flex items-center gap-4 text-[13px] text-slate-400 font-mono">
              {lead.city && lead.country && <span><MapPin className="inline size-3.5 mr-1 text-[#0ea5e9]" />{lead.city}, {lead.country}</span>}
              {lead.website && <span><Globe className="inline size-3.5 mr-1 text-[#0ea5e9]" />{lead.website}</span>}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3 items-start justify-start lg:justify-end">
             {/* Workflow Buttons */}
             <button
               onClick={() => screenshotMutation.mutate()}
               disabled={screenshotMutation.isPending}
               className={`flex items-center gap-2 px-4 py-2 rounded-[10px] text-[12px] font-mono uppercase tracking-widest transition-all border ${screenshotResult ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30' : 'bg-slate-800/50 text-slate-300 border-slate-700 hover:border-[#0ea5e9] hover:text-[#0ea5e9]'}`}
             >
               <Camera size={14} /> {screenshotMutation.isPending ? 'Working...' : 'Screenshot'}
             </button>
             
             <button
               onClick={() => analysisMutation.mutate()}
               disabled={analysisMutation.isPending}
               className={`flex items-center gap-2 px-4 py-2 rounded-[10px] text-[12px] font-mono uppercase tracking-widest transition-all border ${analysisResult ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30' : 'bg-slate-800/50 text-slate-300 border-slate-700 hover:border-[#0ea5e9] hover:text-[#0ea5e9]'}`}
             >
               <Search size={14} /> {analysisMutation.isPending ? 'Working...' : 'Analyze'}
             </button>

             <button
               onClick={() => auditMutation.mutate()}
               disabled={auditMutation.isPending}
               className={`flex items-center gap-2 px-4 py-2 rounded-[10px] text-[12px] font-mono uppercase tracking-widest transition-all border ${auditResult ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30' : 'bg-slate-800/50 text-slate-300 border-slate-700 hover:border-[#0ea5e9] hover:text-[#0ea5e9]'}`}
             >
               <Shield size={14} /> {auditMutation.isPending ? 'Working...' : 'Audit'}
             </button>

             <button
               onClick={() => {
                 if (existingWebsite) { navigate(`/preview/${existingWebsite.id}`); } 
                 else { generateMutation.mutate(); }
               }}
               disabled={generateMutation.isPending}
               className={`flex items-center gap-2 px-6 py-2 rounded-[10px] text-[12px] font-mono uppercase tracking-widest transition-all shadow-[0_0_15px_rgba(14,165,233,0.3)] ${existingWebsite ? 'bg-gradient-to-r from-[#8b5cf6] to-[#d946ef] text-white border-transparent' : 'bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white border-transparent'}`}
             >
               {existingWebsite ? <ExternalLink size={14} /> : <Play size={14} />}
               {generateMutation.isPending ? 'Generating...' : existingWebsite ? 'View Website' : 'Generate Website'}
             </button>

             <button
               onClick={() => outreachMutation.mutate()}
               disabled={outreachMutation.isPending}
               className={`flex items-center gap-2 px-4 py-2 rounded-[10px] text-[12px] font-mono uppercase tracking-widest transition-all border ${outreachResult ? 'bg-[#10b981]/10 text-[#10b981] border-[#10b981]/30' : 'bg-slate-800/50 text-slate-300 border-slate-700 hover:border-[#0ea5e9] hover:text-[#0ea5e9]'}`}
             >
               <Send size={14} /> {outreachMutation.isPending ? 'Working...' : 'Outreach'}
             </button>
          </div>
        </div>
      </PremiumCard>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PremiumCard innerClassName="p-6">
          <h3 className="text-[12px] font-mono uppercase tracking-widest text-slate-400 mb-4 border-b border-slate-800 pb-2">Target Profile</h3>
          <div className="space-y-3 font-mono text-[13px]">
            {lead.website && <div className="flex gap-2"><Globe className="text-[#0ea5e9] size-4" /><span className="text-white truncate">{lead.website}</span></div>}
            {lead.phone && <div className="flex gap-2"><Phone className="text-[#0ea5e9] size-4" /><span className="text-white">{lead.phone}</span></div>}
            {lead.address && <div className="flex gap-2"><MapPin className="text-[#0ea5e9] size-4" /><span className="text-white">{lead.address}</span></div>}
            <div className="flex gap-2"><Building className="text-[#0ea5e9] size-4" /><span className="text-white">{lead.city}, {lead.country}</span></div>
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-6">
          <h3 className="text-[12px] font-mono uppercase tracking-widest text-slate-400 mb-4 border-b border-slate-800 pb-2">Reputation Index</h3>
          <div className="flex items-center gap-3">
             <div className="size-16 rounded-[12px] border border-amber-500/30 bg-amber-500/10 flex items-center justify-center">
               <Star className="size-8 text-amber-500 fill-amber-500" />
             </div>
             <div>
               <div className="text-[28px] font-bold text-white leading-none">{lead.rating?.toFixed(1) ?? '--'}</div>
               <div className="text-[12px] font-mono text-slate-400 mt-1">{lead.reviews_count ?? 0} confirmed reviews</div>
             </div>
          </div>
        </PremiumCard>

        <PremiumCard innerClassName="p-6">
          <h3 className="text-[12px] font-mono uppercase tracking-widest text-slate-400 mb-4 border-b border-slate-800 pb-2">Timeline</h3>
          <div className="space-y-3 font-mono text-[12px]">
            <div className="flex justify-between border-b border-slate-800/50 pb-2">
              <span className="text-slate-500">First Discovered</span>
              <span className="text-white">{formatRelative(lead.created_at)}</span>
            </div>
            <div className="flex justify-between pb-2">
              <span className="text-slate-500">Last Intel Update</span>
              <span className="text-[#0ea5e9]">{formatRelative(lead.updated_at)}</span>
            </div>
          </div>
        </PremiumCard>
      </div>

      {/* Audit Results */}
      {auditResult && (
        <PremiumCard featured innerClassName="p-8">
           <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
             <h3 className="text-[16px] font-mono uppercase tracking-widest text-white flex items-center gap-3">
               <Shield className="text-[#8b5cf6]" /> AI Intelligence Audit
             </h3>
             <Badge tone={scoreTone(auditResult.score.category)} className="font-mono text-[14px] px-3 py-1">
               {auditResult.score.category}
             </Badge>
           </div>
           
           <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
              {[
                { label: 'Overall', value: auditResult.score.overall_score },
                { label: 'SEO', value: auditResult.score.seo_score },
                { label: 'UX', value: auditResult.score.ux_score },
                { label: 'Brand', value: auditResult.score.branding_score },
                { label: 'Trust', value: auditResult.score.trust_score },
                { label: 'Conv.', value: auditResult.score.conversion_score },
              ].map((s, i) => (
                <div key={s.label} className="text-center p-4 rounded-[12px] bg-slate-800/50 border border-slate-700">
                  <div className={`text-[28px] font-bold ${i === 0 ? 'text-[#8b5cf6] drop-shadow-[0_0_10px_rgba(139,92,246,0.5)]' : 'text-white'}`}>{s.value}</div>
                  <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 mt-1">{s.label}</div>
                </div>
              ))}
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {auditResult.audit && typeof auditResult.audit === 'object' && 'Business Summary' in auditResult.audit && (
                <div>
                  <h4 className="text-[12px] font-mono uppercase tracking-widest text-[#0ea5e9] mb-3">Business Profile</h4>
                  <p className="text-[14px] text-slate-300 leading-relaxed font-sans">{String(auditResult.audit['Business Summary'])}</p>
                </div>
              )}
              {auditResult.audit && typeof auditResult.audit === 'object' && 'Overall Summary' in auditResult.audit && (
                <div>
                  <h4 className="text-[12px] font-mono uppercase tracking-widest text-[#0ea5e9] mb-3">Audit Verdict</h4>
                  <p className="text-[14px] text-slate-300 leading-relaxed font-sans">{String(auditResult.audit['Overall Summary'])}</p>
                </div>
              )}
           </div>

           {auditResult.audit && typeof auditResult.audit === 'object' && 'Top Weaknesses' in auditResult.audit && Array.isArray(auditResult.audit['Top Weaknesses']) && (
             <div className="mt-8 pt-6 border-t border-slate-800">
               <h4 className="text-[12px] font-mono uppercase tracking-widest text-[#ef4444] mb-4">Identified Vulnerabilities</h4>
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 {(auditResult.audit['Top Weaknesses'] as Array<string | { title?: string; evidence?: string; impact?: string; recommendation?: string }>).map((w, i) => {
                    const weakness = typeof w === 'string' ? { title: w } : w;
                    return (
                      <div key={i} className="p-4 rounded-[12px] bg-red-500/5 border border-red-500/20">
                        <p className="text-[14px] font-bold text-white mb-2 flex items-center gap-2"><AlertTriangle size={14} className="text-red-500"/> {weakness.title}</p>
                        {weakness.impact && <p className="text-[12px] text-slate-400 mb-2">{weakness.impact}</p>}
                        {weakness.recommendation && <p className="text-[12px] text-[#10b981] font-mono flex items-start gap-2"><CheckCircle size={14} className="shrink-0 mt-0.5"/> {weakness.recommendation}</p>}
                      </div>
                    )
                 })}
               </div>
             </div>
           )}
        </PremiumCard>
      )}

      {/* Website Analysis Results */}
      {analysisResult && (
        <PremiumCard innerClassName="p-8">
           <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
             <h3 className="text-[16px] font-mono uppercase tracking-widest text-white flex items-center gap-3">
               <Search className="text-[#0ea5e9]" /> Technical Analysis
             </h3>
           </div>
           <div className="grid grid-cols-2 md:grid-cols-4 gap-6 font-mono text-[12px]">
             <div>
               <span className="block text-slate-500 mb-1">HTTP Status</span>
               <span className="text-white text-[18px]">{analysisResult.http_status_code}</span>
             </div>
             <div>
               <span className="block text-slate-500 mb-1">Response Time</span>
               <span className="text-[#0ea5e9] text-[18px]">{analysisResult.response_time_ms}ms</span>
             </div>
             <div>
               <span className="block text-slate-500 mb-1">Page Weight</span>
               <span className="text-white text-[18px]">{analysisResult.html_size_kb?.toFixed(1)} KB</span>
             </div>
             <div>
               <span className="block text-slate-500 mb-1">Security</span>
               <span className={analysisResult.https_enabled ? "text-[#10b981] text-[18px]" : "text-red-500 text-[18px]"}>{analysisResult.https_enabled ? 'HTTPS' : 'INSECURE'}</span>
             </div>
             
             {/* Tech breakdown */}
             <div className="col-span-2 md:col-span-4 grid grid-cols-5 gap-4 mt-4 pt-4 border-t border-slate-800">
                <div className="text-center"><div className="text-[24px] text-white">{analysisResult.h1_count}</div><div className="text-slate-500">H1 Tags</div></div>
                <div className="text-center"><div className="text-[24px] text-white">{analysisResult.h2_count}</div><div className="text-slate-500">H2 Tags</div></div>
                <div className="text-center"><div className="text-[24px] text-white">{analysisResult.total_paragraphs}</div><div className="text-slate-500">Paragraphs</div></div>
                <div className="text-center"><div className="text-[24px] text-white">{analysisResult.total_images}</div><div className="text-slate-500">Images</div></div>
                <div className="text-center"><div className="text-[24px] text-white">{analysisResult.total_forms}</div><div className="text-slate-500">Forms</div></div>
             </div>
           </div>
        </PremiumCard>
      )}

      {/* Screenshot Results */}
      {screenshotResult && (screenshotResult.desktop_url || screenshotResult.mobile_url) && (
        <PremiumCard innerClassName="p-8">
           <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
             <h3 className="text-[16px] font-mono uppercase tracking-widest text-white flex items-center gap-3">
               <Camera className="text-[#0ea5e9]" /> Visual Capture
             </h3>
           </div>
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             {screenshotResult.desktop_url && (
                <div>
                  <p className="text-[12px] font-mono uppercase tracking-widest text-slate-400 mb-2">Desktop Viewport</p>
                  <img src={screenshotResult.desktop_url} alt="Desktop" className="w-full rounded-[12px] border border-slate-700 shadow-xl" />
                </div>
             )}
             {screenshotResult.mobile_url && (
                <div>
                  <p className="text-[12px] font-mono uppercase tracking-widest text-slate-400 mb-2">Mobile Viewport</p>
                  <img src={screenshotResult.mobile_url} alt="Mobile" className="w-full max-w-[300px] mx-auto rounded-[12px] border border-slate-700 shadow-xl" />
                </div>
             )}
           </div>
        </PremiumCard>
      )}

      {/* Outreach Results */}
      {outreachResult && (
        <PremiumCard featured innerClassName="p-8">
           <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-4">
             <h3 className="text-[16px] font-mono uppercase tracking-widest text-white flex items-center gap-3">
               <Send className="text-[#10b981]" /> AI Generated Outreach
             </h3>
           </div>
           
           <div className="space-y-6">
             {outreachResult.cold_email && (
               <div className="bg-slate-800/50 rounded-[12px] border border-slate-700 p-5">
                 <div className="flex justify-between items-center mb-3">
                   <span className="text-[12px] font-mono uppercase text-[#10b981]">Cold Email Draft</span>
                   <button onClick={() => copyToClipboard(outreachResult.cold_email!, 'Cold email')} className="text-slate-400 hover:text-white"><Copy size={14}/></button>
                 </div>
                 <p className="text-[14px] text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{outreachResult.cold_email}</p>
               </div>
             )}
             
             {outreachResult.linkedin_message && (
               <div className="bg-slate-800/50 rounded-[12px] border border-slate-700 p-5">
                 <div className="flex justify-between items-center mb-3">
                   <span className="text-[12px] font-mono uppercase text-[#0ea5e9]">LinkedIn Strategy</span>
                   <button onClick={() => copyToClipboard(outreachResult.linkedin_message!, 'LinkedIn')} className="text-slate-400 hover:text-white"><Copy size={14}/></button>
                 </div>
                 <p className="text-[14px] text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">{outreachResult.linkedin_message}</p>
               </div>
             )}
           </div>
        </PremiumCard>
      )}

    </div>
  );
}
