import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

// Layouts
import AppLayout from '@/layouts/AppLayout'

// Auth pages
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'

// App pages — lazy loaded for performance
import { lazy, Suspense } from 'react'

const DashboardPage        = lazy(() => import('@/pages/DashboardPage'))
const LeadManagementPage   = lazy(() => import('@/pages/LeadManagementPage'))
const LeadDetailsPage      = lazy(() => import('@/pages/LeadDetailsPage'))
const LeadDiscoveryPage    = lazy(() => import('@/pages/LeadDiscoveryPage'))
const AnalysisPage         = lazy(() => import('@/pages/AnalysisPage'))
const ScreenshotPage       = lazy(() => import('@/pages/ScreenshotPage'))
const AuditPage            = lazy(() => import('@/pages/AuditPage'))
const OutreachPage         = lazy(() => import('@/pages/OutreachPage'))
const SettingsPage         = lazy(() => import('@/pages/SettingsPage'))
const NotFoundPage         = lazy(() => import('@/pages/NotFoundPage'))

// Full-screen loading spinner shown during code splits
function PageLoader() {
  return (
    <div
      style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-background)',
      }}
    >
      <div className="spinner" style={{ width: 32, height: 32 }} />
    </div>
  )
}

// Protect routes that require authentication
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <PageLoader />
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

// Redirect already-logged-in users away from auth pages
function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <PageLoader />
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Guest-only routes */}
          <Route
            path="/login"
            element={
              <GuestRoute>
                <LoginPage />
              </GuestRoute>
            }
          />
          <Route
            path="/register"
            element={
              <GuestRoute>
                <RegisterPage />
              </GuestRoute>
            }
          />

          {/* Protected app routes — wrapped in sidebar layout */}
          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard"   element={<DashboardPage />} />
            <Route path="/leads"       element={<LeadManagementPage />} />
            <Route path="/leads/:id"   element={<LeadDetailsPage />} />
            <Route path="/discover"    element={<LeadDiscoveryPage />} />
            <Route path="/analysis"    element={<AnalysisPage />} />
            <Route path="/screenshots" element={<ScreenshotPage />} />
            <Route path="/audit"       element={<AuditPage />} />
            <Route path="/outreach"    element={<OutreachPage />} />
            <Route path="/settings"    element={<SettingsPage />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
