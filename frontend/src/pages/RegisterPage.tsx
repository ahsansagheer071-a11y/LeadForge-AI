import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Zap } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { useAuthStore } from '@/store';
import { getErrorMessage } from '@/utils';

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters').regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d|.*[!@#$%^&*()\-_=+{};:,<.>]).{8,}$/, 'Password must be at least 8 characters, contain at least one uppercase letter, one lowercase letter, and one digit or special character'),
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
      // Backend does NOT return tokens on register — redirect to login with success flag
      navigate('/login', { replace: true, state: { registered: true } });
    } catch (err) {
      setServerError(getErrorMessage(err));
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 relative overflow-hidden bg-[var(--color-bg)]">
      {/* Background decorations */}
      <div className="absolute -top-[20%] -right-[10%] w-[60%] h-[60%] rounded-full bg-[var(--color-brand)]/10 blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-[20%] -left-[10%] w-[60%] h-[60%] rounded-full bg-[var(--color-brand-600)]/10 blur-[120px] pointer-events-none" />

      <div className="w-full max-w-sm relative z-10 lf-scale-up">
        <div className="flex flex-col items-center mb-8">
          <div className="size-12 rounded-[14px] bg-[var(--color-brand)] flex items-center justify-center shadow-[0_4px_20px_color-mix(in_oklab,var(--color-brand)_35%,transparent)] mb-4">
            <Zap className="size-6 text-white" strokeWidth={2.5} />
          </div>
          <h1 className="text-xl font-bold tracking-tight">Create an account</h1>
          <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Get started with LeadForge AI</p>
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
            <Label htmlFor="name">Full name</Label>
            <Input
              id="name"
              placeholder="Jane Smith"
              invalid={!!errors.full_name}
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

          <div>
            <Label htmlFor="confirm">Confirm password</Label>
            <Input
              id="confirm"
              type="password"
              placeholder="••••••••"
              invalid={!!errors.confirm}
              {...register('confirm')}
            />
            <FormError>{errors.confirm?.message}</FormError>
          </div>

          <Button type="submit" fullWidth loading={isSubmitting} variant="glow">
            Create account
          </Button>
        </form>

        <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-[var(--color-brand)] hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
