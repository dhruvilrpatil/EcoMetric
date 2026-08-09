/**
 * src/pages/CalculatePage.tsx
 *
 * PRD §6.6 Step 3: Calculation
 * Triggers LCA via FastAPI → AWS RDS. Polls job status with React Query auto-refetch.
 */

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCalculator, faSpinner, faArrowRight, faCheckCircle, faTimesCircle } from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { ButtonPrimary } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'
import { useCalculateLca, useJobStatus, useLcaResults } from '@/hooks/useLcaResults'

export default function CalculatePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [jobId, setJobId] = useState<string | null>(null)
  const [started, setStarted] = useState(false)

  const calculateMutation = useCalculateLca(id!)
  const { data: persistedResult } = useLcaResults(id!, !!id)

  const activeJobId = jobId ?? persistedResult?.run_id ?? null

  // Poll job status — enabled while a job is active or persisted on the backend
  const isPolling = !!activeJobId
  const { data: jobStatus } = useJobStatus(id!, activeJobId, isPolling)

  const currentStatus = jobStatus?.status ?? (persistedResult?.is_final ? 'complete' : persistedResult ? 'running' : undefined)

  const jobState: 'idle' | 'running' | 'complete' | 'failed' =
    currentStatus === 'complete' ? 'complete'
      : currentStatus === 'failed' ? 'failed'
        : currentStatus === 'running' ? 'running'
          : 'idle'

  const progress = jobStatus?.progress ?? (persistedResult ? (persistedResult.is_final ? 100 : 50) : started ? 5 : 0)

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Inventory', to: `/projects/${id}/inventory` },
    { label: 'Calculation' },
  ]

  const projectNav = {
    projectId: id || 'new',
    currentStep: 4 as const,
    highestCompletedStep: (jobState === 'complete' ? 4 : 3) as any,
    maxNavigableStep: (jobState === 'complete' ? 5 : 4) as any,
    confirmBackNavigation: jobState === 'running',
  }

  async function handleStartCalculation() {
    if (!id) return
    setStarted(true)

    try {
      const result = await calculateMutation.mutateAsync()
      setJobId(result.job_id)
    } catch (err: any) {
      // started=true but no jobId → shows as running then fails gracefully
      console.error('Calculation trigger failed:', err)
    }
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-[640px] mx-auto px-hero-h py-section">

        <h1 className="text-heading-lg text-ink mb-md">Calculation Engine</h1>
        <p className="text-body-md text-mute mb-xl">
          Execute the EN 15804+A2 matrix LCA algorithm against your Bill of Materials and the Ecoinvent 3.12 background database.
        </p>

        {calculateMutation.isError && (
          <div className="mb-xl">
            <NotificationCard variant="error" title="Engine Error">
              {(calculateMutation.error as any)?.message || 'Failed to start calculation.'}
            </NotificationCard>
          </div>
        )}

        <div className="bg-white border border-hairline p-xxl rounded-sm flex flex-col items-center justify-center text-center min-h-[320px]">

          {/* IDLE */}
          {jobState === 'idle' && (
            <>
              <div className="w-[80px] h-[80px] rounded-full bg-surface-soft flex items-center justify-center mb-lg">
                <FontAwesomeIcon icon={faCalculator} className="text-heading-xl text-primary" />
              </div>
              <h2 className="text-heading-sm text-ink mb-sm">Ready to Calculate</h2>
              <p className="text-body-sm text-mute max-w-[400px] mb-xl">
                The engine will solve the technology matrix, check ISO 14044 cut-off rules, and compute LCIA results across all 19 EF 3.1 impact categories.
              </p>
              <ButtonPrimary size="lg" onClick={handleStartCalculation} loading={calculateMutation.isPending}>
                Run LCA Calculation
              </ButtonPrimary>
            </>
          )}

          {/* RUNNING */}
          {jobState === 'running' && (
            <div className="w-full max-w-[420px] flex flex-col items-center">
              <FontAwesomeIcon icon={faSpinner} spin className="text-heading-xl text-primary mb-lg" />
              <h2 className="text-heading-sm text-ink mb-md">Computing…</h2>
              <div className="w-full h-[6px] bg-surface-soft rounded-full overflow-hidden mb-xs">
                <div
                  className="h-full bg-primary transition-all duration-500 rounded-full"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="flex justify-between w-full text-caption-sm text-mute">
                <span>Building matrices &amp; solving inventory…</span>
                <span>{progress}%</span>
              </div>
              <p className="text-caption-sm text-mute mt-lg">
                Fetching elementary exchanges from Ecoinvent 3.12 (AWS RDS)
              </p>
            </div>
          )}

          {/* COMPLETE */}
          {jobState === 'complete' && (
            <>
              <div className="w-[80px] h-[80px] rounded-full bg-success/10 flex items-center justify-center mb-lg">
                <FontAwesomeIcon icon={faCheckCircle} className="text-heading-xl text-success" />
              </div>
              <h2 className="text-heading-sm text-ink mb-sm">Calculation Complete</h2>
              {jobStatus?.carbon_footprint_kg_co2e != null && (
                <p className="text-heading-md text-primary font-bold mb-xs">
                  {jobStatus.carbon_footprint_kg_co2e.toFixed(2)} kg CO₂e
                </p>
              )}
              <p className="text-body-sm text-mute max-w-[400px] mb-xl">
                The matrix has been solved and all 19 EF 3.1 impact categories have been computed.
              </p>
              <div className="flex gap-lg">
                <ButtonPrimary iconRight={faArrowRight} onClick={() => navigate(`/projects/${id}/hotspots`)}>
                  View Hotspot Analysis
                </ButtonPrimary>
              </div>
            </>
          )}

          {/* FAILED */}
          {jobState === 'failed' && (
            <>
              <div className="w-[80px] h-[80px] rounded-full bg-error/10 flex items-center justify-center mb-lg">
                <FontAwesomeIcon icon={faTimesCircle} className="text-heading-xl text-error" />
              </div>
              <h2 className="text-heading-sm text-ink mb-sm">Calculation Halted / Validation Failed</h2>
              <div className="bg-error/10 border border-error/30 rounded-sm p-md mb-xl text-left max-w-[500px]">
                <p className="text-body-sm text-error font-semibold mb-xs">
                  {jobStatus?.error_message?.includes('fabrication') || jobStatus?.error_message?.includes('mantissa')
                    ? '⚠️ Fabrication Detection Alert:'
                    : 'Calculation Error:'}
                </p>
                <p className="text-caption-md text-error">
                  {jobStatus?.error_message || 'An error occurred during LCA computation. Please check your project data and try again.'}
                </p>
              </div>
              <ButtonPrimary
                onClick={() => { setStarted(false); setJobId(null) }}
              >
                Retry Calculation
              </ButtonPrimary>
            </>
          )}

        </div>
      </div>
    </AppLayout>
  )
}
