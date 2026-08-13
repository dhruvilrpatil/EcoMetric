import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCalculator,
  faSpinner,
  faArrowRight,
  faCheckCircle,
  faTimesCircle,
  faRotateRight,
} from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { ButtonPrimary, ButtonOutline } from '@/components/atoms/Button'
import { NotificationCard } from '@/components/molecules/NotificationCard'
import { LciaResultsTable } from '@/components/organisms/LciaResultsTable'
import { useCalculateLca, useJobStatus, useLcaResults, useLciaMatrix } from '@/hooks/useLcaResults'

export default function CalculatePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [jobId, setJobId] = useState<string | null>(null)
  const [started, setStarted] = useState(false)
  const [selectedMethodology, setSelectedMethodology] = useState<string>('EN_15804_A2')

  const calculateMutation = useCalculateLca(id!)
  const { data: persistedResult } = useLcaResults(id!, !!id)

  const activeJobId = jobId ?? persistedResult?.run_id ?? null

  // Poll job status — enabled while a job is active or persisted on the backend
  const isPolling = !!activeJobId
  const { data: jobStatus } = useJobStatus(id!, activeJobId, isPolling)

  // Fetch full LCIA matrix for selected methodology
  const { data: matrixData, isLoading: isMatrixLoading } = useLciaMatrix(
    id!,
    selectedMethodology,
    !!persistedResult?.is_final
  )

  const currentStatus =
    jobStatus?.status ??
    (persistedResult?.is_final ? 'complete' : persistedResult ? 'running' : undefined)

  const jobState: 'idle' | 'running' | 'complete' | 'failed' =
    currentStatus === 'complete'
      ? 'complete'
      : currentStatus === 'failed'
      ? 'failed'
      : currentStatus === 'running'
      ? 'running'
      : 'idle'

  const progress =
    jobStatus?.progress ??
    (persistedResult ? (persistedResult.is_final ? 100 : 50) : started ? 5 : 0)

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
      console.error('Calculation trigger failed:', err)
    }
  }

  const effectiveMatrix = matrixData || persistedResult?.matrix

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div
        className={`w-full mx-auto px-hero-h py-section transition-all duration-300 ${
          jobState === 'complete' ? 'max-w-7xl' : 'max-w-[640px]'
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4 mb-xl">
          <div>
            <h1 className="text-heading-lg text-ink mb-1">Calculation Engine</h1>
            <p className="text-body-md text-mute">
              Execute the EN 15804+A2 &amp; ISO 21930 matrix LCA algorithm across all lifecycle stages.
            </p>
          </div>

          {jobState === 'complete' && (
            <div className="flex items-center gap-3">
              <ButtonOutline
                iconLeft={faRotateRight}
                onClick={handleStartCalculation}
                loading={calculateMutation.isPending}
              >
                Recalculate
              </ButtonOutline>
              <ButtonPrimary
                iconRight={faArrowRight}
                onClick={() => navigate(`/projects/${id}/hotspots`)}
              >
                View Hotspot Analysis
              </ButtonPrimary>
            </div>
          )}
        </div>

        {calculateMutation.isError && (
          <div className="mb-xl">
            <NotificationCard variant="error" title="Engine Error">
              {(calculateMutation.error as any)?.message || 'Failed to start calculation.'}
            </NotificationCard>
          </div>
        )}

        {/* ── IDLE / RUNNING / FAILED STATES ──────────────────────────── */}
        {jobState !== 'complete' && (
          <div className="bg-white border border-hairline p-xxl rounded-sm flex flex-col items-center justify-center text-center min-h-[320px]">
            {/* IDLE */}
            {jobState === 'idle' && (
              <>
                <div className="w-[80px] h-[80px] rounded-full bg-surface-soft flex items-center justify-center mb-lg">
                  <FontAwesomeIcon icon={faCalculator} className="text-heading-xl text-primary" />
                </div>
                <h2 className="text-heading-sm text-ink mb-sm">Ready to Calculate</h2>
                <p className="text-body-sm text-mute max-w-[400px] mb-xl">
                  The engine will solve the technology matrix, check ISO 14044 cut-off rules, and compute LCIA results across all 37 environmental, resource, and waste indicators.
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
                  onClick={() => {
                    setStarted(false)
                    setJobId(null)
                  }}
                >
                  Retry Calculation
                </ButtonPrimary>
              </>
            )}
          </div>
        )}

        {/* ── COMPLETE STATE: FULL LCIA MATRIX ────────────────────────── */}
        {jobState === 'complete' && (
          <div className="space-y-6">
            {/* Top KPI Summary Bar */}
            <div className="bg-white border border-border-card rounded-xl p-5 shadow-sm flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center text-success text-xl">
                  <FontAwesomeIcon icon={faCheckCircle} />
                </div>
                <div>
                  <div className="text-xs font-semibold text-text-muted uppercase tracking-wider">
                    Total Lifecycle Carbon Footprint (GWP-total)
                  </div>
                  <div className="text-2xl font-black text-text-primary">
                    {persistedResult?.carbon_footprint_kg_co2e != null
                      ? `${persistedResult.carbon_footprint_kg_co2e.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })} kg CO₂e`
                      : 'Calculated'}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6 text-xs text-text-secondary">
                <div>
                  <span className="text-text-muted block">Standard:</span>
                  <span className="font-semibold text-text-primary">EN 15804+A2 &amp; ISO 21930</span>
                </div>
                <div>
                  <span className="text-text-muted block">Database:</span>
                  <span className="font-semibold text-text-primary">Ecoinvent 3.12 (Cutoff)</span>
                </div>
                <div>
                  <span className="text-text-muted block">Status:</span>
                  <span className="font-semibold text-success flex items-center gap-1">
                    <FontAwesomeIcon icon={faCheckCircle} /> Ready for EPD
                  </span>
                </div>
              </div>
            </div>

            {/* Matrix Component */}
            {effectiveMatrix ? (
              <LciaResultsTable
                matrixData={effectiveMatrix}
                selectedMethodology={selectedMethodology}
                onMethodologyChange={setSelectedMethodology}
                isLoading={isMatrixLoading}
              />
            ) : (
              <div className="bg-white border border-border-card rounded-xl p-12 text-center text-text-muted">
                <FontAwesomeIcon icon={faSpinner} spin className="text-3xl text-primary mb-3" />
                <p className="text-sm font-medium">Formatting multi-indicator matrix results…</p>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
