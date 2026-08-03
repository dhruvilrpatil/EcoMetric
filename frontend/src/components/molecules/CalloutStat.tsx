/**
 * src/components/molecules/CalloutStat.tsx
 *
 * PRD §4.6 callout-stat card:
 *   Background: white, 1px hairline border, 32px padding, 2px radius
 *   Large number displayed in --color-primary (green)
 *   Corner square: top-left (sm)
 *   PRD §6.3: Used in 4-up dashboard stats bar
 *   PRD §6.1: Used in marketing landing page stats
 */

import { CornerSquare } from '@/components/atoms/CornerSquare'
import type { ReactNode } from 'react'

export interface CalloutStatProps {
  /** The large metric value — e.g., "95%", "6 steps", "<10s" */
  value: string | ReactNode
  /** Descriptive caption below the number */
  caption: string
  /** Optional eyebrow label above the number */
  eyebrow?: string
  /** Color of the stat value. Defaults to primary (green) per PRD */
  valueColor?: 'primary' | 'warning' | 'error'
  /** Corner square position — default top-left per PRD */
  cornerPosition?: 'top-left' | 'bottom-right'
  className?: string
}

const VALUE_COLOR_CLASS: Record<string, string> = {
  primary: 'text-primary',
  warning: 'text-warning',
  error:   'text-error',
}

export function CalloutStat({
  value,
  caption,
  eyebrow,
  valueColor = 'primary',
  cornerPosition = 'top-left',
  className = '',
}: CalloutStatProps) {
  return (
    <div className={`callout-stat relative ${className}`}>
      {/* Single corner square — top-left OR bottom-right, never both */}
      <CornerSquare position={cornerPosition} size="sm" />

      <div className="flex flex-col gap-sm">
        {eyebrow && (
          <p className="text-caption-md uppercase text-mute tracking-caption">
            {eyebrow}
          </p>
        )}

        {/* Large metric value — display-lg, green by default */}
        <p className={`text-display-lg font-bold leading-tight ${VALUE_COLOR_CLASS[valueColor]}`}>
          {value}
        </p>

        {/* Caption */}
        <p className="text-body-sm text-mute">{caption}</p>
      </div>
    </div>
  )
}
