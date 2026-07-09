import { useState } from 'react';
import { Activity, Users, Search } from 'lucide-react';

import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Input, Label } from '@/components/Input';

import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { projectsService, leadDiscoveryService } from '@/services/services';
import { getApiErrorMessage } from '@/services/apiClient';
import { formatRelative, scoreTier } from '@/utils';
import type { LeadDiscoveryRequest } from '@/types';
import { toast } from 'sonner';

const statusTone: Record<string, 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  NEW: 'info',
  SCRAPED: 'brand',
  ANALYZED: 'warning',
  OUTREACH_READY: 'success',
  CONTACTED: 'brand',
  CLOSED: 'success',
  draft: 'muted',
  queued: 'info',
  generating: 'info',
  previewing: 'warning',
  deployed: 'success',
  failed: 'danger',
  archived: 'neutral',
};

function ScoreBadgeInner({ score }: { score: number | null | undefined }) {
  if (score == null) return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] border border-[var(--color-border)]">&mdash;</span>;
  const tier = scoreTier(score);
  const cls = tier === 'hot' ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/25'
    : tier === 'warm' ? 'bg-amber-500/15 text-amber-500 border-amber-500/25'
    : 'bg-gray-500/15 text-gray-500 border-gray-500/25';
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-bold border ${cls}`}>{Math.round(score)}</span>;
}

export function ProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: paginated, isLoading, error } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsService.list(),
  });

  const projects = paginated?.items ?? [];
  const [search, setSearch] = useState('');

  const filtered = projects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()),
  );

  const discoveryMutation = useMutation({
    mutationFn: (data: LeadDiscoveryRequest) => leadDiscoveryService.discover(data),
    onSuccess: (data) => {
      toast.success(`Discovered ${data.created} lead(s), skipped ${data.skipped_duplicates} duplicate(s).`);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err, 'Discovery failed'));
    },
  });

  const [discoveryForm, setDiscoveryForm] = useState<LeadDiscoveryRequest>({
    business_type: '',
    city: '',
    country: '',
  });

  const handleDiscoveryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setDiscoveryForm(prev => ({ ...prev, [name]: value }));
  };

  const handleDiscoverySubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!discoveryForm.business_type || !discoveryForm.city || !discoveryForm.country) {
      toast.error('Please fill in all discovery fields');
      return;
    }
    discoveryMutation.mutate(discoveryForm);
  };

  return (
    <div className="space-y-8 animate-[lf-fade-in_0.22s_ease]">
      {/* ── Header ─── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[var(--color-border)]">
        <div>
          <h1 className="text-[clamp(2rem,4vw,2.5rem)] font-extrabold tracking-tight text-white mb-2">Target <span className="bg-gradient-to-r from-[#0ea5e9] to-[#8b5cf6] bg-clip-text text-transparent">Discovery</span></h1>
          <p className="text-[14px] text-slate-400 font-mono">Manage pipeline and initiate new intelligence gathering.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-[var(--color-text-muted)]" />
            <Input
              placeholder="Search targets..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 bg-[#0f172a] border-slate-700 w-[240px] focus:ring-[#0ea5e9]"
            />
          </div>
        </div>
      </div>

      {/* Discovery Form */}
      <PremiumCard featured innerClassName="p-6 md:p-8 bg-gradient-to-br from-[#0a0f1a] to-[#040810]">
        <div className="flex items-center gap-3 mb-6">
          <div className="size-10 rounded-[12px] bg-gradient-to-br from-[#0ea5e9] to-[#8b5cf6] flex items-center justify-center shadow-[0_0_15px_rgba(14,165,233,0.4)]">
            <Search className="text-white size-5" />
          </div>
          <div>
            <h2 className="text-[16px] font-bold text-white uppercase tracking-wider font-mono">Initialize Scan</h2>
            <p className="text-[12px] text-slate-400 font-mono">Enter parameters to locate new high-value targets</p>
          </div>
        </div>
        <form onSubmit={handleDiscoverySubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <Label htmlFor="business_type" className="text-[12px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">Business Vertical</Label>
              <Input
                id="business_type"
                name="business_type"
                value={discoveryForm.business_type}
                onChange={handleDiscoveryChange}
                placeholder="e.g. Cyber Security, Healthcare"
                required
                className="bg-[#0f172a] border-slate-700 h-12 text-[14px]"
              />
            </div>
            <div>
              <Label htmlFor="city" className="text-[12px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">City / Region</Label>
              <Input
                id="city"
                name="city"
                value={discoveryForm.city}
                onChange={handleDiscoveryChange}
                placeholder="e.g. New York"
                required
                className="bg-[#0f172a] border-slate-700 h-12 text-[14px]"
              />
            </div>
            <div>
              <Label htmlFor="country" className="text-[12px] uppercase font-mono tracking-wider text-[#0ea5e9] mb-2 block">Territory</Label>
              <Input
                id="country"
                name="country"
                value={discoveryForm.country}
                onChange={handleDiscoveryChange}
                placeholder="e.g. USA"
                required
                className="bg-[#0f172a] border-slate-700 h-12 text-[14px]"
              />
            </div>
          </div>
          <div className="flex justify-end pt-2 border-t border-slate-800">
            <button 
              type="submit" 
              disabled={discoveryMutation.isPending}
              className="bg-gradient-to-r from-[#0ea5e9] to-[#2563eb] text-white px-8 py-3.5 rounded-[12px] font-bold uppercase tracking-wider text-[13px] font-mono shadow-[0_0_20px_rgba(14,165,233,0.3)] hover:shadow-[0_0_30px_rgba(14,165,233,0.5)] transition-all disabled:opacity-50"
            >
              {discoveryMutation.isPending ? 'Executing Scan...' : 'Execute Scan'}
            </button>
          </div>
        </form>
      </PremiumCard>

      {/* Projects Grid */}
      <div>
        <h2 className="text-[14px] font-mono uppercase tracking-widest text-slate-400 mb-6 flex items-center gap-2">
          <Activity size={16} /> Active Pipeline <span className="text-[#0ea5e9] ml-auto">{filtered.length} targets</span>
        </h2>
        
        {isLoading ? (
          <PremiumCard variant="glass" featured innerClassName="p-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} variant="text" width="100%" height={20} />
            ))}
          </PremiumCard>
        ) : error ? (
           <EmptyState
             title="Database Error"
             message="Failed to establish connection to intelligence database."
             icon={Activity}
             action={<Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}>Reconnect</Button>}
           />
        ) : filtered.length === 0 ? (
           <div className="py-12 border border-dashed border-slate-700 rounded-[24px] flex flex-col items-center justify-center text-center">
             <div className="size-16 rounded-full bg-slate-800/50 flex items-center justify-center mb-4">
               <Users size={28} className="text-slate-500" />
             </div>
             <p className="text-[16px] font-bold text-white mb-2">No Targets Found</p>
             <p className="text-[14px] text-slate-400 max-w-md">Execute a scan above to populate your pipeline with new intelligence targets.</p>
           </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {filtered.map((p) => (
              <PremiumCard 
                key={p.id} 
                innerClassName="p-6 flex flex-col cursor-pointer transition-colors hover:bg-slate-800/50"
              >
                <div onClick={() => navigate(`/project/${p.id}`)} className="flex-1">
                  <div className="flex items-start justify-between mb-4">
                    <Badge tone={statusTone[p.status] ?? 'muted'} className="font-mono">{p.status.replace('_', ' ')}</Badge>
                    <ScoreBadgeInner score={p.rating} />
                  </div>
                  <h3 className="text-[18px] font-bold text-white mb-1 line-clamp-1">{p.name}</h3>
                  <p className="text-[12px] font-mono text-[#0ea5e9] mb-4 line-clamp-1">{p.industry} &middot; {p.city}</p>
                  
                  <div className="space-y-2 mt-auto pt-4 border-t border-slate-800">
                    <div className="flex justify-between text-[11px] font-mono text-slate-400">
                      <span>URL</span>
                      <span className="text-white truncate max-w-[150px]">{p.website || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-[11px] font-mono text-slate-400">
                      <span>Acquired</span>
                      <span>{formatRelative(p.updated_at)}</span>
                    </div>
                  </div>
                </div>
              </PremiumCard>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
