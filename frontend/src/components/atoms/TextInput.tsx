/**
 * src/components/atoms/TextInput.tsx
 *
 * PRD §4.6 Inputs:
 *   text-input:         white bg, 1px hairline border, 44px height, 2px radius
 *   text-input-focused: 2px solid green border (via CSS :focus)
 *
 * CRITICAL RULES:
 *   - All form inputs MUST have visible labels AND aria-labels (PRD accessibility rule)
 *   - Focus ring: 2px solid #76b900 (global CSS handles :focus-visible)
 *   - Never use inline style overrides for colors/spacing
 */

import { forwardRef, InputHTMLAttributes, ReactNode } from 'react'

export interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Visible label shown above the input — REQUIRED per PRD accessibility rules */
  label: string
  /** Additional hint text shown below input */
  hint?: string
  /** Error message — shown in error-red below input */
  error?: string
  /** Icon rendered on left side of input */
  iconLeft?: ReactNode
  /** Full-width (default true) */
  fullWidth?: boolean
  /** Input ID — used for label htmlFor. Auto-generated from label if not provided */
  id?: string
}

export const TextInput = forwardRef<HTMLInputElement, TextInputProps>(
  (
    {
      label,
      hint,
      error,
      iconLeft,
      fullWidth = true,
      id,
      className = '',
      required,
      ...rest
    },
    ref
  ) => {
    const inputId = id ?? `input-${label.toLowerCase().replace(/\s+/g, '-')}`
    const hasError = Boolean(error)

    return (
      <div className={`flex flex-col gap-xs ${fullWidth ? 'w-full' : ''}`}>
        {/* Visible label — PRD mandatory */}
        <label
          htmlFor={inputId}
          className="text-body-strong text-body"
        >
          {label}
          {required && (
            <span className="text-error ml-xxs" aria-label="required">*</span>
          )}
        </label>

        {/* Input wrapper */}
        <div className="relative">
          {iconLeft && (
            <span
              className="absolute left-lg top-1/2 -translate-y-1/2 text-stone pointer-events-none"
              aria-hidden="true"
            >
              {iconLeft}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            aria-label={label}
            aria-required={required}
            aria-invalid={hasError}
            aria-describedby={
              [error ? `${inputId}-error` : null, hint ? `${inputId}-hint` : null]
                .filter(Boolean)
                .join(' ') || undefined
            }
            className={[
              'text-input',
              iconLeft ? 'pl-xxl' : '',
              hasError ? 'border-error focus:border-error' : '',
              className,
            ].join(' ').trim()}
            {...rest}
          />
        </div>

        {/* Hint text */}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="text-caption-sm text-mute">
            {hint}
          </p>
        )}

        {/* Error message — inline, never browser alert */}
        {error && (
          <p
            id={`${inputId}-error`}
            role="alert"
            className="text-caption-sm text-error flex items-center gap-xxs"
          >
            <span aria-hidden="true">✕</span>
            {error}
          </p>
        )}
      </div>
    )
  }
)

TextInput.displayName = 'TextInput'
