/**
 * src/components/organisms/SubNavStrip.tsx
 *
 * PRD §4.6 sub-nav-strip: 56px, surface-soft, 1px bottom border, sticky
 * PRD §5.3 In-Project Sub-Navigation:
 *   Steps 1–6 rendered as PillTab components
 *   Active = pill-tab-active (black bg)
 *   Locked (ahead of progress) = ash text, non-clickable
 *   Sticky beneath the breadcrumb-bar
 *
 * Labels: "1. Setup → 2. Inventory → 3. Calculate → 4. Hotspots → 5. Export → 6. Publish"
 */

import { useNavigate } from 'react-router-dom'
import { PillTab } from '@/components/atoms/PillTab'
import { useProject } from '@/hooks/useProjects'
import { auditProjectCompleteness } from '@/lib/completeness'
import type { ProjectStep } from '@/types'

export interface SubNavStripProps {
  projectId: string
  currentStep: ProjectStep
  /** Highest step the user has reached (unlocks navigation to completed steps) */
  highestCompletedStep: ProjectStep
  /** Optional ceiling for the furthest step the user may jump to */
  maxNavigableStep?: ProjectStep
  /** When true, prompt before jumping backward while a calculation is in progress */
  confirmBackNavigation?: boolean
}

const STEPS: Array<{ step: ProjectStep; label: string; path: string }> = [
  { step: 1, label: '1. Setup',          path: 'setup' },
  { step: 2, label: '2. Inventory',      path: 'inventory' },
  { step: 3, label: '3. Transportation', path: 'transportation' },
  { step: 4, label: '4. Calculate',      path: 'calculate' },
  { step: 5, label: '5. Hotspots',       path: 'hotspots' },
  { step: 6, label: '6. Export',         path: 'export' },
  { step: 7, label: '7. Publish',        path: 'publish' },
]

export function SubNavStrip({
  projectId,
  currentStep,
  highestCompletedStep,
  maxNavigableStep,
  confirmBackNavigation,
}: SubNavStripProps) {
  const navigate = useNavigate()
  const { data: project } = useProject(projectId !== 'new' ? projectId : undefined)
  const completeness = auditProjectCompleteness(project)

  function getPath(step: typeof STEPS[number]) {
    if (step.step === 1) {
      return projectId && projectId !== 'new' ? `/projects/${projectId}/setup` : '/projects/new'
    }
    return `/projects/${projectId}/${step.path}`
  }

  return (
    <nav
      aria-label="Project workflow steps"
      className="sub-nav-strip"
      role="tablist"
    >
      <div className="w-full max-w-content-max mx-auto flex items-center justify-between gap-xs overflow-x-auto scrollbar-thin">
        <div className="flex items-center gap-xs">
          {STEPS.map((step) => {
            const isActive = step.step === currentStep
            const unlockedStep = maxNavigableStep ?? ((highestCompletedStep + 1) as ProjectStep)
            const isLocked = step.step > unlockedStep
            const shouldConfirmBack = confirmBackNavigation && currentStep === 4 && step.step <= 2

            return (
              <PillTab
                key={step.step}
                active={isActive}
                locked={isLocked}
                aria-label={`Step ${step.step}: ${step.label.replace(/^\d+\. /, '')}`}
                onClick={() => {
                  if (isLocked || isActive) return
                  if (shouldConfirmBack) {
                    const shouldLeave = window.confirm(
                      'EPD calculation is still in progress. Select OK to continue calculating here, or Cancel to go back to Inventory.'
                    )
                    if (!shouldLeave) navigate(getPath(step))
                    return
                  }
                  navigate(getPath(step))
                }}
              >
                {step.label}
              </PillTab>
            )
          })}
        </div>

        {projectId && projectId !== 'new' && (
          <div className="flex items-center gap-xs px-md py-xs bg-white border border-hairline rounded-sm shadow-xs whitespace-nowrap ml-md">
            <span className="text-caption-sm text-mute uppercase font-semibold">Completeness:</span>
            <span
              className={`text-body-sm font-bold font-mono ${
                completeness.scorePct === 100
                  ? 'text-green-600'
                  : completeness.scorePct >= 60
                  ? 'text-amber-600'
                  : 'text-red-600'
              }`}
            >
              {completeness.scorePct}%
            </span>
          </div>
        )}
      </div>
    </nav>
  )
}
