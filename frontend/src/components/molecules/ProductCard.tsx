/**
 * src/components/molecules/ProductCard.tsx
 *
 * PRD §4.6 product-card:
 *   Background: white, 1px hairline border, 24px padding, 2px radius
 *   Corner square: top-left (sm, 12×12px)
 *   Contains: BadgeTag status, card-title, body-sm metadata, step progress bar,
 *             ghost-link footer action
 *
 * PRD §6.3: Used in project dashboard 3-up grid
 */

import { CornerSquare } from '@/components/atoms/CornerSquare'
import { BadgeTag, type BadgeTagColor } from '@/components/atoms/BadgeTag'
import { ButtonGhost } from '@/components/atoms/Button'
import { faArrowRight } from '@fortawesome/free-solid-svg-icons'
import type { ProjectStatus, ProjectStep } from '@/types'

// Map PRD project status to badge display text and color
const STATUS_LABEL: Record<ProjectStatus, string> = {
  draft:                'DRAFT',
  in_progress:          'IN PROGRESS',
  pending_verification: 'PENDING VERIFICATION',
  published:            'PUBLISHED',
}

const STATUS_COLOR: Record<ProjectStatus, BadgeTagColor> = {
  draft:                'default',
  in_progress:          'info',
  pending_verification: 'warning',
  published:            'success',
}

export interface ProductCardProps {
  projectName: string
  standard: string
  functionalUnit: string
  lastEdited: string
  status: ProjectStatus
  currentStep: ProjectStep
  /** Called when "Open Project →" is clicked */
  onOpen: () => void
  className?: string
}

/** Thin green step-progress bar (PRD §6.3) — steps 1–6 */
function StepProgressBar({ currentStep }: { currentStep: ProjectStep }) {
  const pct = Math.round(((currentStep - 1) / 5) * 100)
  return (
    <div className="flex flex-col gap-xs">
      <div className="flex justify-between">
        <span className="text-caption-sm text-mute">Step {currentStep} of 6</span>
        <span className="text-caption-sm text-mute">{pct}%</span>
      </div>
      {/* Track */}
      <div className="w-full h-xxs bg-hairline rounded-none" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        {/* Fill — green */}
        <div
          className="h-full bg-primary rounded-none transition-all duration-normal"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export function ProductCard({
  projectName,
  standard,
  functionalUnit,
  lastEdited,
  status,
  currentStep,
  onOpen,
  className = '',
}: ProductCardProps) {
  return (
    <article className={`product-card relative ${className}`}>
      {/* PRD: corner-square top-left */}
      <CornerSquare position="top-left" size="sm" />

      <div className="flex flex-col gap-lg h-full">
        {/* Status badge */}
        <div className="pt-md">
          <BadgeTag color={STATUS_COLOR[status]}>
            {STATUS_LABEL[status]}
          </BadgeTag>
        </div>

        {/* Project name */}
        <h3 className="text-card-title text-ink">{projectName}</h3>

        {/* Metadata row */}
        <p className="text-body-sm text-mute flex flex-col gap-xxs">
          <span>{standard}</span>
          <span>{functionalUnit}</span>
          <span>Last edited: {lastEdited}</span>
        </p>

        {/* Step progress bar */}
        <div className="mt-auto pt-lg border-t border-hairline">
          <StepProgressBar currentStep={currentStep} />
        </div>

        {/* Ghost link CTA */}
        <ButtonGhost
          onClick={onOpen}
          aria-label={`Open project ${projectName}`}
          iconRight={faArrowRight}
        >
          Open Project
        </ButtonGhost>
      </div>
    </article>
  )
}
