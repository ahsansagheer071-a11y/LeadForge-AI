import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { Button } from '@/components/Button';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-[var(--color-bg)]">
      {/* Brand mark */}
      <div className="mb-8 size-16 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
        <LeadForgeLogo variant="compact" size={32} />
      </div>

      {/* Status */}
      <h1
        className="text-[72px] md:text-[96px] font-bold tracking-tighter leading-none mb-3"
        style={{
          background: 'linear-gradient(135deg, var(--color-brand), var(--color-text-muted))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}
      >
        404
      </h1>

      {/* Title & description */}
      <h2 className="text-[20px] font-semibold text-[var(--color-text)] mb-2">Page not found</h2>
      <p className="text-[14px] text-[var(--color-text-secondary)] max-w-sm leading-relaxed mb-8">
        The page you're looking for doesn't exist or has been moved.
      </p>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <Button
          variant="primary"
          size="md"
          leftIcon={<Home size={15} />}
          onClick={() => navigate('/dashboard')}
        >
          Return to Overview
        </Button>
        <Button
          variant="outline"
          size="md"
          leftIcon={<ArrowLeft size={15} />}
          onClick={() => navigate(-1)}
        >
          Go Back
        </Button>
      </div>

      {/* Footer */}
      <p className="mt-16 text-[10px] font-mono text-[var(--color-text-muted)] uppercase tracking-wider">
        LeadForge AI
      </p>
    </div>
  );
}
