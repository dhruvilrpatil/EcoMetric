/**
 * App.tsx — Root router with React Query provider, Redux provider,
 * protected routes, and lazy-loaded page components.
 *
 * Route map per PRD §5.1
 */

import { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Provider } from 'react-redux'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { store, useAppDispatch, useAppSelector } from '@/store'
import { setUser } from '@/store/authSlice'
import type { UserProfile } from '@/types'

// ── Lazy-load all page components ──────────────────────────────────
const LandingPage = lazy(() => import('@/pages/LandingPage'))
const LoginPage = lazy(() => import('@/pages/LoginPage'))
const RegisterPage = lazy(() => import('@/pages/RegisterPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const ProjectSetupPage = lazy(() => import('@/pages/ProjectSetupPage'))
const InventoryPage = lazy(() => import('@/pages/InventoryPage'))
const TransportationPage = lazy(() => import('@/pages/TransportationPage'))
const CalculatePage = lazy(() => import('@/pages/CalculatePage'))
const HotspotsPage = lazy(() => import('@/pages/HotspotsPage'))
const ExportPage = lazy(() => import('@/pages/ExportPage'))
const PublishPage = lazy(() => import('@/pages/PublishPage'))
const PortfolioPage = lazy(() => import('@/pages/PortfolioPage'))
const VerifierPage = lazy(() => import('@/pages/VerifierPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

// ── React Query client ──────────────────────────────────────────────
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 2,
    },
  },
})

// ── Loading spinner (shown during lazy load & auth init) ────────────
function PageLoader() {
  return (
    <div className="loading-overlay" role="status" aria-label="Loading EcoMetric">
      <div className="flex flex-col items-center gap-xl">
        <svg
          width="48" height="48" viewBox="0 0 48 48"
          className="animate-spin text-primary"
          fill="none" aria-hidden="true"
        >
          <circle
            cx="24" cy="24" r="20"
            stroke="currentColor" strokeWidth="4"
            strokeDasharray="90 30" strokeLinecap="round"
          />
        </svg>
        <span className="text-body-sm text-on-dark-mute">Loading…</span>
      </div>
    </div>
  )
}

// ── Protected route wrapper ──────────────────────────────────────────
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, initialized } = useAppSelector((s) => s.auth)

  if (!initialized) return <PageLoader />
  if (!user) return <Navigate to="/login" replace />

  return <>{children}</>
}

// ── Public-only route (redirect authenticated users away from login/register) ──
function PublicOnly({ children }: { children: React.ReactNode }) {
  const { user, initialized } = useAppSelector((s) => s.auth)

  if (!initialized) return <PageLoader />
  if (user) return <Navigate to="/dashboard" replace />

  return <>{children}</>
}

// ── Auth state listener (DEV BYPASS) ──────────────────────────────────
function AuthListener({ children }: { children: React.ReactNode }) {
  const dispatch = useAppDispatch()

  useEffect(() => {
    // DEV MODE: Instantly log in as a mock user to bypass Firebase Auth
    const mockUser: UserProfile = {
      uid: 'dev-user-123',
      email: 'dev@ecometric.test',
      display_name: 'Developer',
      organization: 'org-test-123',
      role: 'engineer',
      created_at: null as any,
    }
    dispatch(setUser(mockUser))
  }, [dispatch])

  return <>{children}</>
}

// ── Root App ─────────────────────────────────────────────────────────
export default function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthListener>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Public — Marketing Landing Page (built last per PRD Phase 8) */}
                <Route path="/" element={<LandingPage />} />

                {/* Auth pages — public only (redirect if already logged in) */}
                <Route
                  path="/login"
                  element={<PublicOnly><LoginPage /></PublicOnly>}
                />
                <Route
                  path="/register"
                  element={<PublicOnly><RegisterPage /></PublicOnly>}
                />

                {/* Public tokenized verifier portal — no auth required */}
                <Route path="/verifier/:token" element={<VerifierPage />} />

                {/* Protected application routes */}
                <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />
                <Route path="/projects/new" element={<RequireAuth><ProjectSetupPage /></RequireAuth>} />
                <Route path="/projects/:id/setup" element={<RequireAuth><ProjectSetupPage /></RequireAuth>} />
                <Route path="/projects/:id/inventory" element={<RequireAuth><InventoryPage /></RequireAuth>} />
                <Route path="/projects/:id/transportation" element={<RequireAuth><TransportationPage /></RequireAuth>} />
                <Route path="/projects/:id/calculate" element={<RequireAuth><CalculatePage /></RequireAuth>} />
                <Route path="/projects/:id/hotspots" element={<RequireAuth><HotspotsPage /></RequireAuth>} />
                <Route path="/projects/:id/export" element={<RequireAuth><ExportPage /></RequireAuth>} />
                <Route path="/projects/:id/publish" element={<RequireAuth><PublishPage /></RequireAuth>} />
                <Route path="/portfolio" element={<RequireAuth><PortfolioPage /></RequireAuth>} />
                <Route path="/settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />

                {/* 404 */}
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </AuthListener>
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  )
}
