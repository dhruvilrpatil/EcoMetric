/**
 * src/pages/PublishPage.tsx
 *
 * PRD §6.9 Step 6: Publish & Portfolio
 *   - Layout: AppLayout with SubNavStrip (Step 6 active)
 *   - Verifier Access Panel
 *   - Sibling EPD Generator
 *   - DPP Registry Push
 */

import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { faEnvelope, faCopy, faCloudArrowUp } from '@fortawesome/free-solid-svg-icons'

import { AppLayout } from '@/components/organisms/AppLayout'
import { ButtonPrimary, Button } from '@/components/atoms/Button'
import { TextInput } from '@/components/atoms/TextInput'
import { BadgeTag } from '@/components/atoms/BadgeTag'
import { NotificationCard } from '@/components/molecules/NotificationCard'

export default function PublishPage() {
  const { id } = useParams()

  const [verifierEmail, setVerifierEmail] = useState('')
  const [inviteSent, setInviteSent] = useState(false)

  const breadcrumbs = [
    { label: 'Projects', to: '/dashboard' },
    { label: 'Project Setup', to: `/projects/${id}/setup` },
    { label: 'Inventory', to: `/projects/${id}/inventory` },
    { label: 'Calculation', to: `/projects/${id}/calculate` },
    { label: 'Hotspots', to: `/projects/${id}/hotspots` },
    { label: 'Export', to: `/projects/${id}/export` },
    { label: 'Publish' },
  ]

  const projectNav = {
    projectId: id || 'new',
    currentStep: 7 as const,
    highestCompletedStep: 6 as const,
  }

  const handleSendInvite = (e: React.FormEvent) => {
    e.preventDefault()
    if (verifierEmail) {
      setInviteSent(true)
      setVerifierEmail('')
      setTimeout(() => setInviteSent(false), 3000)
    }
  }

  return (
    <AppLayout breadcrumbs={breadcrumbs} projectNav={projectNav}>
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        <div className="mb-xl">
          <h1 className="text-heading-lg text-ink">Publish & Verification</h1>
          <p className="text-body-md text-mute mt-xxs">
            Submit your EPD for third-party verification and distribute to registries.
          </p>
        </div>

        {inviteSent && (
          <div className="mb-xl">
            <NotificationCard variant="success" title="Invitation Sent">
              A secure, read-only link has been sent to the verifier.
            </NotificationCard>
          </div>
        )}

        <div className="grid grid-cols-1 tablet:grid-cols-2 gap-lg">

          {/* Verifier Access Panel */}
          <div className="bg-white border border-hairline rounded-sm p-xl flex flex-col h-full">
            <h2 className="text-heading-md text-ink mb-md">Share with Verifier</h2>
            <p className="text-body-sm text-mute mb-lg">
              Grant read-only access to all calculations down to the elementary exchange level for third-party auditing.
            </p>

            <form onSubmit={handleSendInvite} className="flex gap-md mb-xl mt-auto">
              <div className="flex-1">
                <TextInput
                  label="Verifier Email Address"
                  type="email"
                  placeholder="verifier@agency.com"
                  value={verifierEmail}
                  onChange={(e) => setVerifierEmail(e.target.value)}
                  required
                />
              </div>
              <div className="mt-[28px]">
                <ButtonPrimary type="submit" iconLeft={faEnvelope}>
                  Send Invitation
                </ButtonPrimary>
              </div>
            </form>

            <div className="border-t border-hairline pt-md">
              <h3 className="text-body-strong text-ink mb-sm">Active Sessions</h3>
              <div className="flex items-center justify-between py-xs">
                <span className="text-body-sm">j.smith@tuv.com</span>
                <BadgeTag color="success">ACTIVE</BadgeTag>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-lg h-full">
            {/* Sibling EPD Generator */}
            <div className="bg-white border border-hairline rounded-sm p-xl flex flex-col flex-1">
              <h2 className="text-heading-md text-ink mb-md">Scale to Other Facilities</h2>
              <p className="text-body-sm text-mute mb-lg flex-1">
                Clone this EPD's core topology for a product manufactured at a different facility. Only swap the localized electricity grid or transport datasets.
              </p>
              <div>
                <Button variant="outline" iconLeft={faCopy}>Create Sibling EPD</Button>
              </div>
            </div>

            {/* DPP Registry Push */}
            <div className="bg-white border border-hairline rounded-sm p-xl flex flex-col flex-1">
              <h2 className="text-heading-md text-ink mb-md">Push to Digital Product Passport</h2>
              <p className="text-body-sm text-mute mb-lg flex-1">
                Export verified EPD dataset to ESPR-compliant DPP registry in machine-readable format with GS1 Digital Link.
              </p>
              <div className="flex items-center justify-between">
                <Button variant="outline" iconLeft={faCloudArrowUp}>Connect DPP Registry</Button>
                <BadgeTag color="info">NOT CONNECTED</BadgeTag>
              </div>
            </div>
          </div>

        </div>
      </div>
    </AppLayout>
  )
}
