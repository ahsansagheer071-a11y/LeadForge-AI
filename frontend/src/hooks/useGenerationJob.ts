import { useState, useEffect, useRef } from 'react';
import { createGenerationJob, pollGenerationJob, type GenerationJobResult } from '@/services/services';
import { extractApiError } from '@/services/apiClient';

export function categorizeGenerationError(err: unknown): string {
  const apiErr = extractApiError(err);
  if (apiErr.status === 0 || apiErr.category === 'network') {
    return 'Cannot connect to the LeadForge API.';
  }
  if (apiErr.status === 401 || apiErr.status === 403) {
    return 'Your session has expired. Please sign in again.';
  }
  if (apiErr.status === 404) {
    return 'The website generation service is not available in this deployment.';
  }
  if (apiErr.status === 422) {
    return apiErr.message || 'Prerequisite validation failed.';
  }
  if (apiErr.status === 500) {
    return 'Website generation failed on the server.';
  }
  return apiErr.message || 'An unexpected error occurred.';
}

export interface UseGenerationJobOptions {
  leadId: string;
  onSuccess?: (websiteId: string, htmlContent: string) => void;
  onError?: (errorMsg: string) => void;
}

export function useGenerationJob({ leadId, onSuccess, onError }: UseGenerationJobOptions) {
  const [jobId, setJobId] = useState<string | null>(() => {
    if (!leadId) return null;
    return localStorage.getItem(`active_job_lead_${leadId}`);
  });
  const [jobResult, setJobResult] = useState<GenerationJobResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobError, setJobError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const startPolling = (id: string) => {
    stopPolling();
    localStorage.setItem(`active_job_lead_${leadId}`, id);
    
    pollRef.current = setInterval(async () => {
      try {
        const result = await pollGenerationJob(id);
        setJobResult(result);
        if (result.status === 'succeeded') {
          stopPolling();
          localStorage.removeItem(`active_job_lead_${leadId}`);
          if (result.website_id) {
            onSuccess?.(result.website_id, result.html || '');
          } else {
            const err = 'Generation completed but no website ID was returned.';
            setJobError(err);
            onError?.(err);
          }
        } else if (result.status === 'failed') {
          stopPolling();
          localStorage.removeItem(`active_job_lead_${leadId}`);
          const msg = result.error || 'Website generation failed on the server.';
          setJobError(msg);
          onError?.(msg);
        }
      } catch (err: unknown) {
        console.warn('Polling error (retrying):', err);
      }
    }, 3000);
  };

  useEffect(() => {
    if (jobId) {
      setJobResult({
        job_id: jobId,
        lead_id: leadId,
        status: 'running',
        progress: 'Resuming scan...',
        generation_time: 0,
      });
      startPolling(jobId);
    }
    return () => stopPolling();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, leadId]);

  const generate = async () => {
    if (!leadId || isSubmitting) return;
    setIsSubmitting(true);
    setJobError(null);
    setJobResult(null);

    try {
      const { job_id } = await createGenerationJob(leadId);
      setJobId(job_id);
      setJobResult({
        job_id,
        lead_id: leadId,
        status: 'pending',
        progress: 'Queued',
        generation_time: 0,
      });
      startPolling(job_id);
    } catch (err: unknown) {
      const apiErr = extractApiError(err);
      if (apiErr.status === 409) {
        const existingJobId = (apiErr.details as any)?.data?.job_id || (apiErr.details as any)?.job_id;
        if (existingJobId) {
          setJobId(existingJobId);
          startPolling(existingJobId);
          return;
        }
      }
      const msg = categorizeGenerationError(err);
      setJobError(msg);
      onError?.(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const reset = () => {
    stopPolling();
    localStorage.removeItem(`active_job_lead_${leadId}`);
    setJobId(null);
    setJobResult(null);
    setJobError(null);
  };

  const isRunning = jobResult?.status === 'pending' || jobResult?.status === 'running' || isSubmitting;
  const isSuccess = jobResult?.status === 'succeeded';
  const isError = !!jobError || jobResult?.status === 'failed';

  return {
    jobId,
    jobResult,
    jobError,
    isRunning,
    isSuccess,
    isError,
    generate,
    reset,
  };
}
