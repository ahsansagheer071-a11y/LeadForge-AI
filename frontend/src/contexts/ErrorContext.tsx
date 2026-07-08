/**
 * Global error sink context. Wired to Sonner and to a tiny toast
 * queue so API failures are surfaced to the user automatically.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { toast } from 'sonner';
import { setGlobalErrorSink } from '@/services/apiClient';
import type { APIErrorShape } from '@/types';

interface ErrorContextValue {
  errors: APIErrorShape[];
  push: (e: APIErrorShape) => void;
  dismiss: (i: number) => void;
  clear: () => void;
}

const ErrorContext = createContext<ErrorContextValue | null>(null);

function asSonnerKind(code?: string | null) {
  if (code === 'unauthorized' || code === 'forbidden') return 'error' as const;
  if (code === 'network') return 'warning' as const;
  if (code === 'validation') return 'info' as const;
  return 'error' as const;
}

export function ErrorContextProvider({ children }: { children: ReactNode }) {
  const [errors, setErrors] = useState<APIErrorShape[]>([]);

  const push = useCallback((e: APIErrorShape) => {
    setErrors((cur) => [...cur, e].slice(-50));
    toast[e.status === 0 ? 'warning' : asSonnerKind(e.code)](e.message, {
      id: `${e.status}-${e.code}-${e.message}`,
      description: e.code ? `Code: ${e.code}` : undefined,
    });
  }, []);

  const dismiss = useCallback(
    (i: number) => setErrors((cur) => cur.filter((_, idx) => idx !== i)),
    [],
  );
  const clear = useCallback(() => setErrors([]), []);

  useEffect(() => {
    setGlobalErrorSink(push);
    return () => setGlobalErrorSink(null);
  }, [push]);

  const value = useMemo(
    () => ({ errors, push, dismiss, clear }),
    [errors, push, dismiss, clear],
  );

  return <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useErrorSink(): ErrorContextValue {
  const ctx = useContext(ErrorContext);
  if (!ctx) throw new Error('useErrorSink must be used within <ErrorContextProvider>');
  return ctx;
}
