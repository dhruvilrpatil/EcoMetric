/**
 * src/pages/ExportPage.tsx
 *
 * PRD §6.8 Step 5: EPD Generation
 */

import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faCheck, faFilePdf, faArrowRight, faDownload, faSpinner } from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { ButtonPrimary, Button } from '@/components/atoms/Button'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { ApiError } from '@/lib/api'
import { auth } from '@/lib/firebase'
import { useProject } from '@/hooks/useProjects'
import { auditProjectCompleteness } from '@/lib/completeness'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export default function ExportPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: project } = useProject(id)
  const completeness = auditProjectCompleteness(project)

  const [isGeneratingEpd, setIsGeneratingEpd] = useState(false)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [epdUrl, setEpdUrl] = useState<string | null>(null)
  const [exportError, setExportError] = useState<string | null>(null)

  const previewUrl = useMemo(() => epdUrl, [epdUrl])

  useEffect(() => {
    return () => {
      if (epdUrl) URL.revokeObjectURL(epdUrl)
    }
  }, [epdUrl])

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Project Setup', to: `/projects/${id}/setup` },
    { label: 'Inventory', to: `/projects/${id}/inventory` },
    { label: 'Calculation', to: `/projects/${id}/calculate` },
    { label: 'Hotspots', to: `/projects/${id}/hotspots` },
    { label: 'Export' },
  ]

  const projectNav = {
    projectId: id || 'new',
    currentStep: 6 as const,
    highestCompletedStep: previewUrl ? 6 as const : 5 as const,
    maxNavigableStep: previewUrl ? 7 as const : 6 as const,
  }

  async function fetchBlob(path: string) {
    const token = auth.currentUser ? await auth.currentUser.getIdToken() : null
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    })

    if (!response.ok) {
      let message = `HTTP ${response.status}`
      try {
        const body = await response.json()
        message = body?.detail || body?.message || message
      } catch {
        // ignore parsing failures and surface the HTTP status instead
      }
      throw new ApiError(response.status, 'EXPORT_FAILED', message)
    }

    return response.blob()
  }

  async function downloadExport(path: string, filename: string, setLoading: (value: boolean) => void, previewPdf = false) {
    if (!window.confirm(`Download ${filename}?`)) return

    setExportError(null)
    setLoading(true)

    try {
      const blob = await fetchBlob(path)
      const objectUrl = URL.createObjectURL(blob)

      const link = document.createElement('a')
      link.href = objectUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      link.remove()

      if (previewPdf) {
        if (epdUrl) URL.revokeObjectURL(epdUrl)
        setEpdUrl(objectUrl)
      } else {
        URL.revokeObjectURL(objectUrl)
      }
    } catch (error: any) {
      setExportError(error?.message || 'Export failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateEPD = () => {
    void downloadExport(`/projects/${id}/exports/public-epd.pdf`, `${id}-public-epd.pdf`, setIsGeneratingEpd, true)
  }

  const handleGenerateReport = () => {
    void downloadExport(`/projects/${id}/exports/background-report.pdf`, `${id}-background-report.pdf`, setIsGeneratingReport)
  }

  const handleExportIlcd = () => {
    void downloadExport(`/projects/${id}/exports/ilcd-epd.xml`, `${id}-ilcd-epd.xml`, setIsGeneratingReport)
  }

  const handleExportOpenEpd = () => {
    void downloadExport(`/projects/${id}/exports/open-epd.json`, `${id}-open-epd.json`, setIsGeneratingReport)
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        <div className="flex items-center justify-between mb-xl">
          <div>
            <h1 className="text-heading-lg text-ink">EPD Generation</h1>
            <p className="text-body-md text-mute">
              Generate the final, verification-ready documentation package.
            </p>
          </div>
          <ButtonPrimary
            iconRight={faArrowRight}
            onClick={() => navigate(`/projects/${id}/publish`)}
            disabled={!previewUrl}
          >
            Next: Publish & Verify
          </ButtonPrimary>
        </div>

        {exportError && (
          <div className="mb-lg rounded-sm border border-error/30 bg-error/10 p-md text-body-sm text-error">
            {exportError}
          </div>
        )}

        <div className="flex flex-col tablet:flex-row gap-xxl">

          {/* Left Column: Actions */}
          <div className="flex-[1.2] flex flex-col gap-lg">

            {/* Pre-Export Checklist */}
            <div className="bg-white border border-hairline rounded-sm p-xl">
              <div className="flex items-center justify-between mb-md">
                <h2 className="text-heading-sm text-ink">Pre-Export Verification Checklist</h2>
                <span className={`text-body-sm font-bold font-mono ${completeness.scorePct === 100 ? 'text-green-600' : 'text-amber-600'}`}>
                  Score: {completeness.scorePct}% ({completeness.completedCount}/{completeness.totalCount})
                </span>
              </div>
              <ul className="flex flex-col gap-sm">
                {completeness.checks.map((item) => (
                  <li key={item.id} className="flex items-center justify-between gap-sm text-body-sm py-xs border-b border-hairline/50">
                    <div className="flex items-center gap-sm">
                      <div className={`w-[20px] h-[20px] rounded-full flex items-center justify-center text-xs ${item.isComplete ? 'bg-success/20 text-success' : 'bg-error/20 text-error font-bold'}`}>
                        {item.isComplete ? <FontAwesomeIcon icon={faCheck} size="xs" /> : '✕'}
                      </div>
                      <div>
                        <span className="font-semibold text-ink">{item.label}</span>
                        <p className="text-caption-sm text-mute">{item.helpText}</p>
                      </div>
                    </div>
                    {!item.isComplete && (
                      <Button
                        variant="ghost"
                        className="text-caption-sm text-primary underline hover:text-primary-dark"
                        onClick={() => navigate(`/projects/${id}/${item.stepPath}`)}
                      >
                        Edit →
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {/* Generation Cards */}
            <div className="grid grid-cols-1 mobile:grid-cols-2 gap-lg">

              {/* Public EPD */}
              <div className="bg-white border border-hairline rounded-sm p-xl flex flex-col">
                <div className="mb-sm">
                  <BadgeTag color="info">PUBLIC DOCUMENT</BadgeTag>
                </div>
                <h3 className="text-body-strong text-ink mb-xs">Public EPD</h3>
                <p className="text-body-sm text-mute flex-1 mb-xl">
                  Standardized EN 15942 format EPD. Includes product description, material composition tables, system boundary diagram, and full LCIA results matrices.
                </p>
                {epdUrl ? (
                  <div className="flex flex-col gap-sm">
                    <ButtonPrimary iconLeft={faDownload} fullWidth aria-label="Download EPD PDF" onClick={handleGenerateEPD}>
                      Download PDF
                    </ButtonPrimary>
                    <Button variant="ghost" fullWidth onClick={handleGenerateEPD}>
                      Regenerate
                    </Button>
                  </div>
                ) : (
                  <ButtonPrimary
                    iconLeft={isGeneratingEpd ? faSpinner : faFilePdf}
                    onClick={handleGenerateEPD}
                    disabled={isGeneratingEpd}
                    fullWidth
                  >
                    {isGeneratingEpd ? 'Generating...' : 'Generate Public EPD'}
                  </ButtonPrimary>
                )}
              </div>

              {/* Background Report */}
              <div className="bg-white border border-hairline rounded-sm p-xl flex flex-col">
                <div className="mb-sm">
                  <BadgeTag color="warning">CONFIDENTIAL</BadgeTag>
                </div>
                <h3 className="text-body-strong text-ink mb-xs">LCA Background Report</h3>
                <p className="text-body-sm text-mute flex-1 mb-xl">
                  Comprehensive technical background report detailing modeling choices, cut-off justifications, and primary vs. secondary data percentages.
                </p>
                <Button
                  variant="outline"
                  iconLeft={isGeneratingReport ? faSpinner : faFilePdf}
                  onClick={handleGenerateReport}
                  disabled={isGeneratingReport}
                  fullWidth
                >
                  {isGeneratingReport ? 'Generating...' : 'Generate Report PDF'}
                </Button>
              </div>

            </div>

            {/* Machine Readable Exports */}
            <div className="mt-md border-t border-hairline pt-xl">
              <h3 className="text-heading-sm text-ink mb-md">Machine-Readable Exports</h3>
              <div className="flex gap-md">
                <Button variant="outline" onClick={handleExportIlcd}>Export ILCD+EPD (XML)</Button>
                <Button variant="outline" onClick={handleExportOpenEpd}>Export OpenEPD (JSON)</Button>
              </div>
            </div>

          </div>

          {/* Right Column: PDF Preview */}
          <div className="flex-1 min-h-[600px] bg-surface-soft border border-hairline rounded-sm flex flex-col items-center justify-center p-md">
            {previewUrl ? (
              <iframe
                title="Public EPD Preview"
                src={previewUrl}
                className="w-full h-full min-h-[560px] bg-white border border-hairline"
              />
            ) : (
              <div className="text-center">
                <FontAwesomeIcon icon={faFilePdf} className="text-heading-xl text-mute mb-md opacity-50" />
                <p className="text-body-sm text-mute">Generate the Public EPD to preview it here.</p>
              </div>
            )}
          </div>

        </div>
      </div>
    </AppLayout>
  )
}
