import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store';
import type { ReactNode } from 'react';

export function ProtectedRoute({ children }: { children?: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children ? <>{children}</> : <Outlet />;
}

export function PublicRoute({ children }: { children?: ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children ? <>{children}</> : <Outlet />;
}
