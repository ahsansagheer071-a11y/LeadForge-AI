import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Globe, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
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
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">AI Generation</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Generate a website from any business profile</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Lead selector */}
        <Card variant="glass" className="lg:col-span-1">
          <CardHeader><CardTitle>Select Lead</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} variant="rounded" width="100%" height={44} delay={i * 60} />
                ))}
              </div>
            ) : leads.length > 0 ? (
              <div className="space-y-1 max-h-[380px] overflow-y-auto -mx-1 px-1">
                {leads.map((lead) => (
                  <button
                    key={lead.id}
                    onClick={() => setSelectedId(lead.id)}
                    className={cn(
                      'w-full text-left px-3 py-2.5 rounded-[8px] transition-colors text-[13px]',
                      selectedId === lead.id
                        ? 'bg-[var(--color-brand-soft)] border border-[var(--color-brand-border)]'
                        : 'bg-[var(--color-surface-hover)] hover:bg-[var(--color-surface-overlay)] border border-transparent',
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium truncate">{lead.name}</span>
                      <Badge tone={statusBadgeTone(lead.status)}>{lead.status.replace(/_/g, ' ')}</Badge>
                    </div>
                    {lead.website && (
                      <p className="text-[11.5px] text-[var(--color-text-muted)] mt-0.5 truncate">{lead.website}</p>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <EmptyState title="No leads" message="Import leads first to generate a website." />
            )}

            {leads.length > 0 && (
              <div className="pt-3 border-t border-[var(--color-border)] space-y-3">
                <div className="flex items-center justify-between text-[12px] text-[var(--color-text-muted)]">
                  <span>{selectedLead ? selectedLead.name : 'No lead selected'}</span>
                  {selectedLead?.rating != null && (
                    <span className="font-medium">★ {selectedLead.rating.toFixed(1)}</span>
                  )}
                </div>
                <Button
                  fullWidth
                  disabled={!selectedId || mutation.isPending}
                  loading={mutation.isPending}
                  leftIcon={<Sparkles className="size-4" />}
                  onClick={() => mutation.mutate()}
                >
                  {mutation.isPending ? 'Generating...' : 'Generate Website'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Status */}
        <Card variant="glass" className="lg:col-span-2">
          <CardHeader><CardTitle>Status</CardTitle></CardHeader>
          <CardContent>
            {!selectedId && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Globe className="size-12 text-[var(--color-text-muted)] mb-4" />
                <p className="text-[13px] text-[var(--color-text-muted)]">
                  Select a lead and click Generate to start.
                </p>
              </div>
            )}

            {selectedId && mutation.isPending && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-4">
                  <div className="absolute inset-0 rounded-full bg-[var(--color-brand-soft)] blur-xl" />
                  <div className="relative size-12 rounded-full bg-[var(--color-brand-soft)] flex items-center justify-center">
                    <Loader2 className="size-5 text-[var(--color-brand)] lf-spin" />
                  </div>
                </div>
                <p className="text-[14px] font-medium">Generating website...</p>
                <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1">This may take up to a minute.</p>
              </div>
            )}

            {selectedId && mutation.isSuccess && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-4">
                  <div className="absolute inset-0 rounded-full bg-[var(--color-brand-soft)] blur-xl" />
                  <div className="relative size-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
                    <CheckCircle2 className="size-5 text-[var(--color-success)]" />
                  </div>
                </div>
                <p className="text-[14px] font-semibold">Generation complete!</p>
                <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1">Your website is ready to preview.</p>
                <div className="flex gap-2 mt-5">
                  <Button variant="brand" onClick={() => {
                    const data = mutation.data;
                    if (data) navigate(`/preview/${data.website_id}`);
                  }}>View Preview</Button>
                </div>
              </div>
            )}

            {selectedId && mutation.isError && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="relative mb-4">
                  <div className="absolute inset-0 rounded-full bg-[var(--color-brand-soft)] blur-xl" />
                  <div className="relative size-12 rounded-full bg-red-500/10 flex items-center justify-center">
                    <AlertCircle className="size-5 text-[var(--color-danger)]" />
                  </div>
                </div>
                <p className="text-[14px] font-semibold">Generation failed</p>
                <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1">
                  {getApiErrorMessage(mutation.error, 'An unexpected error occurred.')}
                </p>
                <div className="flex gap-2 mt-5">
                  <Button variant="brand" onClick={() => mutation.mutate()}>Try Again</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
