/**
 * src/components/atoms/Button.tsx
 *
 * All PRD §4.6 button variants as a single typed component.
 *
 * PRD CRITICAL RULES enforced here:
 *   - Height 44px on all variants (WCAG AA touch target)
 *   - Border radius: rounded-sm (2px) ONLY
 *   - button-primary: green fill (#76b900), black text
 *   - button-primary appears once per fold MAX — consumer must enforce
 *   - Focus: 2px solid #76b900 via global CSS (no override here)
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core'

// ── Variant type ──────────────────────────────────────────────────────────────
export type ButtonVariant =
  | 'primary'
  | 'outline'
  | 'outline-dark'
  | 'ghost'
  | 'disabled'

// ── Size ─────────────────────────────────────────────────────────────────────
export type ButtonSize = 'lg' | 'md' | 'sm'

// ── Props ─────────────────────────────────────────────────────────────────────
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Icon rendered before label text */
  iconLeft?: IconDefinition
  /** Icon rendered after label text */
  iconRight?: IconDefinition
  /** Full-width block button */
  fullWidth?: boolean
  /** Show spinner and block interaction */
  loading?: boolean
  children: ReactNode
}

// ── Variant → className map (all use PRD design token classes from index.css) ─
const VARIANT_CLASS: Record<ButtonVariant, string> = {
  'primary':      'btn-primary',
  'outline':      'btn-outline',
  'outline-dark': 'btn-outline-dark',
  'ghost':        'btn-ghost',
  'disabled':     'btn-disabled',
}

// ── Size overrides (font only — height is always 44px per PRD) ───────────────
const SIZE_FONT_CLASS: Record<ButtonSize, string> = {
  lg: 'text-button-lg',
  md: 'text-button-md',
  sm: 'text-button-sm',
}

export function Button({
  variant = 'primary',
  size = 'md',
  iconLeft,
  iconRight,
  fullWidth = false,
  loading = false,
  disabled,
  children,
  className = '',
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || variant === 'disabled' || loading

  const baseClass = VARIANT_CLASS[isDisabled && variant !== 'ghost' ? 'disabled' : variant]
  const fontClass  = SIZE_FONT_CLASS[size]
  const widthClass = fullWidth ? 'w-full' : ''

  return (
    <button
      {...rest}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      className={`${baseClass} ${fontClass} ${widthClass} ${className}`.trim()}
    >
      {loading && (
        <svg
          className="animate-spin mr-sm"
          width="16" height="16" viewBox="0 0 16 16"
          fill="none" aria-hidden="true"
        >
          <circle
            cx="8" cy="8" r="6"
            stroke="currentColor" strokeWidth="2"
            strokeDasharray="28 8" strokeLinecap="round"
          />
        </svg>
      )}

      {iconLeft && !loading && (
        <FontAwesomeIcon icon={iconLeft} className="mr-sm" aria-hidden="true" />
      )}

      <span>{children}</span>

      {iconRight && (
        <FontAwesomeIcon icon={iconRight} className="ml-sm" aria-hidden="true" />
      )}
    </button>
  )
}

// ── Convenience exports matching PRD naming ────────────────────────────────────
export function ButtonPrimary(props: Omit<ButtonProps, 'variant'>) {
  return <Button variant="primary" {...props} />
}

export function ButtonOutline(props: Omit<ButtonProps, 'variant'>) {
  return <Button variant="outline" {...props} />
}

export function ButtonOutlineDark(props: Omit<ButtonProps, 'variant'>) {
  return <Button variant="outline-dark" {...props} />
}

export function ButtonGhost(props: Omit<ButtonProps, 'variant'>) {
  return <Button variant="ghost" {...props} />
}
