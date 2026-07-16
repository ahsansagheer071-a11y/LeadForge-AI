import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, ArrowRight } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { AuthLayout } from '@/layouts/AuthLayout';
import { useAuthStore } from '@/store';
import { getErrorMessage } from '@/utils';

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d|.*[!@#$%^&*()\-_=+{};:,<.>]).{8,}$/,
        'Must contain uppercase, lowercase, and a number or special character',
      ),
    confirm: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirm, {
    message: 'Passwords do not match',
    path: ['confirm'],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const storeRegister = useAuthStore((s) => s.register);
  const [serverError, setServerError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: '', email: '', password: '', confirm: '' },
  });

  const onSubmit = async (data: RegisterForm) => {
    setServerError('');
    try {
      await storeRegister(data.email, data.password, data.full_name);
      navigate('/login', { replace: true, state: { registered: true } });
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  const header = (
    <div className="mb-7">
      <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
        Create account
      </h2>
      <p className="text-[13px] text-[var(--color-text-muted)]">
        Start your free trial
      </p>
    </div>
  );

  const form = (
    <>
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
          <Label htmlFor="name">Full name</Label>
          <Input
            id="name"
            placeholder="Jane Smith"
            invalid={!!errors.full_name}
            autoComplete="name"
            {...register('full_name')}
          />
          <FormError>{errors.full_name?.message}</FormError>
        </div>

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
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Create a strong password"
              invalid={!!errors.password}
              autoComplete="new-password"
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

        <div>
          <Label htmlFor="confirm">Confirm password</Label>
          <div className="relative">
            <Input
              id="confirm"
              type={showConfirm ? 'text' : 'password'}
              placeholder="Re-enter your password"
              invalid={!!errors.confirm}
              autoComplete="new-password"
              className="pr-10"
              {...register('confirm')}
            />
            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors cursor-pointer"
              aria-label={showConfirm ? 'Hide password' : 'Show password'}
              tabIndex={-1}
            >
              {showConfirm ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          <FormError>{errors.confirm?.message}</FormError>
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
          Create account
        </Button>
      </form>

      <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
        Already have an account?{' '}
        <Link
          to="/login"
          className="text-[var(--color-brand)] hover:text-[var(--color-brand-hover)] font-medium transition-colors"
        >
          Sign in
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
