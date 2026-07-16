import { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Eye, EyeOff, ArrowRight } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { AuthLayout } from '@/layouts/AuthLayout';
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
  const [showPassword, setShowPassword] = useState(false);
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

  const header = (
    <div className="mb-8">
      <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
        Welcome back
      </h2>
      <p className="text-[13px] text-[var(--color-text-muted)]">
        Sign in to your workspace
      </p>
    </div>
  );

  const form = (
    <>
      {/* Server Error */}
      {serverError && (
        <div
          role="alert"
          className="rounded-[var(--radius-md)] bg-[var(--color-danger)]/10 border border-[var(--color-danger)]/20 text-[var(--color-danger)] text-[12.5px] p-3 mb-5"
        >
          {serverError}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="you@company.com"
            invalid={!!errors.email}
            autoComplete="email"
            {...register('email')}
          />
          <FormError>{errors.email?.message}</FormError>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <Label htmlFor="password">Password</Label>
            <Link
              to="/forgot-password"
              className="text-[11px] text-[var(--color-brand)] hover:text-[var(--color-brand-hover)] transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Enter your password"
              invalid={!!errors.password}
              autoComplete="current-password"
              className="pr-10"
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors cursor-pointer"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          <FormError>{errors.password?.message}</FormError>
        </div>

        <Button
          type="submit"
          fullWidth
          loading={isSubmitting}
          variant="primary"
          size="lg"
          className="mt-2"
          rightIcon={!isSubmitting ? <ArrowRight className="size-4" /> : undefined}
        >
          Sign in
        </Button>
      </form>

      <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          className="text-[var(--color-brand)] hover:text-[var(--color-brand-hover)] font-medium transition-colors"
        >
          Create one
        </Link>
      </p>
    </>
  );

  return (
    <AuthLayout card={form}>
      {header}
    </AuthLayout>
  );
}
