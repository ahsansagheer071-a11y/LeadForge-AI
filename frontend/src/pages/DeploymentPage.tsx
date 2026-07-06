import { Globe, ExternalLink, RotateCcw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { EmptyState } from '@/components/ErrorStates';
import { cn, formatRelative } from '@/utils';
import { deploymentsService } from '@/services/services';
import type { DeploymentInfo } from '@/types';

const statusTone: Record<DeploymentInfo['status'], 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'muted' | 'neutral'> = {
  pending: 'info',
  building: 'warning',
  live: 'success',
  failed: 'danger',
  'rolled-back': 'neutral',
};

const providerColor: Record<DeploymentInfo['provider'], string> = {
  vercel: 'text-black dark:text-white',
  netlify: 'text-teal-500',
  aws: 'text-orange-500',
  gcp: 'text-blue-500',
  azure: 'text-sky-600',
  'self-hosted': 'text-[var(--color-text-muted)]',
};

export function DeploymentPage() {
  const [deployments, setDeployments] = useState<DeploymentInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    deploymentsService.list().then((list) => {
      setDeployments(list);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Deployments</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Manage and monitor your website deployments</p>
        </div>
        <Button leftIcon={<Globe className="size-4" />}>New Deployment</Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Deployments</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} variant="text" width="100%" height={24} />
              ))}
            </div>
          ) : deployments.length === 0 ? (
            <div className="p-8">
              <EmptyState title="No deployments yet" message="Deploy a generated website to see it here." />
            </div>
          ) : (
            <div className="divide-y divide-[var(--color-border)]">
              {deployments.map((d) => (
                <div key={d.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-[var(--color-surface-hover)] transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={cn('text-[12px] font-semibold', providerColor[d.provider])}>{d.provider}</span>
                      <Badge tone={statusTone[d.status]}>{d.status}</Badge>
                    </div>
                    {d.url && (
                      <a href={d.url} target="_blank" rel="noopener noreferrer" className="text-[11.5px] text-[var(--color-brand)] hover:underline inline-flex items-center gap-1 mt-0.5">
                        {d.url} <ExternalLink className="size-3" />
                      </a>
                    )}
                  </div>
                  <span className="text-[11px] text-[var(--color-text-muted)]">{formatRelative(d.created_at)}</span>
                  <Button variant="ghost" size="xs"><RotateCcw className="size-3.5" /></Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
