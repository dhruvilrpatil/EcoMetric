/**
 * src/components/organisms/PrimaryNav.tsx
 *
 * PRD §4.6 Navigation Chrome:
 *   utility-bar:  32px, black bg, white text — WCAG read-only strip
 *   primary-nav:  64px, black bg, white text, sticky, box-shadow: 0 0 5px rgba(0,0,0,0.3)
 *
 * PRD §5.2 Primary Navigation (Authenticated):
 *   Left:   Product wordmark / logo
 *   Center: Projects · Portfolio · Resources · Settings
 *   Right:  Search icon · User avatar dropdown · "+ New Declaration" (button-primary)
 *
 * PRD §4.8: Hamburger drawer on tablet breakpoint (768px)
 * PRD RULE: button-primary appears ONCE per fold — "+ New Declaration" is the only primary CTA
 */

import { useState, useRef, useEffect } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faMagnifyingGlass,
  faBars,
  faXmark,
  faChevronDown,
  faGear,
  faArrowRightFromBracket,
} from '@fortawesome/free-solid-svg-icons'
import { signOut } from 'firebase/auth'
import { auth } from '@/lib/firebase'
import { useAppSelector } from '@/store'
import { ButtonPrimary } from '@/components/atoms/Button'

// ── Utility Bar ───────────────────────────────────────────────────────────────
interface UtilityBarProps {
  /** Text shown on left — used for VERIFIER MODE badge in §6.10 */
  leftText?: string
  /** Text shown on right */
  rightText?: string
}

export function UtilityBar({ leftText, rightText }: UtilityBarProps) {
  return (
    <div className="utility-bar">
      <div className="w-content-max mx-auto flex items-center justify-between w-full">
        <span className="text-utility-xs uppercase text-on-dark-mute">
          {leftText ?? 'EcoMetric — Automated EPD Platform'}
        </span>
        {rightText && (
          <span className="text-utility-xs uppercase text-on-dark-mute">
            {rightText}
          </span>
        )}
      </div>
    </div>
  )
}

// ── Nav links ─────────────────────────────────────────────────────────────────
const NAV_LINKS = [
  { label: 'Projects',  to: '/dashboard' },
  { label: 'Portfolio', to: '/portfolio' },
  { label: 'Resources', to: '/#resources' },
  { label: 'Settings',  to: '/settings' },
]

// ── User avatar dropdown ──────────────────────────────────────────────────────
function UserMenu({ displayName }: { displayName: string }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function handleSignOut() {
    await signOut(auth)
    navigate('/login')
  }

  const initials = displayName
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <div ref={ref} className="relative">
      <button
        id="user-menu-button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="true"
        aria-label={`User menu for ${displayName}`}
        className="flex items-center gap-sm text-on-dark hover:text-on-dark-mute transition-colors duration-fast min-h-touch min-w-touch"
      >
        {/* Avatar circle — rounded-full per PRD (ONLY exception to 2px rule) */}
        <span className="w-[32px] h-[32px] rounded-full bg-primary text-on-primary text-caption-xs font-bold flex items-center justify-center">
          {initials}
        </span>
        <FontAwesomeIcon icon={faChevronDown} size="xs" />
      </button>

      {/* Dropdown panel */}
      {open && (
        <div
          role="menu"
          aria-labelledby="user-menu-button"
          className="absolute right-0 top-full mt-sm w-[200px] bg-surface-elevated border border-hairline-strong rounded-sm z-modal"
        >
          <div className="px-xl py-md border-b border-hairline-strong">
            <p className="text-caption-xs uppercase text-on-dark-mute">Signed in as</p>
            <p className="text-body-sm text-on-dark truncate">{displayName}</p>
          </div>

          <nav className="py-xs">
            <Link
              to="/settings"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="flex items-center gap-md px-xl py-sm text-body-sm text-on-dark-mute hover:text-on-dark hover:bg-surface-elevated transition-colors min-h-touch"
            >
              <FontAwesomeIcon icon={faGear} size="sm" aria-hidden="true" />
              Account Settings
            </Link>
            <button
              role="menuitem"
              onClick={handleSignOut}
              className="flex items-center gap-md px-xl py-sm text-body-sm text-on-dark-mute hover:text-on-dark hover:bg-surface-elevated transition-colors w-full text-left min-h-touch"
            >
              <FontAwesomeIcon icon={faArrowRightFromBracket} size="sm" aria-hidden="true" />
              Sign Out
            </button>
          </nav>
        </div>
      )}
    </div>
  )
}

// ── Mobile Drawer ─────────────────────────────────────────────────────────────
function MobileDrawer({
  open,
  onClose,
}: {
  open: boolean
  onClose: () => void
}) {
  // Lock body scroll when drawer is open
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-overlay"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Drawer panel */}
      <div
        role="dialog"
        aria-label="Navigation menu"
        aria-modal="true"
        className="fixed top-0 left-0 bottom-0 w-[280px] bg-surface-dark z-modal flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-xl h-primary-nav border-b border-hairline-strong">
          <Link to="/" onClick={onClose} className="text-heading-sm font-bold text-on-dark">
            EcoMetric
          </Link>
          <button
            onClick={onClose}
            aria-label="Close navigation menu"
            className="text-on-dark min-h-touch min-w-touch flex items-center justify-center"
          >
            <FontAwesomeIcon icon={faXmark} />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-xl py-xl flex flex-col gap-sm">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              onClick={onClose}
              className={({ isActive }) =>
                `text-body-strong py-md px-lg rounded-sm transition-colors min-h-touch flex items-center ${
                  isActive ? 'bg-primary text-on-primary' : 'text-on-dark-mute hover:text-on-dark'
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* CTA */}
        <div className="px-xl py-xl border-t border-hairline-strong">
          <Link to="/projects/new" onClick={onClose}>
            <ButtonPrimary fullWidth>+ New Declaration</ButtonPrimary>
          </Link>
        </div>
      </div>
    </>
  )
}

// ── PrimaryNav (main export) ──────────────────────────────────────────────────
export interface PrimaryNavProps {
  /** Shown in utility bar for verifier mode */
  utilityBarText?: string
}

export function PrimaryNav({ utilityBarText }: PrimaryNavProps) {
  const { user } = useAppSelector((s) => s.auth)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <>
      {/* Utility bar */}
      <UtilityBar leftText={utilityBarText} />

      {/* Primary nav */}
      <header className="primary-nav">
        <div className="w-full max-w-content-max mx-auto flex items-center justify-between gap-xl">

          {/* Wordmark */}
          <Link
            to={user ? '/dashboard' : '/'}
            aria-label="EcoMetric home"
            className="text-heading-sm font-bold text-on-dark flex-shrink-0 min-h-touch flex items-center"
          >
            Quick<span className="text-primary">LCA</span>
          </Link>

          {/* Desktop center nav — hidden on tablet */}
          <nav
            aria-label="Main navigation"
            className="hidden desktop-small:flex items-center gap-sm"
          >
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `text-body-strong px-md py-sm rounded-sm transition-colors min-h-touch flex items-center ${
                    isActive
                      ? 'text-primary'
                      : 'text-on-dark-mute hover:text-on-dark'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>

          {/* Right side controls */}
          <div className="flex items-center gap-md">
            {/* Search icon */}
            <button
              onClick={() => setSearchOpen((o) => !o)}
              aria-label="Open search"
              aria-expanded={searchOpen}
              className="text-on-dark-mute hover:text-on-dark transition-colors min-h-touch min-w-touch flex items-center justify-center"
            >
              <FontAwesomeIcon icon={faMagnifyingGlass} />
            </button>

            {/* User menu (authenticated) */}
            {user && (
              <UserMenu displayName={user.display_name || user.email} />
            )}

            {/* + New Declaration — button-primary, ONCE per fold */}
            <div className="hidden desktop-small:block">
              <Link to="/projects/new">
                <ButtonPrimary size="sm" aria-label="Create new EPD declaration">
                  + New Declaration
                </ButtonPrimary>
              </Link>
            </div>

            {/* Hamburger — tablet and below */}
            <button
              onClick={() => setDrawerOpen(true)}
              aria-label="Open navigation menu"
              aria-expanded={drawerOpen}
              className="desktop-small:hidden text-on-dark min-h-touch min-w-touch flex items-center justify-center"
            >
              <FontAwesomeIcon icon={faBars} />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer */}
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </>
  )
}
