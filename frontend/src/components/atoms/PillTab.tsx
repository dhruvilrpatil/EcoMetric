/**
 * src/components/atoms/PillTab.tsx
 *
 * PRD §4.6 — Tabs & Chips
 * pill-tab:        transparent bg, black text, button-sm type, 10px/18px padding, 2px radius
 * pill-tab-active: black bg, white text, same padding/radius
 *
 * WCAG AA: min 44×44px touch target enforced.
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react'

export interface PillTabProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean
  /** When true, tab is past current step — rendered in ash color, non-clickable */
  locked?: boolean
  children: ReactNode
}

export function PillTab({ active = false, locked = false, children, className = '', ...rest }: PillTabProps) {
  const base = active ? 'pill-tab-active' : 'pill-tab'

  // Locked state: ash text, non-interactive (PRD §5.3 — steps ahead of progress)
  const lockedClass = locked ? 'text-ash cursor-not-allowed pointer-events-none' : ''

  return (
    <button
      {...rest}
      role="tab"
      aria-selected={active}
      disabled={locked}
      aria-disabled={locked}
      className={`${base} ${lockedClass} ${className}`.trim()}
    >
      {children}
    </button>
  )
}
