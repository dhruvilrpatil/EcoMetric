/**
 * src/components/atoms/BadgeTag.tsx
 *
 * PRD §4.6 — Tabs & Chips
 * badge-tag: surface-soft bg, body text, caption-md uppercase, 4px/10px padding, 2px radius
 *
 * Usage: <BadgeTag>IN PROGRESS</BadgeTag>
 * Optional color overrides for semantic states (warning amber, error red).
 */

import type { HTMLAttributes, ReactNode } from 'react'

export type BadgeTagColor = 'default' | 'warning' | 'error' | 'success' | 'info'

export interface BadgeTagProps extends HTMLAttributes<HTMLSpanElement> {
  color?: BadgeTagColor
  children: ReactNode
}

// Color → Tailwind override (still using token colors from tailwind.config.ts)
const COLOR_CLASS: Record<BadgeTagColor, string> = {
  default: 'bg-surface-soft text-body',
  warning: 'bg-warning-bright/20 text-warning',
  error:   'bg-error/15 text-error',
  success: 'bg-primary/15 text-success-deep',
  info:    'bg-link-blue/10 text-link-blue',
}

export function BadgeTag({ color = 'default', children, className = '', ...rest }: BadgeTagProps) {
  return (
    <span
      {...rest}
      className={`badge-tag ${COLOR_CLASS[color]} ${className}`.trim()}
    >
      {children}
    </span>
  )
}
