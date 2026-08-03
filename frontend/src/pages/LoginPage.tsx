/**
 * src/pages/LoginPage.tsx
 *
 * PRD §6.2 Sign In page:
 *   - Centered 420px card on surface-soft
 *   - Logo wordmark at top
 *   - Email + Password fields (TextInput)
 *   - Primary CTA: "Sign In" (button-primary, full-width)
 *   - Google SSO: "Continue with Google" (button-outline, full-width)
 *   - Forgot password link
 *   - Link to register
 *   - Inline NotificationCard on error — never alert()
 *   - All loading, success, error states visible
 *
 * PRD RULE: button-primary once per fold.
 * Auth: Firebase Auth email/password + Google SSO via useAuth hook.
 * Validation: React Hook Form + Zod.
 */

import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { faGoogle } from '@fortawesome/free-brands-svg-icons'
import { faArrowRight } from '@fortawesome/free-solid-svg-icons'

import { loginSchema, type LoginFormData } from '@/lib/schemas'
import { useAuth } from '@/hooks/useAuth'
import { useAppSelector } from '@/store'
import { TextInput } from '@/components/atoms/TextInput'
import { Button, ButtonPrimary } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'

export default function LoginPage() {
  const navigate  = useNavigate()
  const { user }  = useAppSelector((s) => s.auth)
  const { loading, error, clearError, signIn, signInWithGoogle } = useAuth()

  // Redirect if already signed in
  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: zodResolver(loginSchema) })

  async function onSubmit(data: LoginFormData) {
    const ok = await signIn(data.email, data.password)
    if (ok) navigate('/dashboard', { replace: true })
  }

  async function handleGoogle() {
    const ok = await signInWithGoogle()
    if (ok) navigate('/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen bg-surface-soft flex flex-col items-center justify-center px-hero-h py-section">

      {/* Auth card — 420px centered */}
      <div
        className="w-full max-w-[420px] bg-surface border border-hairline rounded-sm"
        style={{ padding: '40px 40px' }}
      >
        {/* Wordmark */}
        <div className="text-center mb-xxl">
          <Link
            to="/"
            aria-label="EcoMetric home"
            className="text-heading-md font-bold text-ink inline-block"
          >
            Quick<span className="text-primary">LCA</span>
          </Link>
          <p className="text-caption-md uppercase text-mute mt-xs tracking-caption">
            Sign in to your account
          </p>
        </div>

        {/* Inline error notification */}
        {error && (
          <div className="mb-xl">
            <NotificationCard variant="error" title="Sign-in failed">
              {error}
            </NotificationCard>
          </div>
        )}

        {/* Email / Password form */}
        <form
          id="login-form"
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="flex flex-col gap-xl"
        >
          <TextInput
            label="Work Email"
            id="login-email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            error={errors.email?.message}
            {...register('email')}
            onChange={() => { if (error) clearError() }}
          />

          <div className="flex flex-col gap-xs">
            <TextInput
              label="Password"
              id="login-password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register('password')}
              onChange={() => { if (error) clearError() }}
            />
            {/* Forgot password link — below the input */}
            <div className="flex justify-end">
              <Link
                to="/forgot-password"
                className="text-caption-sm text-link-blue hover:underline"
              >
                Forgot your password?
              </Link>
            </div>
          </div>

          {/* PRIMARY CTA — once per fold */}
          <ButtonPrimary
            type="submit"
            fullWidth
            loading={loading}
            disabled={loading}
            aria-label="Sign in to EcoMetric"
            iconRight={faArrowRight}
          >
            Sign In
          </ButtonPrimary>
        </form>

        {/* ── Divider ──────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-lg my-xl">
          <div className="flex-1 h-px bg-hairline" />
          <span className="text-caption-sm text-mute uppercase">or</span>
          <div className="flex-1 h-px bg-hairline" />
        </div>

        {/* Google SSO — button-outline, NOT button-primary */}
        <Button
          variant="outline"
          fullWidth
          onClick={handleGoogle}
          disabled={loading}
          aria-label="Sign in with Google"
          iconLeft={faGoogle}
        >
          Continue with Google
        </Button>

        {/* Register link */}
        <p className="text-center text-body-sm text-mute mt-xl">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="text-link-blue hover:underline font-bold"
          >
            Create one free
          </Link>
        </p>
      </div>

      {/* Legal fine-print */}
      <p className="text-utility-xs uppercase text-mute text-center mt-xl max-w-[420px]">
        By signing in you agree to EcoMetric's{' '}
        <Link to="/#terms" className="hover:underline">Terms of Use</Link>
        {' '}and{' '}
        <Link to="/#privacy" className="hover:underline">Privacy Policy</Link>.
      </p>
    </div>
  )
}
