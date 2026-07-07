import { ExternalLink, RefreshCw, Monitor, Smartphone, Tablet, Loader2, AlertCircle, Globe } from 'lucide-react';
import { Card, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { Skeleton } from '@/components/Loading';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cn } from '@/utils';
import { EmptyState } from '@/components/ErrorStates';
import { usePreviewStore, useAuthStore } from '@/store';
import { generationService } from '@/services/services';

type Viewport = 'desktop' | 'tablet' | 'mobile';

export function PreviewPage() {
  const { websiteId } = useParams<{ websiteId: string }>();
  const navigate = useNavigate();
  const { htmlContent: storeHtml, setHtmlContent } = usePreviewStore();
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
      <div className="space-y-6">
        <div>
          <Skeleton variant="text" width={200} height={24} />
          <Skeleton variant="text" width={300} height={16} className="mt-1" />
        </div>
        <Card>
          <CardContent className="p-8">
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Loader2 className="size-8 text-[var(--color-brand)] lf-spin mb-4" />
              <p className="text-[14px] font-medium">Loading preview...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (websiteId && error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Preview</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Preview generated websites before deployment</p>
        </div>
        <Card>
          <CardContent className="p-8">
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <AlertCircle className="size-12 text-[var(--color-danger)] mb-4" />
              <p className="text-[14px] font-semibold">Preview unavailable</p>
              <p className="text-[12.5px] text-[var(--color-text-muted)] mt-1">
                This preview could not be loaded. It may have expired, been removed, or you may not have access.
              </p>
              <div className="flex gap-2 mt-5">
                <Button variant="outline" onClick={() => navigate('/generation')}>
                  Back to Generation
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Preview</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Preview generated websites before deployment</p>
        </div>
        {hasPreview && (
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" leftIcon={<RefreshCw className="size-3.5" />} onClick={handleReload}>Reload</Button>
            <Button size="sm" leftIcon={<ExternalLink className="size-3.5" />} onClick={handleOpenInTab}>
              Open in Tab
            </Button>
          </div>
        )}
      </div>

      {/* Viewport switcher */}
      {hasPreview && (
        <div className="flex items-center gap-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-[10px] p-1 w-fit">
          {(['desktop', 'tablet', 'mobile'] as const).map((v) => (
            <button
              key={v}
              onClick={() => setViewport(v)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-[7px] text-[12px] font-medium transition-colors',
                viewport === v
                  ? 'bg-[var(--color-brand-soft)] text-[var(--color-brand)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]',
              )}
            >
              {v === 'desktop' && <Monitor className="size-3.5" />}
              {v === 'tablet' && <Tablet className="size-3.5" />}
              {v === 'mobile' && <Smartphone className="size-3.5" />}
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          {hasPreview ? (
            <div className="flex justify-center p-4 bg-[var(--color-bg)] rounded-b-[14px]">
              <div className={cn('h-[600px] rounded-[8px] border border-[var(--color-border)] overflow-hidden bg-white transition-all', vpClasses[viewport])}>
                <iframe
                  title="Generated website preview"
                  srcDoc={htmlContent}
                  style={{ width: '100%', height: '100%', border: 'none' }}
                />
              </div>
            </div>
          ) : (
            <div className="p-8">
              <EmptyState
                title="No preview available"
                message="Generate a website first, then preview it here."
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}