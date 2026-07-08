import { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Zap } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { useAuthStore } from '@/store';
import { getErrorMessage } from '@/utils';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const storeLogin = useAuthStore((s) => s.login);
  const [serverError, setServerError] = useState('');
  const justRegistered = location.state?.registered === true;

  useEffect(() => {
    if (justRegistered) {
      toast.success('Account created successfully. Sign in to continue.');
    }
  }, [justRegistered]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  const onSubmit = async (data: LoginForm) => {
    setServerError('');
    try {
      await storeLogin(data.email, data.password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden bg-[var(--color-bg)]">
      {/* Background decorations */}
      <div className="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-[var(--color-brand)]/10 blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-[20%] -right-[10%] w-[60%] h-[60%] rounded-full bg-[var(--color-brand-600)]/10 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-sm relative z-10 lf-scale-up">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="size-12 rounded-[14px] bg-[var(--color-brand)] flex items-center justify-center shadow-[0_4px_20px_color-mix(in_oklab,var(--color-brand)_35%,transparent)] mb-4">
            <Zap className="size-6 text-white" strokeWidth={2.5} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Welcome back</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Sign in to LeadForge AI</p>
        </div>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="rounded-[14px] bg-[var(--color-glass)] backdrop-blur-[var(--blur-lg)] border border-[var(--color-glass-border)] shadow-[var(--shadow-pop)] p-6 space-y-4"
        >
          {serverError && (
            <div className="rounded-[10px] bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 text-[12.5px] p-3">
              {serverError}
            </div>
          )}

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              invalid={!!errors.email}
              {...register('email')}
            />
            <FormError>{errors.email?.message}</FormError>
          </div>

          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              invalid={!!errors.password}
              {...register('password')}
            />
            <FormError>{errors.password?.message}</FormError>
          </div>

          <Button type="submit" fullWidth loading={isSubmitting} variant="glow">
            Sign in
          </Button>
        </form>

        <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="text-[var(--color-brand)] hover:underline font-medium">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
