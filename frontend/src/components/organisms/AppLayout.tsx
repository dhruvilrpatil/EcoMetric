/**
 * src/components/organisms/AppLayout.tsx
 *
 * Authenticated application layout wrapper.
 * Renders: PrimaryNav + BreadcrumbBar + (optional SubNavStrip) + main content
 *
 * All interior authenticated pages use this layout.
 * PRD §4.7: Alternating dark/light section rhythm is handled by page content,
 * not this layout.
 */

import type { ReactNode } from 'react'
import { PrimaryNav } from './PrimaryNav'
import { BreadcrumbBar, type BreadcrumbItem } from './BreadcrumbBar'
import { SubNavStrip } from './SubNavStrip'
import type { ProjectStep } from '@/types'

export interface AppLayoutProps {
  /** Breadcrumb navigation items */
  breadcrumbs: BreadcrumbItem[]
  /** If provided, renders the in-project sub-nav strip */
  projectNav?: {
    projectId: string
    currentStep: ProjectStep
    highestCompletedStep: ProjectStep
    maxNavigableStep?: ProjectStep
    confirmBackNavigation?: boolean
  }
  children: ReactNode
  /** Utility bar override — used for READ-ONLY VERIFIER MODE badge */
  utilityBarText?: string
}

export function AppLayout({
  breadcrumbs,
  projectNav,
  children,
  utilityBarText,
}: AppLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col bg-surface-soft">
      {/* Sticky navigation chrome */}
      <PrimaryNav utilityBarText={utilityBarText} />
      <BreadcrumbBar items={breadcrumbs} />

      {/* In-project workflow step nav */}
      {projectNav && (
        <SubNavStrip
          projectId={projectNav.projectId}
          currentStep={projectNav.currentStep}
          highestCompletedStep={projectNav.highestCompletedStep}
          maxNavigableStep={projectNav.maxNavigableStep}
          confirmBackNavigation={projectNav.confirmBackNavigation}
        />
      )}

      {/* Page content */}
      <main id="main-content" className="flex-1">
        {children}
      </main>
    </div>
  )
}
