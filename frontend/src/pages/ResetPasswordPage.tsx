import { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, ArrowRight, ArrowLeft, CheckCircle2, KeyRound } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { AuthLayout } from '@/layouts/AuthLayout';
import apiClient from '@/services/apiClient';
import { getErrorMessage } from '@/utils';

const resetSchema = z
  .object({
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

type ResetForm = z.infer<typeof resetSchema>;

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [serverError, setServerError] = useState('');
  const [success, setSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetForm>({
    resolver: zodResolver(resetSchema),
    defaultValues: { password: '', confirm: '' },
  });

  const onSubmit = async (data: ResetForm) => {
    setServerError('');
    try {
      await apiClient.post('/auth/reset-password', {
        token,
        password: data.password,
      });
      setSuccess(true);
    } catch (err) {
      const status = (err as { status?: number }).status;
      if (status === 404) {
        setServerError('This password reset link is not valid or has expired. Please request a new one.');
      } else {
        setServerError(getErrorMessage(err));
      }
    }
  };

  if (!token) {
    return (
      <AuthLayout card={<InvalidToken />}>
        <div className="mb-6">
          <div className="size-11 rounded-full bg-[var(--color-danger)]/10 flex items-center justify-center mb-4">
            <KeyRound className="size-5 text-[var(--color-danger)]" />
          </div>
          <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
            Invalid reset link
          </h2>
          <p className="text-[13px] text-[var(--color-text-muted)]">
            This link is missing a reset token.
          </p>
        </div>
      </AuthLayout>
    );
  }

  if (success) {
    return (
      <AuthLayout card={<SuccessReset />}>
        <div className="mb-6">
          <div className="size-11 rounded-full bg-[var(--color-success)]/10 flex items-center justify-center mb-4">
            <CheckCircle2 className="size-5 text-[var(--color-success)]" />
          </div>
          <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
            Password updated
          </h2>
          <p className="text-[13px] text-[var(--color-text-muted)]">
            Your password has been reset successfully.
          </p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout card={<ResetFormView serverError={serverError} errors={errors} isSubmitting={isSubmitting} register={register} handleSubmit={handleSubmit} onSubmit={onSubmit} showPassword={showPassword} setShowPassword={setShowPassword} showConfirm={showConfirm} setShowConfirm={setShowConfirm} />}>
      <div className="mb-6">
        <div className="size-11 rounded-full bg-[var(--color-brand-subtle)] flex items-center justify-center mb-4">
          <KeyRound className="size-5 text-[var(--color-brand)]" />
        </div>
        <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
          Set new password
        </h2>
        <p className="text-[13px] text-[var(--color-text-muted)]">
          Choose a strong password for your account.
        </p>
      </div>
    </AuthLayout>
  );
}

function ResetFormView({
  serverError,
  errors,
  isSubmitting,
  register,
  handleSubmit,
  onSubmit,
  showPassword,
  setShowPassword,
  showConfirm,
  setShowConfirm,
}: {
  serverError: string;
  errors: any;
  isSubmitting: boolean;
  register: any;
  handleSubmit: any;
  onSubmit: (data: ResetForm) => Promise<void>;
  showPassword: boolean;
  setShowPassword: (v: boolean) => void;
  showConfirm: boolean;
  setShowConfirm: (v: boolean) => void;
}) {
  return (
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
          <Label htmlFor="password">New password</Label>
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
          <Label htmlFor="confirm">Confirm new password</Label>
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
          Reset password
        </Button>
      </form>

      <Link
        to="/login"
        className="flex items-center justify-center gap-1.5 text-[12.5px] text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] mt-6 transition-colors"
      >
        <ArrowLeft className="size-3.5" />
        Back to sign in
      </Link>
    </>
  );
}

function InvalidToken() {
  return (
    <div className="text-center">
      <p className="text-[12.5px] text-[var(--color-text-muted)] mb-6 leading-relaxed">
        The password reset link is invalid or has expired. Please request a new one.
      </p>
      <Link to="/forgot-password">
        <Button variant="primary" size="md" fullWidth>
          Request new reset link
        </Button>
      </Link>
    </div>
  );
}

function SuccessReset() {
  return (
    <div className="text-center">
      <p className="text-[12.5px] text-[var(--color-text-muted)] mb-6 leading-relaxed">
        You can now sign in with your new password.
      </p>
      <Link to="/login">
        <Button variant="primary" size="md" fullWidth rightIcon={<ArrowRight className="size-4" />}>
          Sign in
        </Button>
      </Link>
    </div>
  );
}
