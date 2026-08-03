/**
 * src/components/molecules/NotificationCard.tsx
 *
 * PRD CRITICAL RULE: "Computation errors surface as inline notification cards,
 * not browser alerts."
 *
 * Three semantic variants: error, warning, success
 * All render inline — never alert(), confirm(), or console.error to UI
 */

import type { ReactNode } from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import {
  faCircleXmark,
  faTriangleExclamation,
  faCircleCheck,
  faCircleInfo,
} from '@fortawesome/free-solid-svg-icons'

export type NotificationVariant = 'error' | 'warning' | 'success' | 'info'

export interface NotificationCardProps {
  variant: NotificationVariant
  title?: string
  children: ReactNode
  /** Optional action link/button rendered after body */
  action?: ReactNode
  className?: string
}

const VARIANT_CONFIG = {
  error: {
    containerClass: 'notification-error',
    iconClass:      'text-error',
    icon:           faCircleXmark,
    role:           'alert' as const,
  },
  warning: {
    containerClass: 'notification-warning',
    iconClass:      'text-warning',
    icon:           faTriangleExclamation,
    role:           'status' as const,
  },
  success: {
    containerClass: 'notification-success',
    iconClass:      'text-primary',
    icon:           faCircleCheck,
    role:           'status' as const,
  },
  info: {
    containerClass: 'notification-card border-link-blue bg-link-blue/5',
    iconClass:      'text-link-blue',
    icon:           faCircleInfo,
    role:           'status' as const,
  },
}

export function NotificationCard({
  variant,
  title,
  children,
  action,
  className = '',
}: NotificationCardProps) {
  const config = VARIANT_CONFIG[variant]

  return (
    <div
      role={config.role}
      className={`${config.containerClass} ${className}`}
    >
      {/* Icon */}
      <FontAwesomeIcon
        icon={config.icon}
        className={`${config.iconClass} flex-shrink-0 mt-xxs`}
        size="lg"
        aria-hidden="true"
      />

      {/* Content */}
      <div className="flex flex-col gap-xs flex-1">
        {title && (
          <p className="text-body-strong text-ink">{title}</p>
        )}
        <div className="text-body-sm text-body">{children}</div>
        {action && <div className="mt-xs">{action}</div>}
      </div>
    </div>
  )
}
