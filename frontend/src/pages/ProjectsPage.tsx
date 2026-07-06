import { useState } from 'react';
import { Plus, Search, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Input, Label } from '@/components/Input';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsService, leadDiscoveryService } from '@/services/services';
import { formatRelative } from '@/utils';
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

export function ProjectsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: paginated,
    isLoading,
    error,
  } = useQuery({
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
      toast.error(err instanceof Error ? err.message : 'Discovery failed');
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
    <div className="space-y-6">
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
        <Button leftIcon={<Plus className="size-4" />}>New Project</Button>
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
            <div className="p-4 space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} variant="text" width="100%" height={24} />
              ))}
            </div>
          ) : error ? (
            <div className="p-4">
              <EmptyState title="Failed to load projects" message="Try refreshing the page." />
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState title="No projects found" message={search ? 'Try a different search term' : 'Create your first project to get started'} />
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
                    <p className="text-[11.5px] text-[var(--color-text-muted)]">{p.website ?? '—'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={statusTone[p.status] ?? 'muted'}>{p.status}</Badge>
                    {p.rating != null && (
                      <span className="text-[12px] font-semibold text-amber-500">★ {p.rating.toFixed(1)}</span>
                    )}
                  </div>
                  <span className="text-[11px] text-[var(--color-text-muted)] whitespace-nowrap">{formatRelative(p.updated_at)}</span>
                  <ExternalLink className="size-3.5 text-[var(--color-text-muted)] flex-shrink-0" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
