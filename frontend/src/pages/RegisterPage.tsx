import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, ArrowRight, Sparkles } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { PremiumCard } from '@/components/PremiumCard';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { useAuthStore } from '@/store';
import { getErrorMessage } from '@/utils';

const registerSchema = z
  .object({
    full_name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters').regex(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d|.*[!@#$%^&*()\-_=+{};:,<.>]).{8,}$/,
      'Password must be at least 8 characters, contain at least one uppercase letter, one lowercase letter, and one digit or special character',
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

  return (
    <div className="min-h-screen w-full flex relative overflow-hidden bg-[var(--color-bg)]">
      {/* ── Premium Background ───────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-8%] right-[-3%] w-[45%] h-[45%] rounded-full bg-[rgba(6,182,212,0.10)] blur-[140px]" />
        <div className="absolute bottom-[-8%] left-[-3%] w-[45%] h-[45%] rounded-full bg-[rgba(139,92,246,0.08)] blur-[140px]" />
        <div className="absolute top-[40%] right-[30%] w-[25%] h-[25%] rounded-full bg-[rgba(14,165,233,0.06)] blur-[120px]" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(0deg, transparent, transparent 59px, rgba(255,255,255,0.015) 59px, rgba(255,255,255,0.015) 60px), repeating-linear-gradient(90deg, transparent, transparent 59px, rgba(255,255,255,0.015) 59px, rgba(255,255,255,0.015) 60px)',
            backgroundSize: '60px 60px',
          }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_70%_at_50%_50%,transparent_40%,rgba(0,0,0,0.6)_100%)]" />
      </div>

      {/* ── Desktop Layout ───────────────────────────── */}
      <div className="relative z-10 w-full min-h-screen flex flex-col lg:flex-row-reverse">
        {/* ── Left: Brand Visual ──────────────────────── */}
        <div className="flex-1 lg:w-[55%] flex flex-col justify-center px-8 md:px-16 lg:px-20 xl:px-28 py-12 lg:py-0">
          <div className="max-w-xl lf-fade-in">
            {/* Logo */}
            <LeadForgeLogo variant="glowing" size={48} className="mb-6" />

            {/* Onboarding title */}
            <h1 className="lf-display text-white mb-4">
              Build your AI-powered<br />
              <span className="lf-display-gradient">sales engine</span>
            </h1>

            <p className="text-[14px] text-[var(--color-text-secondary)] leading-relaxed mb-8 max-w-lg">
              LeadForge AI helps you discover overlooked businesses, audit their websites, 
              generate professional sites, and convert them with automated outreach — all from one command center.
            </p>

            {/* Quick workflow bullets */}
            <div className="space-y-4 mb-10">
              {[
                { icon: '01', text: 'Discover leads from any business directory' },
                { icon: '02', text: 'AI-powered website analysis & scoring' },
                { icon: '03', text: 'Generate premium websites instantly' },
                { icon: '04', text: 'Automated outreach campaigns' },
              ].map((item) => (
                <div key={item.icon} className="flex items-center gap-3.5 group">
                  <span className="size-7 rounded-full border border-[var(--color-border-strong)] bg-[var(--color-glass)] flex items-center justify-center text-[10px] font-mono font-bold text-[#0ea5e9] group-hover:shadow-[0_0_12px_rgba(14,165,233,0.2)] transition-shadow">
                    {item.icon}
                  </span>
                  <span className="text-[13px] text-[var(--color-text-secondary)]">{item.text}</span>
                </div>
              ))}
            </div>

            {/* System capabilities */}
            <div className="flex flex-wrap gap-3">
              {['Lead Discovery', 'AI Audit Engine', 'Website Builder', 'Smart Outreach'].map((label) => (
                <span
                  key={label}
                  className="text-[10px] font-mono uppercase tracking-[0.15em] px-3 py-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-glass)] text-[var(--color-text-muted)]"
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Right: Registration Card ────────────────── */}
        <div className="lg:w-[45%] flex items-center justify-center p-6 md:p-10 lg:p-14 xl:p-20">
          <div className="w-full max-w-md lf-fade-in" style={{ animationDelay: '80ms' }}>
            <PremiumCard variant="featured" innerClassName="p-8">
              {/* Header */}
              <div className="text-center mb-7">
                <div className="size-14 rounded-full bg-gradient-to-br from-[#06b6d4] to-[#8b5cf6] flex items-center justify-center mx-auto mb-5 shadow-[0_0_30px_rgba(6,182,212,0.3)]">
                  <Sparkles className="size-6 text-white" strokeWidth={2} />
                </div>
                <h2 className="text-[22px] font-bold tracking-tight text-white">Create account</h2>
                <p className="text-[13px] text-[var(--color-text-muted)] mt-1.5 font-mono">Begin your onboarding</p>
              </div>

              {/* Server Error */}
              {serverError && (
                <div className="rounded-[var(--radius-md)] bg-red-500/10 border border-red-500/30 text-red-400 text-[12.5px] p-3 mb-5 flex items-center gap-2" role="alert">
                  <span className="size-1.5 rounded-full bg-red-500 shrink-0" />
                  {serverError}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {/* Full name */}
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

                {/* Email */}
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

                {/* Password */}
                <div>
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
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

                {/* Confirm password */}
                <div>
                  <Label htmlFor="confirm">Confirm password</Label>
                  <div className="relative">
                    <Input
                      id="confirm"
                      type={showConfirm ? 'text' : 'password'}
                      placeholder="••••••••"
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

                <Button type="submit" fullWidth loading={isSubmitting} variant="glow" size="lg" rightIcon={!isSubmitting ? <ArrowRight className="size-4" /> : undefined}>
                  Create account
                </Button>
              </form>

              {/* Login nav */}
              <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
                Already have an account?{' '}
                <Link to="/login" className="text-[#0ea5e9] hover:text-[#06b6d4] font-semibold transition-colors">
                  Sign in
                </Link>
              </p>
            </PremiumCard>
          </div>
        </div>
      </div>
    </div>
  );
}
