/**
 * src/components/organisms/FooterSection.tsx
 *
 * PRD §6.1 Footer:
 *   5-column link grid: Product · Resources · Standards · Company · Support
 *   Social icons row (Font Awesome brand icons) — rounded-full per PRD (ONLY exception)
 *   Legal fine-print in utility-xs uppercase
 *   Background: surface-dark (black)
 *   Border top: 1px hairline-strong
 *
 * PRD §4.8 responsive: Footer collapses to accordion on mobile
 */

import { Link } from 'react-router-dom'
import { useState } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faLinkedin,
  faXTwitter,
  faGithub,
} from '@fortawesome/free-brands-svg-icons'
import { faChevronDown } from '@fortawesome/free-solid-svg-icons'

// ── Footer link data ──────────────────────────────────────────────────────────
const COLUMNS = [
  {
    heading: 'Product',
    links: [
      { label: 'Dashboard',       to: '/dashboard' },
      { label: 'New Declaration', to: '/projects/new' },
      { label: 'Portfolio',       to: '/portfolio' },
      { label: 'Settings',        to: '/settings' },
    ],
  },
  {
    heading: 'Resources',
    links: [
      { label: 'Documentation',   to: '/#docs' },
      { label: 'API Reference',   to: '/#api' },
      { label: 'Changelog',       to: '/#changelog' },
      { label: 'Status',          to: '/#status' },
    ],
  },
  {
    heading: 'Standards',
    links: [
      { label: 'EN 15804+A2',     to: '/#en15804' },
      { label: 'ISO 14025',       to: '/#iso14025' },
      { label: 'ISO 21930',       to: '/#iso21930' },
      { label: 'ESPR / DPP',      to: '/#espr' },
    ],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About',           to: '/#about' },
      { label: 'Blog',            to: '/#blog' },
      { label: 'Careers',         to: '/#careers' },
      { label: 'Contact',         to: '/#contact' },
    ],
  },
  {
    heading: 'Support',
    links: [
      { label: 'Help Center',     to: '/#help' },
      { label: 'Verifier Guide',  to: '/#verifier' },
      { label: 'Privacy Policy',  to: '/#privacy' },
      { label: 'Terms of Use',    to: '/#terms' },
    ],
  },
]

const SOCIAL_LINKS = [
  { icon: faLinkedin, label: 'LinkedIn',  href: 'https://linkedin.com' },
  { icon: faXTwitter, label: 'X/Twitter', href: 'https://x.com' },
  { icon: faGithub,   label: 'GitHub',    href: 'https://github.com' },
]

// ── Mobile accordion column ───────────────────────────────────────────────────
function AccordionColumn({
  heading,
  links,
}: {
  heading: string
  links: Array<{ label: string; to: string }>
}) {
  const [open, setOpen] = useState(false)

  return (
    <div className="border-b border-hairline-strong">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="w-full flex items-center justify-between py-md text-body-strong text-on-dark min-h-touch"
      >
        {heading}
        <FontAwesomeIcon
          icon={faChevronDown}
          className={`transition-transform duration-fast ${open ? 'rotate-180' : ''}`}
          size="xs"
          aria-hidden="true"
        />
      </button>

      {open && (
        <ul className="pb-md flex flex-col gap-sm list-none" style={{ padding: '0 0 12px 0', margin: 0 }}>
          {links.map((link) => (
            <li key={link.to}>
              <Link
                to={link.to}
                className="text-body-sm text-on-dark-mute hover:text-on-dark transition-colors min-h-touch flex items-center"
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// ── FooterSection ─────────────────────────────────────────────────────────────
export function FooterSection() {
  const currentYear = new Date().getFullYear()

  return (
    <footer
      className="bg-surface-dark border-t border-hairline-strong"
      aria-label="Site footer"
    >
      <div className="w-full max-w-content-max mx-auto px-hero-h py-section">

        {/* Desktop: 5-column grid — hidden on mobile */}
        <div className="hidden tablet:grid grid-cols-5 gap-xxl mb-section">
          {/* Wordmark column */}
          <div className="col-span-1 flex flex-col gap-lg">
            <Link to="/" aria-label="EcoMetric home" className="text-heading-sm font-bold text-on-dark">
              Quick<span className="text-primary">LCA</span>
            </Link>
            <p className="text-body-sm text-on-dark-mute">
              Automated EPD & Life Cycle Assessment Platform. EN 15804+A2 compliant.
            </p>
          </div>

          {/* Link columns */}
          {COLUMNS.map((col) => (
            <div key={col.heading} className="flex flex-col gap-lg">
              <h3 className="text-body-strong text-on-dark">{col.heading}</h3>
              <ul className="flex flex-col gap-sm list-none" style={{ margin: 0, padding: 0 }}>
                {col.links.map((link) => (
                  <li key={link.to}>
                    <Link
                      to={link.to}
                      className="text-body-sm text-on-dark-mute hover:text-on-dark transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Mobile: accordion columns */}
        <div className="tablet:hidden mb-xl">
          {COLUMNS.map((col) => (
            <AccordionColumn key={col.heading} heading={col.heading} links={col.links} />
          ))}
        </div>

        {/* Bottom bar: social icons + legal */}
        <div className="flex flex-col tablet:flex-row items-center justify-between gap-lg pt-xl border-t border-hairline-strong">

          {/* Social icons — rounded-full per PRD (ONLY exception to 2px radius) */}
          <div className="flex items-center gap-md" aria-label="Social media links">
            {SOCIAL_LINKS.map((social) => (
              <a
                key={social.label}
                href={social.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.label}
                className="w-[36px] h-[36px] rounded-full bg-surface-elevated border border-hairline-strong flex items-center justify-center text-on-dark-mute hover:text-on-dark hover:border-primary transition-all duration-fast min-h-touch min-w-touch"
              >
                <FontAwesomeIcon icon={social.icon} size="sm" aria-hidden="true" />
              </a>
            ))}
          </div>

          {/* Legal text — utility-xs uppercase per PRD */}
          <p className="text-utility-xs uppercase text-on-dark-mute text-center tablet:text-right">
            © {currentYear} EcoMetric. All rights reserved.
            {' '}EN 15804+A2 · ISO 14025 · ISO 14040/14044
          </p>
        </div>
      </div>
    </footer>
  )
}
