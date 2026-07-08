import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FileQuestion } from 'lucide-react';
import { Button } from '@/components/Button';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-10 text-center relative overflow-hidden bg-[var(--color-bg)]">
      {/* Background decorations */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] max-w-[800px] rounded-full bg-[var(--color-brand)]/5 blur-[120px] pointer-events-none" />
      
      <div className="relative z-10 lf-scale-up flex flex-col items-center">
        <div className="size-24 rounded-full bg-[var(--color-brand-soft)] flex items-center justify-center mb-6 shadow-[0_0_40px_var(--color-brand-soft)]">
          <FileQuestion className="size-10 text-[var(--color-brand)] lf-pulse" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight mb-2">404</h1>
        <h2 className="text-xl font-semibold tracking-tight text-[var(--color-text-secondary)]">Page not found</h2>
        <p className="text-[14px] text-[var(--color-text-muted)] mt-3 max-w-sm">
          The page you're looking for doesn't exist or has been moved. Let's get you back on track.
        </p>
        <Button className="mt-8" leftIcon={<ArrowLeft className="size-4" />} variant="glow" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </Button>
      </div>
    </div>
  );
}
