import { useState } from 'react';
import { Plus, Search, ExternalLink, Star, Activity, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Input, Label } from '@/components/Input';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { PremiumCard } from '@/components/PremiumCard';
import { AnimatedCounter } from '@/components/AnimatedCounter';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService, leadDiscoveryService, dashboardService } from '@/services/services';
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

  const { data: summary } = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardService.summary(),
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
    <div className="space-y-6 animate-[lf-fade-in_0.22s_ease]">
      {/* ── Pipeline Overview mini-KPIs ─── */}
      {summary && (summary.total_leads > 0 || summary.audited_leads > 0) && (
        <div className="grid grid-cols-3 gap-4">
          <PremiumCard innerClassName="p-4 flex flex-col gap-2">
            <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">Total Pipeline</span>
            <div className="text-[1.5rem] font-bold tracking-tight"><AnimatedCounter value={summary.total_leads} /></div>
          </PremiumCard>
          <PremiumCard innerClassName="p-4 flex flex-col gap-2">
            <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">AI Audited</span>
            <div className="text-[1.5rem] font-bold tracking-tight"><AnimatedCounter value={summary.audited_leads} /></div>
          </PremiumCard>
          <PremiumCard innerClassName="p-4 flex flex-col gap-2">
            <span className="text-[11.5px] font-medium text-[var(--color-text-muted)]">Avg Score</span>
            <div className="text-[1.5rem] font-bold tracking-tight">{Math.round(summary.average_lead_score)}</div>
          </PremiumCard>
        </div>
      )}

      {/* Discovery Form */}
      <Card>
        <CardHeader>
          <CardTitle>Discover New Leads</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <form onSubmit={handleDiscoverySubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="business_type">Business Type</Label>
                <Input
                  id="business_type"
                  name="business_type"
                  value={discoveryForm.business_type}
                  onChange={handleDiscoveryChange}
                  placeholder="e.g. Pizza Restaurant, Dentist"
                  required
                />
              </div>
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  name="city"
                  value={discoveryForm.city}
                  onChange={handleDiscoveryChange}
                  placeholder="e.g. New York"
                  required
                />
              </div>
              <div>
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  name="country"
                  value={discoveryForm.country}
                  onChange={handleDiscoveryChange}
                  placeholder="e.g. USA"
                  required
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button type="submit" loading={discoveryMutation.isPending}>
                Discover Leads
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Projects List */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Projects</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Manage your lead generation projects</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-[var(--color-text-muted)]">{projects.length} total</span>
          <Button leftIcon={<Plus className="size-4" />}>New Project</Button>
        </div>
      </div>

      <div className="relative w-full max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-[var(--color-text-muted)]" />
        <Input
          placeholder="Search projects..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Projects</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-5 space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} variant="text" width="100%" height={28} delay={60 * i} />
              ))}
            </div>
          ) : error ? (
            <div className="p-5">
              <EmptyState
                title="Failed to load projects"
                message="We couldn't retrieve your projects. Check your connection and try again."
                icon={Activity}
                action={<Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['projects'] })}>Retry</Button>}
              />
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-5">
              {search ? (
                <EmptyState title="No matching projects" message={`No projects match "${search}". Try a different search term.`} icon={Search} />
              ) : (
                <EmptyState
                  title="No projects yet"
                  message="Your project list will populate after you discover leads. Use the form above to find businesses."
                  icon={Users}
                />
              )}
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {filtered.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-surface-hover)] transition-colors cursor-pointer"
                  onClick={() => navigate(`/project/${p.id}`)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-medium truncate">{p.name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      {p.website && <p className="text-[11.5px] text-[var(--color-text-muted)] truncate">{p.website}</p>}
                      {p.rating != null && (
                        <span className="inline-flex items-center gap-0.5 text-[11px] text-amber-500 shrink-0">
                          <Star className="size-3 fill-amber-500" />{p.rating.toFixed(1)}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <ScoreBadgeInner score={p.rating} />
                    <Badge tone={statusTone[p.status] ?? 'muted'}>{p.status}</Badge>
                  </div>
                  <span className="text-[11px] text-[var(--color-text-muted)] whitespace-nowrap shrink-0">{formatRelative(p.updated_at)}</span>
                  <ExternalLink className="size-3.5 text-[var(--color-text-muted)] shrink-0" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
