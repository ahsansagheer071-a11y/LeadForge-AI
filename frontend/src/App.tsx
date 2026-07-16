import { lazy, Suspense, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ErrorContextProvider } from '@/contexts/ErrorContext';
import { DashboardLayout, Workspace } from '@/layouts/DashboardLayout';
import { TopBar } from '@/layouts/TopBar';
import { Sidebar } from '@/layouts/Sidebar';
import { RightActivityPanel } from '@/layouts/RightActivityPanel';
import { FooterStatusBar } from '@/layouts/FooterStatusBar';
import { PageLoader } from '@/components/Loading';
import { ErrorBoundary } from '@/components/ErrorStates';
import { ProtectedRoute, PublicRoute } from '@/components/ProtectedRoute';
import { useAuthStore } from '@/store';
import { useLocalStorage } from '@/hooks/hooks';

const LoginPage = lazy(() => import('@/pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('@/pages/RegisterPage').then((m) => ({ default: m.RegisterPage })));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('@/pages/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })));
const DashboardPage = lazy(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage').then((m) => ({ default: m.ProjectsPage })));
const GenerationPage = lazy(() => import('@/pages/GenerationPage').then((m) => ({ default: m.GenerationPage })));
const PreviewPage = lazy(() => import('@/pages/PreviewPage').then((m) => ({ default: m.PreviewPage })));
const DeploymentPage = lazy(() => import('@/pages/DeploymentPage').then((m) => ({ default: m.DeploymentPage })));
const HistoryPage = lazy(() => import('@/pages/HistoryPage').then((m) => ({ default: m.HistoryPage })));
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage').then((m) => ({ default: m.AnalyticsPage })));
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })));
const HelpPage = lazy(() => import('@/pages/HelpPage').then((m) => ({ default: m.HelpPage })));
const LeadDetailPage = lazy(() => import('@/pages/LeadDetailPage').then((m) => ({ default: m.LeadDetailPage })));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })));

function DashboardShell() {
  const [activityOpen, setActivityOpen] = useLocalStorage('lf_activity_open', false);

  return (
    <ProtectedRoute>
      <DashboardLayout
        topBar={<TopBar />}
        sidebar={<Sidebar />}
        activityPanel={
          <RightActivityPanel open={activityOpen} onClose={() => setActivityOpen(false)} />
        }
        footer={<FooterStatusBar />}
        activityOpen={activityOpen}
      >
        <Workspace>
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </Workspace>
      </DashboardLayout>
    </ProtectedRoute>
  );
}

const router = createBrowserRouter([
  { path: '/login', element: <PublicRoute><LoginPage /></PublicRoute> },
  { path: '/register', element: <PublicRoute><RegisterPage /></PublicRoute> },
  { path: '/forgot-password', element: <PublicRoute><ForgotPasswordPage /></PublicRoute> },
  { path: '/reset-password', element: <PublicRoute><ResetPasswordPage /></PublicRoute> },
  {
    path: '/',
    element: <DashboardShell />,
    errorElement: <DashboardShell />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'projects', element: <ProjectsPage /> },
      { path: 'generation', element: <GenerationPage /> },
      { path: 'preview', element: <PreviewPage /> },
      { path: 'preview/:websiteId', element: <PreviewPage /> },
      { path: 'project/:id', element: <LeadDetailPage /> },
      { path: 'deployment', element: <DeploymentPage /> },
      { path: 'deployment/:websiteId', element: <DeploymentPage /> },
      { path: 'history', element: <HistoryPage /> },
      { path: 'analytics', element: <AnalyticsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'help', element: <HelpPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

export default function App() {
  const initialised = useAuthStore((s) => s.initialised);
  const checkAuth = useAuthStore((s) => s.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Wait for Zustand rehydration + initial checkAuth() before rendering routes.
  // Theme CSS variables are already active via the <script> in index.html.
  if (!initialised) {
    return (
      <div className="min-h-screen w-full bg-[var(--color-bg)] flex items-center justify-center">
        <PageLoader />
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <ErrorContextProvider>
            <RouterProvider router={router} />
            <Toaster
              position="bottom-right"
              toastOptions={{
                style: {
                  background: 'var(--color-surface)',
                  color: 'var(--color-text)',
                  border: '1px solid var(--color-border)',
                  fontSize: '13px',
                  borderRadius: '10px',
                },
              }}
            />
          </ErrorContextProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
