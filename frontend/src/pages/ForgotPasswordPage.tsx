import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, ArrowRight, CheckCircle2, Mail } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input, Label, FormError } from '@/components/Input';
import { AuthLayout } from '@/layouts/AuthLayout';
import apiClient from '@/services/apiClient';
import { getErrorMessage } from '@/utils';

const forgotSchema = z.object({
  email: z.string().email('Enter a valid email'),
});

type ForgotForm = z.infer<typeof forgotSchema>;

export function ForgotPasswordPage() {
  const [serverError, setServerError] = useState('');
  const [sent, setSent] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotForm>({
    resolver: zodResolver(forgotSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = async (data: ForgotForm) => {
    setServerError('');
    try {
      await apiClient.post('/auth/forgot-password', { email: data.email });
      setSubmittedEmail(data.email);
      setSent(true);
    } catch (err) {
      const status = (err as { status?: number }).status;
      if (status === 404) {
        // Endpoint doesn't exist yet — still show success to prevent enumeration
        setSubmittedEmail(data.email);
        setSent(true);
      } else {
        setServerError(getErrorMessage(err));
      }
    }
  };

  if (sent) {
    return (
      <AuthLayout card={<SuccessState email={submittedEmail} />}>
        <div className="mb-6">
          <div className="size-11 rounded-full bg-[var(--color-success)]/10 flex items-center justify-center mb-4">
            <CheckCircle2 className="size-5 text-[var(--color-success)]" />
          </div>
          <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
            Check your email
          </h2>
          <p className="text-[13px] text-[var(--color-text-muted)]">
            We sent a password reset link to
          </p>
          <p className="text-[13px] font-medium text-[var(--color-text)] mt-1">{submittedEmail}</p>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout card={<ForgotFormView serverError={serverError} errors={errors} isSubmitting={isSubmitting} register={register} handleSubmit={handleSubmit} onSubmit={onSubmit} setServerError={setServerError} />}>
      <div className="mb-6">
        <div className="size-11 rounded-full bg-[var(--color-brand-subtle)] flex items-center justify-center mb-4">
          <Mail className="size-5 text-[var(--color-brand)]" />
        </div>
        <h2 className="text-[22px] font-bold tracking-tight text-[var(--color-text)] mb-1.5">
          Reset your password
        </h2>
        <p className="text-[13px] text-[var(--color-text-muted)]">
          Enter the email address associated with your account and we&apos;ll send you a link to reset your password.
        </p>
      </div>
    </AuthLayout>
  );
}

function ForgotFormView({
  serverError,
  errors,
  isSubmitting,
  register,
  handleSubmit,
  onSubmit,
}: {
  serverError: string;
  errors: any;
  isSubmitting: boolean;
  register: any;
  handleSubmit: any;
  onSubmit: (data: ForgotForm) => Promise<void>;
  setServerError: (s: string) => void;
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
          <Label htmlFor="email">Email address</Label>
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

        <Button
          type="submit"
          fullWidth
          loading={isSubmitting}
          variant="primary"
          size="lg"
          rightIcon={!isSubmitting ? <ArrowRight className="size-4" /> : undefined}
        >
          Send reset link
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

function SuccessState({ email }: { email: string }) {
  return (
    <div className="text-center">
      <p className="text-[12.5px] text-[var(--color-text-muted)] mb-6 leading-relaxed">
        If an account exists for <span className="font-medium text-[var(--color-text)]">{email}</span>, you&apos;ll receive a password reset link shortly. Check your inbox and spam folder.
      </p>

      <Link to="/login">
        <Button variant="secondary" size="md" fullWidth leftIcon={<ArrowLeft className="size-3.5" />}>
          Return to sign in
        </Button>
      </Link>

      <button
        type="button"
        onClick={() => window.location.reload()}
        className="text-[12px] text-[var(--color-brand)] hover:text-[var(--color-brand-hover)] mt-4 transition-colors cursor-pointer"
      >
        Didn&apos;t receive it? Try again
      </button>
    </div>
  );
}
