/**
 * src/components/organisms/HeroCardDark.tsx
 *
 * PRD §6.1 Hero Chapter:
 *   Background: surface-dark (black) with SVG supply chain visualization
 *   Headline: display-xl — "Audit-Ready EPDs. Generated Automatically."
 *   Subheadline: heading-lg — long-form intro text
 *   Primary CTA: button-primary — "Start Your First EPD"
 *   Secondary CTA: button-outline-on-dark — "See How It Works"
 *   Corner square: 16×16px at bottom-right of hero copy block
 *   Vertical padding: 80px (hero-v token)
 *
 * PRD RULE: button-primary appears ONCE per fold — hero has one primary CTA only.
 *
 * SVG visualization is programmatically generated (no stock images per PRD §Phase 8).
 */

import { Link } from 'react-router-dom'
import { CornerSquare } from '@/components/atoms/CornerSquare'
import { ButtonPrimary, ButtonOutlineDark } from '@/components/atoms/Button'
import type { ReactNode } from 'react'

// ── Programmatic Supply Chain SVG ─────────────────────────────────────────────
function SupplyChainSVG() {
  // Nodes: 6 circles representing stages of supply chain
  const nodes = [
    { id: 'raw',   x: 80,  y: 160, label: 'Raw\nMaterials' },
    { id: 'mfg',   x: 240, y: 80,  label: 'Manufacturing' },
    { id: 'trans', x: 400, y: 160, label: 'Transport' },
    { id: 'use',   x: 240, y: 240, label: 'Use' },
    { id: 'eol',   x: 80,  y: 320, label: 'End of\nLife' },
    { id: 'epd',   x: 400, y: 320, label: 'EPD\nOutput' },
  ]

  const edges = [
    ['raw', 'mfg'], ['mfg', 'trans'], ['trans', 'use'],
    ['use', 'eol'], ['eol', 'epd'],   ['raw', 'eol'],
    ['mfg', 'use'], ['trans', 'epd'],
  ]

  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]))

  return (
    <svg
      viewBox="0 0 480 400"
      width="480"
      height="400"
      aria-label="Supply chain network visualization"
      role="img"
      className="w-full max-w-[480px] opacity-40"
    >
      <defs>
        <marker
          id="arrowhead"
          markerWidth="6" markerHeight="4"
          refX="6" refY="2"
          orient="auto"
        >
          <polygon points="0 0, 6 2, 0 4" fill="#76b900" />
        </marker>
      </defs>

      {/* Edges */}
      {edges.map(([from, to], idx) => {
        const f = nodeMap[from]
        const t = nodeMap[to]
        if (!f || !t) return null
        return (
          <line
            key={idx}
            x1={f.x} y1={f.y}
            x2={t.x} y2={t.y}
            stroke="#5e5e5e"
            strokeWidth="1.5"
            strokeDasharray="4 3"
            markerEnd="url(#arrowhead)"
          />
        )
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <g key={node.id}>
          <circle
            cx={node.x} cy={node.y} r="28"
            fill="#1a1a1a"
            stroke="#76b900"
            strokeWidth="1.5"
          />
          {node.label.split('\n').map((line, i) => (
            <text
              key={i}
              x={node.x}
              y={node.y + (node.label.includes('\n') ? -5 + i * 12 : 4)}
              textAnchor="middle"
              fill="#ffffff"
              fontSize="9"
              fontFamily="Inter, Arial, sans-serif"
              fontWeight="700"
            >
              {line}
            </text>
          ))}
        </g>
      ))}
    </svg>
  )
}

// ── HeroCardDark ──────────────────────────────────────────────────────────────
export interface HeroCardDarkProps {
  headline?: string
  subheadline?: string
  primaryCta?: { label: string; to: string }
  secondaryCta?: { label: string; to: string; onClick?: () => void }
  children?: ReactNode
}

export function HeroCardDark({
  headline = 'Audit-Ready EPDs. Generated Automatically.',
  subheadline = 'From bill of materials to verified Environmental Product Declaration in a single session.',
  primaryCta = { label: 'Start Your First EPD', to: '/register' },
  secondaryCta = { label: 'See How It Works', to: '/#how-it-works' },
  children,
}: HeroCardDarkProps) {
  return (
    <section className="section-dark w-full overflow-hidden" aria-label="Hero">
      <div className="w-full max-w-content-max mx-auto">
        <div className="flex flex-col desktop-small:flex-row items-center gap-xxl">

          {/* Copy block — left/center */}
          <div className="flex-1 relative">
            {/* Corner square — 16px (lg) at bottom-right per PRD §6.1 */}
            <CornerSquare position="bottom-right" size="lg" />

            <div className="flex flex-col gap-xl">
              {/* Eyebrow */}
              <p className="text-caption-md uppercase text-primary tracking-caption">
                Life Cycle Assessment Platform
              </p>

              {/* Headline — display-xl (scales to 32px on mobile-narrow per PRD §4.8) */}
              <h1 className="text-display-xl-mobile desktop-small:text-display-xl text-on-dark leading-tight">
                {headline}
              </h1>

              {/* Subheadline — heading-lg */}
              <p className="text-heading-lg text-on-dark-mute max-w-[540px]">
                {subheadline}
              </p>

              {/* CTA row — one primary, one outline-dark per PRD fold rule */}
              <div className="flex flex-col mobile:flex-row gap-lg">
                <Link to={primaryCta.to}>
                  <ButtonPrimary size="lg" aria-label={primaryCta.label}>
                    {primaryCta.label}
                  </ButtonPrimary>
                </Link>
                <Link to={secondaryCta.to}>
                  <ButtonOutlineDark size="lg" aria-label={secondaryCta.label}>
                    {secondaryCta.label}
                  </ButtonOutlineDark>
                </Link>
              </div>

              {/* Optional slot */}
              {children}
            </div>
          </div>

          {/* SVG visualization — right side */}
          <div
            className="hidden desktop-small:flex flex-1 items-center justify-center"
            aria-hidden="true"
          >
            <SupplyChainSVG />
          </div>
        </div>
      </div>
    </section>
  )
}
