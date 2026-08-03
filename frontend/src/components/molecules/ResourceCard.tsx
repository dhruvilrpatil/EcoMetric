/**
 * src/components/molecules/ResourceCard.tsx
 *
 * PRD §4.6 resource-card:
 *   Background: white, 1px hairline border, 24px padding, 2px radius
 *   Contains: badge-tag + optional thumbnail + heading + body + ghost-link
 *   Corner square: top-left
 *
 * PRD §6.1: Regulatory compliance section (CPR, ESPR, CBAM)
 * PRD §6.7: Sensitivity panel resource cards with HIGH SENSITIVITY badge
 */

import { CornerSquare } from '@/components/atoms/CornerSquare'
import { BadgeTag, type BadgeTagColor } from '@/components/atoms/BadgeTag'
import { ButtonGhost } from '@/components/atoms/Button'
import { faArrowRight } from '@fortawesome/free-solid-svg-icons'
import type { ReactNode } from 'react'

export interface ResourceCardProps {
  badge: string
  badgeColor?: BadgeTagColor
  heading: string
  body: string | ReactNode
  /** Link text for ghost-link CTA. If not provided, no CTA is shown */
  ctaLabel?: string
  /** Called when CTA ghost link is clicked */
  onCta?: () => void
  /** Optional thumbnail image URL */
  thumbnailUrl?: string
  /** Optional metric for sensitivity cards */
  metricValue?: string
  metricLabel?: string
  className?: string
}

export function ResourceCard({
  badge,
  badgeColor = 'default',
  heading,
  body,
  ctaLabel,
  onCta,
  thumbnailUrl,
  metricValue,
  metricLabel,
  className = '',
}: ResourceCardProps) {
  return (
    <article className={`resource-card relative ${className}`}>
      {/* Corner square — top-left per PRD */}
      <CornerSquare position="top-left" size="sm" />

      <div className="flex flex-col gap-md">
        {/* Thumbnail */}
        {thumbnailUrl && (
          <div className="w-full h-[120px] bg-surface-soft rounded-none overflow-hidden mb-sm">
            <img
              src={thumbnailUrl}
              alt=""
              aria-hidden="true"
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* Badge */}
        <div>
          <BadgeTag color={badgeColor}>{badge}</BadgeTag>
        </div>

        {/* Optional metric (sensitivity cards) */}
        {metricValue && (
          <div className="flex flex-col gap-xxs">
            <span className="text-display-lg text-primary font-bold leading-tight">
              {metricValue}
            </span>
            {metricLabel && (
              <span className="text-caption-sm text-mute">{metricLabel}</span>
            )}
          </div>
        )}

        {/* Heading */}
        <h3 className="text-card-title text-ink">{heading}</h3>

        {/* Body */}
        <div className="text-body-sm text-mute">{body}</div>

        {/* Ghost link CTA */}
        {ctaLabel && (
          <ButtonGhost
            onClick={onCta}
            aria-label={ctaLabel}
            iconRight={faArrowRight}
          >
            {ctaLabel}
          </ButtonGhost>
        )}
      </div>
    </article>
  )
}
