/**
 * src/pages/LandingPage.tsx
 *
 * PRD §6.1 Marketing Landing Page
 *   - HeroCardDark
 *   - Features Section (4-up)
 *   - How-It-Works
 *   - Stat Callout Bar
 *   - Regulatory Compliance
 *   - CTAStripDark
 *   - FooterSection
 */

import { Link } from 'react-router-dom'
import { faNetworkWired, faShield, faDatabase, faCertificate } from '@fortawesome/free-solid-svg-icons'

import { PrimaryNav } from '@/components/organisms/PrimaryNav'
import { HeroCardDark } from '@/components/organisms/HeroCardDark'
import { CTAStripDark } from '@/components/organisms/CTAStripDark'
import { FooterSection } from '@/components/organisms/FooterSection'
import { FeatureCard } from '@/components/molecules/FeatureCard'
import { CalloutStat } from '@/components/molecules/CalloutStat'
import { ResourceCard } from '@/components/molecules/ResourceCard'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas flex flex-col">
      {/* Utility Bar (Optional for Marketing, but good for completeness) */}
      <div className="h-[32px] bg-ink border-b border-hairline-strong flex justify-end items-center px-lg">
        <div className="flex gap-md text-caption-xs text-mute">
          <Link to="/login" className="hover:text-white transition-colors">Sign In</Link>
          <Link to="/register" className="hover:text-white transition-colors text-white font-bold">Register</Link>
        </div>
      </div>
      
      <PrimaryNav />

      <main className="flex-1">
        {/* HERO CHAPTER */}
        <HeroCardDark />

        {/* FEATURES CHAPTER (White canvas) */}
        <section className="w-full max-w-content-max mx-auto px-hero-h py-section">
          <div className="text-center mb-xl">
            <h2 className="text-display-lg text-ink">Engineered for Accuracy</h2>
          </div>
          <div className="grid grid-cols-1 tablet:grid-cols-2 desktop-small:grid-cols-4 gap-lg">
            <FeatureCard 
              icon={faNetworkWired} 
              heading="Matrix-Powered LCA"
              body="Heijungs-Suh linear algebra engine solves complete supply chain networks in seconds."
            />
            <FeatureCard 
              icon={faShield} 
              heading="PCR Auto-Compliance"
              body="Product Category Rules automatically enforced. System boundaries set without manual lookup."
            />
            <FeatureCard 
              icon={faDatabase} 
              heading="Ecoinvent Integration"
              body="Sub-millisecond semantic search across the full ecoinvent v3.10 background database."
            />
            <FeatureCard 
              icon={faCertificate} 
              heading="Verification-Ready"
              body="PDF output meets EN 15942 formatting requirements. Zero blank cells, zero rejections."
            />
          </div>
        </section>

        {/* STATS CALLOUT BAR */}
        <section className="bg-surface-soft border-y border-hairline py-section">
          <div className="w-full max-w-content-max mx-auto px-hero-h">
            <div className="grid grid-cols-1 tablet:grid-cols-3 gap-lg">
              <CalloutStat eyebrow="THE WORKFLOW" value="6 steps" caption="From setup to published EPD" />
              <CalloutStat eyebrow="SUCCESS RATE" value="95%" caption="First-submission verification pass rate" />
              <CalloutStat eyebrow="SPEED" value="10× faster" caption="Versus manual LCA consultancy" />
            </div>
          </div>
        </section>

        {/* REGULATORY COMPLIANCE CHAPTER */}
        <section className="w-full max-w-content-max mx-auto px-hero-h py-section">
          <div className="text-center mb-xl">
            <h2 className="text-display-lg text-ink">Stay Ahead of Regulation</h2>
            <p className="text-body-md text-mute max-w-[600px] mx-auto mt-sm">
              EcoMetric automatically maps your product data to the latest European and global environmental directives.
            </p>
          </div>
          <div className="grid grid-cols-1 tablet:grid-cols-3 gap-lg">
            <ResourceCard 
              badge="REGULATION"
              badgeColor="info"
              heading="Construction Products Regulation (CPR)"
              body={<p className="mt-xs text-body-sm text-mute mb-md">Seamlessly generate EN 15804+A2 compliant declarations required for EU market access.</p>}
              metricValue="" metricLabel=""
              ctaLabel="Learn More"
            />
            
            <ResourceCard 
              badge="REGULATION"
              badgeColor="info"
              heading="Digital Product Passport (DPP)"
              body={<p className="mt-xs text-body-sm text-mute mb-md">Export machine-readable lifecycle data for ESPR compliance via the OpenEPD standard.</p>}
              metricValue="" metricLabel=""
              ctaLabel="Learn More"
            />

            <ResourceCard 
              badge="REGULATION"
              badgeColor="info"
              heading="Carbon Border Adjustment (CBAM)"
              body={<p className="mt-xs text-body-sm text-mute mb-md">Automatically calculate and report embedded Scope 1, 2, and 3 emissions per functional unit.</p>}
              metricValue="" metricLabel=""
              ctaLabel="Learn More"
            />
          </div>
        </section>

        {/* CTA CHAPTER (Dark) */}
        <CTAStripDark />
      </main>

      <FooterSection />
    </div>
  )
}
