import { useEffect, useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { Eye, EyeOff, ArrowRight, Shield } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { PremiumCard } from '@/components/PremiumCard';
import { LeadForgeLogo } from '@/components/LeadForgeLogo';
import { useAuthStore } from '@/store';
import { getErrorMessage } from '@/utils';

const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginForm = z.infer<typeof loginSchema>;

const workflowSteps = [
  { label: 'Discover', desc: 'Lead Intelligence', icon: '01' },
  { label: 'Audit', desc: 'AI Website Audit', icon: '02' },
  { label: 'Build', desc: 'Website Generation', icon: '03' },
  { label: 'Convert', desc: 'Automated Outreach', icon: '04' },
];

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

  return (
    <div className="min-h-screen w-full flex relative overflow-hidden bg-[var(--color-bg)]">
      {/* ── Premium Background ───────────────────────── */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-5%] w-[50%] h-[50%] rounded-full bg-[rgba(14,165,233,0.10)] blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[50%] h-[50%] rounded-full bg-[rgba(124,58,237,0.08)] blur-[140px]" />
        <div className="absolute top-[60%] left-[40%] w-[30%] h-[30%] rounded-full bg-[rgba(6,182,212,0.06)] blur-[120px]" />
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

      {/* ── Desktop: 55/45 Split ─────────────────────── */}
      <div className="relative z-10 w-full min-h-screen flex flex-col lg:flex-row">
        {/* ── Left: Brand Experience ──────────────────── */}
        <div className="flex-1 lg:w-[55%] flex flex-col justify-center px-8 md:px-16 lg:px-20 xl:px-28 py-12 lg:py-0">
          <div className="max-w-xl lf-fade-in">
            {/* Logo */}
            <LeadForgeLogo variant="full" size={44} className="mb-8" />

            {/* Gradient Title */}
            <h1 className="lf-display lf-display-gradient mb-4">
              Lead Intelligence<br />Command Center
            </h1>

            {/* Tagline */}
            <p className="text-[15px] text-[var(--color-text-secondary)] font-mono mb-2 tracking-wide">
              Discover. Audit. Build. Convert.
            </p>
            <p className="text-[13px] text-[var(--color-text-muted)] leading-relaxed mb-12 max-w-lg">
              Turn overlooked businesses into ready-to-close opportunities.
            </p>

            {/* Workflow Steps */}
            <div className="space-y-0">
              {workflowSteps.map((step, i) => (
                <div key={step.label} className="flex items-start gap-4 group">
                  {/* Node + line */}
                  <div className="flex flex-col items-center">
                    <div className="size-8 rounded-full border border-[var(--color-border-strong)] bg-[var(--color-glass)] flex items-center justify-center text-[11px] font-mono font-bold text-[#0ea5e9] shadow-[0_0_10px_rgba(14,165,233,0.15)] transition-all duration-300 group-hover:shadow-[0_0_16px_rgba(14,165,233,0.3)]">
                      {step.icon}
                    </div>
                    {i < workflowSteps.length - 1 && (
                      <div className="w-px h-8 bg-gradient-to-b from-[var(--color-border-strong)] to-transparent my-1 relative overflow-hidden">
                        <div className="absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-[#0ea5e9] to-transparent opacity-50 animate-[lf-scan-line_2s_ease-in-out_infinite]" />
                      </div>
                    )}
                  </div>
                  {/* Content */}
                  <div className="pb-6 pt-0.5">
                    <p className="text-[14px] font-semibold text-[var(--color-text)]">{step.label}</p>
                    <p className="text-[12px] font-mono text-[var(--color-text-muted)]">{step.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* System labels */}
            <div className="mt-10 flex flex-wrap gap-3">
              {['Lead Intelligence', 'AI Website Audit', 'Website Generation', 'Automated Outreach'].map((label) => (
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

        {/* ── Right: Authentication ──────────────────── */}
        <div className="lg:w-[45%] flex items-center justify-center p-6 md:p-10 lg:p-14 xl:p-20">
          <div className="w-full max-w-md lf-fade-in" style={{ animationDelay: '80ms' }}>
            <PremiumCard variant="featured" innerClassName="p-8">
              {/* Welcome */}
              <div className="text-center mb-8">
                <div className="size-14 rounded-full bg-gradient-to-br from-[#0ea5e9] to-[#8b5cf6] flex items-center justify-center mx-auto mb-5 shadow-[0_0_30px_rgba(14,165,233,0.3)]">
                  <Shield className="size-6 text-white" strokeWidth={2} />
                </div>
                <h2 className="text-[22px] font-bold tracking-tight text-white">Welcome back</h2>
                <p className="text-[13px] text-[var(--color-text-muted)] mt-1.5 font-mono">Sign in to your workspace</p>
              </div>

              {/* Server Error */}
              {serverError && (
                <div className="rounded-[var(--radius-md)] bg-red-500/10 border border-red-500/30 text-red-400 text-[12.5px] p-3 mb-5 flex items-center gap-2" role="alert">
                  <span className="size-1.5 rounded-full bg-red-500 shrink-0" />
                  {serverError}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
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

                <Button type="submit" fullWidth loading={isSubmitting} variant="glow" size="lg" rightIcon={!isSubmitting ? <ArrowRight className="size-4" /> : undefined}>
                  Sign in
                </Button>
              </form>

              {/* Register nav */}
              <p className="text-center text-[12.5px] text-[var(--color-text-muted)] mt-6">
                Don't have an account?{' '}
                <Link to="/register" className="text-[#0ea5e9] hover:text-[#06b6d4] font-semibold transition-colors">
                  Create one
                </Link>
              </p>
            </PremiumCard>

            {/* Secure detail */}
            <p className="text-center text-[10px] text-[var(--color-text-muted)] mt-4 font-mono uppercase tracking-wider flex items-center justify-center gap-1.5">
              <Shield className="size-3" /> Encrypted connection
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
