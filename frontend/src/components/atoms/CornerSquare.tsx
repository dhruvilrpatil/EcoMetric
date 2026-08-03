/**
 * src/components/atoms/CornerSquare.tsx
 *
 * PRD §4.6 — Decorative Corner Square
 *   Size:       12×12px (16×16px on hero callouts)
 *   Color:      #76b900 (--color-primary)
 *   Radius:     0px (never rounded)
 *   Position:   Anchored to top-left OR bottom-right — NEVER BOTH
 *
 * Usage:
 *   <div className="relative card p-xl">
 *     <CornerSquare position="top-left" />
 *     … card content …
 *   </div>
 */

export type CornerSquarePosition = 'top-left' | 'bottom-right'
export type CornerSquareSize = 'sm' | 'lg'

export interface CornerSquareProps {
  /** top-left OR bottom-right — never both on same card */
  position: CornerSquarePosition
  /** sm = 12×12px (default), lg = 16×16px (hero callouts) */
  size?: CornerSquareSize
  className?: string
}

const POSITION_CLASS: Record<CornerSquarePosition, string> = {
  'top-left':     'corner-sq-tl',
  'bottom-right': 'corner-sq-br',
}

const SIZE_CLASS: Record<CornerSquareSize, string> = {
  sm: 'corner-sq',
  lg: 'corner-sq-lg',
}

export function CornerSquare({
  position,
  size = 'sm',
  className = '',
}: CornerSquareProps) {
  return (
    <span
      aria-hidden="true"
      className={`${SIZE_CLASS[size]} ${POSITION_CLASS[position]} ${className}`.trim()}
    />
  )
}
