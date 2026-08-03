/**
 * src/pages/RegisterPage.tsx
 *
 * PRD §6.2 Register page:
 *   - Full Name, Organization, Work Email, Password, Confirm Password
 *   - Role selector: 3 PillTab chips in a row
 *   - Password strength indicator (visual only — no % score)
 *   - button-primary: "Create Account" (once per fold)
 *   - Google SSO: "Continue with Google" (button-outline)
 *   - Inline NotificationCard on error
 *   - On success: creates Firestore profile → navigate /dashboard
 *
 * Validation: React Hook Form + Zod (registerSchema).
 */

import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faGoogle } from '@fortawesome/free-brands-svg-icons'
import { faArrowRight, faCheck, faXmark } from '@fortawesome/free-solid-svg-icons'

import { registerSchema, type RegisterFormData } from '@/lib/schemas'
import { useAuth } from '@/hooks/useAuth'
import { useAppSelector } from '@/store'
import { TextInput } from '@/components/atoms/TextInput'
import { PillTab } from '@/components/atoms/PillTab'
import { Button, ButtonPrimary } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'

// ── Role options ──────────────────────────────────────────────────────────────
const ROLES: Array<{ value: RegisterFormData['role']; label: string }> = [
  { value: 'engineer',   label: 'Sustainability Engineer' },
  { value: 'consultant', label: 'LCA Consultant' },
  { value: 'org_admin',  label: 'Portfolio Manager' },
]

// ── Password strength rules ───────────────────────────────────────────────────
interface PasswordRule {
  label: string
  met: (v: string) => boolean
}

const PASSWORD_RULES: PasswordRule[] = [
  { label: 'At least 8 characters',      met: (v) => v.length >= 8 },
  { label: 'One uppercase letter (A–Z)',  met: (v) => /[A-Z]/.test(v) },
  { label: 'One number (0–9)',            met: (v) => /[0-9]/.test(v) },
]

function PasswordStrengthIndicator({ password }: { password: string }) {
  if (!password) return null
  return (
    <ul className="flex flex-col gap-xxs mt-xs list-none" style={{ margin: 0, padding: 0 }}>
      {PASSWORD_RULES.map((rule) => {
        const met = rule.met(password)
        return (
          <li
            key={rule.label}
            className={`flex items-center gap-xs text-caption-sm ${met ? 'text-success-deep' : 'text-mute'}`}
          >
            <FontAwesomeIcon
              icon={met ? faCheck : faXmark}
              size="xs"
              className={met ? 'text-primary' : 'text-mute'}
              aria-hidden="true"
            />
            {rule.label}
          </li>
        )
      })}
    </ul>
  )
}

// ── RegisterPage ──────────────────────────────────────────────────────────────
export default function RegisterPage() {
  const navigate  = useNavigate()
  const { user }  = useAppSelector((s) => s.auth)
  const { loading, error, clearError, register: registerUser, signInWithGoogle } = useAuth()

  // Redirect if already signed in
  useEffect(() => {
    if (user) navigate('/dashboard', { replace: true })
  }, [user, navigate])

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'engineer' },
  })

  const passwordValue = watch('password', '')

  async function onSubmit(data: RegisterFormData) {
    const ok = await registerUser({
      email:        data.email,
      password:     data.password,
      fullName:     data.full_name,
      organization: data.organization,
      role:         data.role,
    })
    if (ok) navigate('/dashboard', { replace: true })
  }

  async function handleGoogle() {
    const ok = await signInWithGoogle()
    if (ok) navigate('/dashboard', { replace: true })
  }

  return (
    <div className="min-h-screen bg-surface-soft flex flex-col items-center justify-center px-hero-h py-section">

      {/* Auth card — 480px (wider than login for extra fields) */}
      <div
        className="w-full max-w-[480px] bg-surface border border-hairline rounded-sm"
        style={{ padding: '40px 40px' }}
      >
        {/* Wordmark */}
        <div className="text-center mb-xxl">
          <Link to="/" aria-label="EcoMetric home" className="text-heading-md font-bold text-ink inline-block">
            Quick<span className="text-primary">LCA</span>
          </Link>
          <p className="text-caption-md uppercase text-mute mt-xs tracking-caption">
            Create your free account
          </p>
        </div>

        {/* Inline error notification */}
        {error && (
          <div className="mb-xl">
            <NotificationCard variant="error" title="Registration failed">
              {error}
            </NotificationCard>
          </div>
        )}

        {/* Registration form */}
        <form
          id="register-form"
          onSubmit={handleSubmit(onSubmit)}
          noValidate
          className="flex flex-col gap-xl"
        >
          {/* Full Name */}
          <TextInput
            label="Full Name"
            id="register-full-name"
            type="text"
            autoComplete="name"
            placeholder="Jane Smith"
            required
            error={errors.full_name?.message}
            {...register('full_name')}
            onChange={() => { if (error) clearError() }}
          />

          {/* Organization */}
          <TextInput
            label="Organization"
            id="register-organization"
            type="text"
            autoComplete="organization"
            placeholder="Your company name"
            required
            error={errors.organization?.message}
            {...register('organization')}
            onChange={() => { if (error) clearError() }}
          />

          {/* Work Email */}
          <TextInput
            label="Work Email"
            id="register-email"
            type="email"
            autoComplete="email"
            placeholder="you@company.com"
            required
            error={errors.email?.message}
            {...register('email')}
            onChange={() => { if (error) clearError() }}
          />

          {/* Role selector — PillTab row */}
          <div className="flex flex-col gap-xs">
            <label className="text-body-strong text-body" id="role-label">
              Your Role
              <span className="text-error ml-xxs" aria-label="required">*</span>
            </label>
            <Controller
              name="role"
              control={control}
              render={({ field }) => (
                <div
                  role="radiogroup"
                  aria-labelledby="role-label"
                  className="flex flex-wrap gap-xs"
                >
                  {ROLES.map((role) => (
                    <PillTab
                      key={role.value}
                      active={field.value === role.value}
                      onClick={() => field.onChange(role.value)}
                      type="button"
                      aria-label={`Role: ${role.label}`}
                      aria-checked={field.value === role.value}
                    >
                      {role.label}
                    </PillTab>
                  ))}
                </div>
              )}
            />
            {errors.role && (
              <p role="alert" className="text-caption-sm text-error">
                {errors.role.message}
              </p>
            )}
          </div>

          {/* Password */}
          <div className="flex flex-col gap-xs">
            <TextInput
              label="Password"
              id="register-password"
              type="password"
              autoComplete="new-password"
              placeholder="Minimum 8 characters"
              required
              error={errors.password?.message}
              {...register('password')}
              onChange={() => { if (error) clearError() }}
            />
            {/* Real-time strength indicator */}
            <PasswordStrengthIndicator password={passwordValue} />
          </div>

          {/* Confirm Password */}
          <TextInput
            label="Confirm Password"
            id="register-confirm-password"
            type="password"
            autoComplete="new-password"
            placeholder="Repeat your password"
            required
            error={errors.confirm_password?.message}
            {...register('confirm_password')}
          />

          {/* PRIMARY CTA — button-primary, once per fold */}
          <ButtonPrimary
            type="submit"
            fullWidth
            loading={loading}
            disabled={loading}
            aria-label="Create your EcoMetric account"
            iconRight={faArrowRight}
          >
            Create Account
          </ButtonPrimary>
        </form>

        {/* ── Divider ──────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-lg my-xl">
          <div className="flex-1 h-px bg-hairline" />
          <span className="text-caption-sm text-mute uppercase">or</span>
          <div className="flex-1 h-px bg-hairline" />
        </div>

        {/* Google SSO — button-outline */}
        <Button
          variant="outline"
          fullWidth
          onClick={handleGoogle}
          disabled={loading}
          aria-label="Register with Google"
          iconLeft={faGoogle}
        >
          Continue with Google
        </Button>

        {/* Sign in link */}
        <p className="text-center text-body-sm text-mute mt-xl">
          Already have an account?{' '}
          <Link to="/login" className="text-link-blue hover:underline font-bold">
            Sign in
          </Link>
        </p>
      </div>

      {/* Legal fine-print */}
      <p className="text-utility-xs uppercase text-mute text-center mt-xl max-w-[480px]">
        By creating an account you agree to EcoMetric's{' '}
        <Link to="/#terms" className="hover:underline">Terms of Use</Link>
        {' '}and{' '}
        <Link to="/#privacy" className="hover:underline">Privacy Policy</Link>.
      </p>
    </div>
  )
}
