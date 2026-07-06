import { useNavigate } from 'react-router-dom';
import { ArrowLeft, FileQuestion } from 'lucide-react';
import { Button } from '@/components/Button';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center h-full p-10 text-center">
      <div className="size-16 rounded-full bg-[var(--color-brand-soft)] flex items-center justify-center mb-4">
        <FileQuestion className="size-8 text-[var(--color-brand)]" />
      </div>
      <h1 className="text-2xl font-bold tracking-tight">Page not found</h1>
      <p className="text-[13px] text-[var(--color-text-muted)] mt-2 max-w-sm">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button className="mt-6" leftIcon={<ArrowLeft className="size-4" />} onClick={() => navigate('/dashboard')}>
        Back to Dashboard
      </Button>
    </div>
  );
}
