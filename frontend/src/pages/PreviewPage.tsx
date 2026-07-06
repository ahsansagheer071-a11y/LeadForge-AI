import { ExternalLink, RefreshCw, Monitor, Smartphone, Tablet } from 'lucide-react';
import { Card, CardContent } from '@/components/Card';
import { Button } from '@/components/Button';
import { useState } from 'react';
import { cn } from '@/utils';
import { EmptyState } from '@/components/ErrorStates';
import { usePreviewStore } from '@/store';

type Viewport = 'desktop' | 'tablet' | 'mobile';

export function PreviewPage() {
  const { htmlContent } = usePreviewStore();
  const [viewport, setViewport] = useState<Viewport>('desktop');
  const hasPreview = !!htmlContent;

  const vpClasses: Record<Viewport, string> = {
    desktop: 'w-full',
    tablet: 'w-[768px]',
    mobile: 'w-[375px]',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Preview</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Preview generated websites before deployment</p>
        </div>
        {hasPreview && (
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" leftIcon={<RefreshCw className="size-3.5" />}>Reload</Button>
            <Button size="sm" leftIcon={<ExternalLink className="size-3.5" />}>
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
                {/* NOTE: iframe srcDoc renders the HTML string directly */}
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