/**
 * src/components/molecules/FeatureCard.tsx
 *
 * PRD §4.6 feature-card:
 *   Background: white, 1px hairline border, 32px padding, 2px radius
 *   Contains: Font Awesome icon + heading + body text
 *   Corner square: bottom-right (differentiates from product-card which uses top-left)
 *   NO drop shadow
 *
 * PRD §6.1: Used in marketing landing page 4-up features grid
 * PRD §6.5: Used in right-pane compliance sidebar
 * PRD §6.8: Used in export action cards
 */

import { CornerSquare, type CornerSquarePosition } from '@/components/atoms/CornerSquare'
import { BadgeTag, type BadgeTagColor } from '@/components/atoms/BadgeTag'
import type { IconDefinition } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import type { ReactNode } from 'react'

export interface FeatureCardProps {
  /** Font Awesome icon — required for feature card layout */
  icon?: IconDefinition
  /** Optional badge above heading */
  badge?: string
  badgeColor?: BadgeTagColor
  /** Card heading */
  heading: string
  /** Body copy */
  body: string | ReactNode
  /** Optional CTA at bottom */
  action?: ReactNode
  /** Corner square position — defaults to bottom-right (different from ProductCard) */
  cornerPosition?: CornerSquarePosition
  /** Highlight card with green-border variant */
  highlighted?: boolean
  className?: string
}

export function FeatureCard({
  icon,
  badge,
  badgeColor = 'default',
  heading,
  body,
  action,
  cornerPosition = 'bottom-right',
  highlighted = false,
  className = '',
}: FeatureCardProps) {
  const borderClass = highlighted ? 'border-primary border-2' : ''

  return (
    <div className={`feature-card relative ${borderClass} ${className}`}>
      {/* Single corner square */}
      <CornerSquare position={cornerPosition} size="sm" />

      <div className="flex flex-col gap-lg">
        {/* Optional badge */}
        {badge && (
          <div>
            <BadgeTag color={badgeColor}>{badge}</BadgeTag>
          </div>
        )}

        {/* Icon */}
        {icon && (
          <div
            className="w-[44px] h-[44px] flex items-center justify-center bg-primary/10 rounded-sm"
            aria-hidden="true"
          >
            <FontAwesomeIcon icon={icon} className="text-primary text-heading-md" />
          </div>
        )}

        {/* Heading */}
        <h3 className="text-heading-sm text-ink">{heading}</h3>

        {/* Body */}
        <div className="text-body-sm text-mute">{body}</div>

        {/* Optional action */}
        {action && <div className="mt-md">{action}</div>}
      </div>
    </div>
  )
}
