/**
 * src/components/organisms/BreadcrumbBar.tsx
 *
 * PRD §4.6 breadcrumb-bar: 48px height, surface-soft bg, body text, 1px bottom border
 * PRD §5.2: Shows current project path e.g. "PROJECTS > AQUAEDGE 19DV > INVENTORY"
 * Typography: caption-md uppercase
 */

import { Link } from 'react-router-dom'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faChevronRight } from '@fortawesome/free-solid-svg-icons'

export interface BreadcrumbItem {
  label: string
  to?: string  // If not provided, renders as current (non-linked) crumb
}

export interface BreadcrumbBarProps {
  items: BreadcrumbItem[]
}

export function BreadcrumbBar({ items }: BreadcrumbBarProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className="breadcrumb-bar"
    >
      <ol
        className="w-full max-w-content-max mx-auto flex items-center gap-xs list-none"
        style={{ margin: 0, padding: 0 }}
      >
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1
          return (
            <li
              key={idx}
              className="flex items-center gap-xs"
              aria-current={isLast ? 'page' : undefined}
            >
              {/* Separator */}
              {idx > 0 && (
                <FontAwesomeIcon
                  icon={faChevronRight}
                  className="text-mute"
                  size="xs"
                  aria-hidden="true"
                />
              )}

              {/* Crumb */}
              {!isLast && item.to ? (
                <Link
                  to={item.to}
                  className="text-caption-md uppercase text-mute hover:text-ink transition-colors"
                >
                  {item.label}
                </Link>
              ) : (
                <span
                  className={`text-caption-md uppercase ${
                    isLast ? 'text-ink font-bold' : 'text-mute'
                  }`}
                >
                  {item.label}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
