/**
 * src/components/organisms/CTAStripDark.tsx
 *
 * PRD §6.1 Dark CTA Strip (cta-strip-dark):
 *   Background: surface-dark (black)
 *   Headline: heading-xl
 *   Button: button-primary (single CTA per fold rule)
 *   No corner squares on CTA strip — it's a full-bleed band
 *   Alternates with white sections per PRD §4.7 page rhythm
 */

import { Link } from 'react-router-dom'
import { ButtonPrimary } from '@/components/atoms/Button'

export interface CTAStripDarkProps {
  headline?: string
  body?: string
  cta?: { label: string; to: string }
}

export function CTAStripDark({
  headline = 'Ready to Generate Your First EPD?',
  body,
  cta = { label: 'Get Started Free', to: '/register' },
}: CTAStripDarkProps) {
  return (
    <section
      className="section-dark text-center"
      aria-label="Call to action"
    >
      <div className="w-full max-w-content-max mx-auto flex flex-col items-center gap-xl">
        {/* Eyebrow */}
        <p className="text-caption-md uppercase text-primary tracking-caption">
          Get Started Today
        </p>

        {/* Headline — heading-xl per PRD */}
        <h2 className="text-heading-xl text-on-dark max-w-[600px]">
          {headline}
        </h2>

        {/* Optional body */}
        {body && (
          <p className="text-body-md text-on-dark-mute max-w-[480px]">
            {body}
          </p>
        )}

        {/* Single button-primary — once per fold */}
        <Link to={cta.to}>
          <ButtonPrimary size="lg" aria-label={cta.label}>
            {cta.label}
          </ButtonPrimary>
        </Link>
      </div>
    </section>
  )
}
