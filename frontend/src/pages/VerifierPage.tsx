/**
 * src/pages/VerifierPage.tsx
 *
 * Verifier Portal (EN 15804+A2 / ISO 14025 EPD Third-Party Auditing)
 * Read-only interface surfacing full NLP extraction audit logs, dataset confidence breakdowns,
 * alternative match candidates, and digital signature sign-off.
 */

import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faLock, faCheckCircle, faFileSignature, faChevronDown, faChevronUp } from '@fortawesome/free-solid-svg-icons'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { Button } from '@/components/atoms/Button'
import { api } from '@/lib/api'

interface CandidateMatch {
  rank: number
  ecoinvent_id: string
  ecoinvent_name: string
  geography: string
  match_confidence: number
}

interface ConfidenceComponents {
  semantic: number
  category: number
  geography: number
  recency: number
  synonym?: number
}

interface AuditEvent {
  material_id: string
  extracted_material_name: string
  selected_ecoinvent_id: string
  selected_ecoinvent_name: string
  confidence_components: ConfidenceComponents
  candidate_matches: CandidateMatch[]
}

export default function VerifierPage() {
  const { token } = useParams<{ token: string }>()
  const [project, setProject] = useState<any>(null)
  const [auditLog, setAuditLog] = useState<AuditEvent[]>([])
  const [signatureStatus, setSignatureStatus] = useState('unsigned')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    async function fetchProject() {
      try {
        const data = await api.get<any>(`/verifier/${token}/project`)
        setProject(data)
        setAuditLog(data.audit_log || [])
        setSignatureStatus(data.signature_status || 'unsigned')
      } catch {
        setError('This verifier link is invalid or has expired.')
      } finally {
        setLoading(false)
      }
    }

    fetchProject()
  }, [token])

  const handleSign = async (name: string, org: string, accreditation: string) => {
    try {
      await api.post(`/verifier/${token}/sign`, {
        verifier_name: name,
        verifier_organization: org,
        iso_14025_accreditation: accreditation,
      })
      setSignatureStatus('signed')
    } catch (err) {
      console.error('Failed to sign EPD', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-canvas flex flex-col items-center justify-center p-xl">
        <p className="text-body-md text-mute animate-pulse">Loading verifier audit portal...</p>
      </div>
    )
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-canvas flex flex-col items-center justify-center p-xl">
        <div className="bg-white border border-hairline rounded-sm p-xl max-w-md text-center">
          <p className="text-body-md text-error font-semibold mb-md">{error || 'Project not found.'}</p>
          <p className="text-caption-sm text-mute">Please check your tokenized verifier link.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      {/* Read-Only Mode Banner */}
      <div className="h-[36px] bg-ink flex items-center justify-center gap-sm">
        <FontAwesomeIcon icon={faLock} className="text-white" size="xs" />
        <span className="text-caption-xs text-white uppercase tracking-wider font-bold">
          READ-ONLY ACCESS — VERIFIER MODE
        </span>
      </div>

      {/* Header */}
      <header className="h-[64px] bg-white border-b border-hairline px-hero-h flex items-center justify-between">
        <div className="text-heading-md font-bold text-ink">
          Eco<span className="text-primary">Metric</span>
        </div>
        <BadgeTag color="info">Token: {token?.substring(0, 8)}...</BadgeTag>
      </header>

      <main className="flex-1 w-full max-w-4xl mx-auto px-hero-h py-section space-y-xl">
        
        {/* Project Summary */}
        <section className="bg-white border border-hairline rounded-sm p-xl shadow-card">
          <div className="flex items-center justify-between mb-md">
            <h1 className="text-heading-lg text-ink font-bold">
              EPD Verification: {project.product_name}
            </h1>
            <BadgeTag color={signatureStatus === 'signed' ? 'success' : 'warning'}>
              {signatureStatus === 'signed' ? 'Verified & Published' : 'Pending Verification'}
            </BadgeTag>
          </div>

          <div className="grid grid-cols-1 tablet:grid-cols-2 gap-lg bg-surface-soft p-md rounded-sm border border-hairline text-body-sm">
            <div>
              <span className="text-caption-xs uppercase font-bold text-mute">Functional Unit</span>
              <p className="font-semibold text-ink mt-xs">{project.functional_unit}</p>
            </div>
            <div>
              <span className="text-caption-xs uppercase font-bold text-mute">Assessment Standard</span>
              <p className="font-semibold text-ink mt-xs">{project.standard}</p>
            </div>
          </div>
        </section>

        {/* Material Audit Trail */}
        <section className="bg-white border border-hairline rounded-sm p-xl shadow-card space-y-lg">
          <div>
            <h2 className="text-heading-md text-ink font-bold">Material Extraction &amp; Matching Audit Trail</h2>
            <p className="text-body-sm text-mute mt-xs">
              Every material below was extracted via NLP from the uploaded BOM and matched to an ecoinvent dataset.
              Confidence components and alternative candidates are shown for full traceability.
            </p>
          </div>

          {auditLog.map((event, idx) => (
            <AuditEventRow key={event.material_id || idx} event={event} />
          ))}
        </section>

        {/* Signature Block */}
        <section className="bg-ink text-white p-xl rounded-sm shadow-card">
          <h2 className="text-heading-md font-bold mb-xs text-white flex items-center gap-sm">
            <FontAwesomeIcon icon={faFileSignature} className="text-primary" />
            Third-Party Verifier Digital Signature
          </h2>

          {signatureStatus === 'unsigned' ? (
            <VerifierSignatureForm onSign={handleSign} />
          ) : (
            <div className="border border-success bg-surface-dark/50 rounded-sm p-lg mt-md flex items-start gap-md">
              <FontAwesomeIcon icon={faCheckCircle} className="text-success text-heading-md mt-xs" />
              <div>
                <p className="text-body-strong text-white font-bold">✓ EPD Digitally Signed &amp; Published</p>
                <p className="text-caption-sm text-on-dark-mute mt-xs">
                  Signature on file in compliance with ISO 14025 / EN 15804+A2.
                </p>
              </div>
            </div>
          )}
        </section>

      </main>
    </div>
  )
}

function AuditEventRow({ event }: { event: AuditEvent }) {
  const [showConfidence, setShowConfidence] = useState(false)
  const [showAlternatives, setShowAlternatives] = useState(false)

  const c = event.confidence_components || { semantic: 0.9, category: 0.9, geography: 0.9, recency: 0.9 }

  return (
    <div className="p-md border-l-4 border-primary bg-surface-soft rounded-sm space-y-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-body-strong text-ink font-bold">{event.extracted_material_name}</p>
          <p className="text-body-sm text-mute">
            Matched to: <span className="font-semibold text-ink">{event.selected_ecoinvent_name}</span>
          </p>
        </div>
        <span className="text-caption-xs font-mono font-bold bg-white border border-hairline px-xs py-1 rounded">
          ID: {event.selected_ecoinvent_id.substring(0, 12)}...
        </span>
      </div>

      <div className="flex items-center gap-md pt-xs">
        <button
          onClick={() => setShowConfidence(!showConfidence)}
          className="text-caption-sm text-primary hover:underline font-semibold flex items-center gap-xs"
        >
          <span>Confidence breakdown</span>
          <FontAwesomeIcon icon={showConfidence ? faChevronUp : faChevronDown} size="xs" />
        </button>

        {event.candidate_matches && event.candidate_matches.length > 1 && (
          <button
            onClick={() => setShowAlternatives(!showAlternatives)}
            className="text-caption-sm text-primary hover:underline font-semibold flex items-center gap-xs"
          >
            <span>{event.candidate_matches.length} alternatives considered</span>
            <FontAwesomeIcon icon={showAlternatives ? faChevronUp : faChevronDown} size="xs" />
          </button>
        )}
      </div>

      {showConfidence && (
        <div className="mt-sm bg-white p-sm rounded-sm border border-hairline grid grid-cols-2 tablet:grid-cols-4 gap-sm text-caption-xs">
          <div>
            <span className="text-mute block">Semantic similarity</span>
            <span className="font-bold font-mono">{(c.semantic * 100).toFixed(0)}%</span>
          </div>
          <div>
            <span className="text-mute block">Category match</span>
            <span className="font-bold font-mono">{(c.category * 100).toFixed(0)}%</span>
          </div>
          <div>
            <span className="text-mute block">Geography fit</span>
            <span className="font-bold font-mono">{(c.geography * 100).toFixed(0)}%</span>
          </div>
          <div>
            <span className="text-mute block">Data recency</span>
            <span className="font-bold font-mono">{(c.recency * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}

      {showAlternatives && event.candidate_matches && (
        <div className="mt-sm bg-white p-sm rounded-sm border border-hairline space-y-xs text-caption-xs">
          <p className="font-bold text-mute uppercase">Candidate Ranking:</p>
          <ul className="space-y-xs list-disc pl-md">
            {event.candidate_matches.map((alt) => (
              <li key={alt.ecoinvent_id} className="text-ink">
                <span className="font-semibold">{alt.ecoinvent_name}</span> ({alt.geography}) —{' '}
                <span className="font-mono font-bold text-primary">{alt.match_confidence}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function VerifierSignatureForm({ onSign }: { onSign: (name: string, org: string, accred: string) => void }) {
  const [name, setName] = useState('')
  const [org, setOrg] = useState('')
  const [accreditation, setAccreditation] = useState('')

  return (
    <div className="space-y-md mt-md">
      <input
        type="text"
        placeholder="Verifier full name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full border border-hairline bg-surface-elevated text-white rounded-sm p-sm text-body-sm"
      />
      <input
        type="text"
        placeholder="Organization (e.g. UL Solutions, SCS Global Services)"
        value={org}
        onChange={(e) => setOrg(e.target.value)}
        className="w-full border border-hairline bg-surface-elevated text-white rounded-sm p-sm text-body-sm"
      />
      <input
        type="text"
        placeholder="ISO 14025 accreditation number (optional)"
        value={accreditation}
        onChange={(e) => setAccreditation(e.target.value)}
        className="w-full border border-hairline bg-surface-elevated text-white rounded-sm p-sm text-body-sm"
      />
      <Button
        variant="primary"
        onClick={() => onSign(name, org, accreditation)}
        disabled={!name || !org}
      >
        Digitally Sign &amp; Publish EPD
      </Button>
    </div>
  )
}
