/**
 * src/components/index.ts — Barrel exports for all components
 *
 * Import from '@/components' for any component rather than deep paths.
 *
 * ── Atoms ──────────────────────────────────────────────────────────────────
 */

// Atoms
export { Button, ButtonPrimary, ButtonOutline, ButtonOutlineDark, ButtonGhost } from './atoms/Button'
export type { ButtonProps, ButtonVariant, ButtonSize } from './atoms/Button'

export { PillTab } from './atoms/PillTab'
export type { PillTabProps } from './atoms/PillTab'

export { BadgeTag } from './atoms/BadgeTag'
export type { BadgeTagProps, BadgeTagColor } from './atoms/BadgeTag'

export { CornerSquare } from './atoms/CornerSquare'
export type { CornerSquareProps, CornerSquarePosition, CornerSquareSize } from './atoms/CornerSquare'

export { TextInput } from './atoms/TextInput'
export type { TextInputProps } from './atoms/TextInput'

export { SearchInput } from './atoms/SearchInput'
export type { SearchInputProps } from './atoms/SearchInput'

// Molecules
export { CalloutStat } from './molecules/CalloutStat'
export type { CalloutStatProps } from './molecules/CalloutStat'

export { ProductCard } from './molecules/ProductCard'
export type { ProductCardProps } from './molecules/ProductCard'

export { FeatureCard } from './molecules/FeatureCard'
export type { FeatureCardProps } from './molecules/FeatureCard'

export { ResourceCard } from './molecules/ResourceCard'
export type { ResourceCardProps } from './molecules/ResourceCard'

export { NotificationCard } from './molecules/NotificationCard'
export type { NotificationCardProps, NotificationVariant } from './molecules/NotificationCard'

// Organisms
export { PrimaryNav, UtilityBar } from './organisms/PrimaryNav'
export type { PrimaryNavProps } from './organisms/PrimaryNav'

export { BreadcrumbBar } from './organisms/BreadcrumbBar'
export type { BreadcrumbBarProps, BreadcrumbItem } from './organisms/BreadcrumbBar'

export { SubNavStrip } from './organisms/SubNavStrip'
export type { SubNavStripProps } from './organisms/SubNavStrip'

export { HeroCardDark } from './organisms/HeroCardDark'
export type { HeroCardDarkProps } from './organisms/HeroCardDark'

export { CTAStripDark } from './organisms/CTAStripDark'
export type { CTAStripDarkProps } from './organisms/CTAStripDark'

export { FooterSection } from './organisms/FooterSection'

export { AppLayout } from './organisms/AppLayout'
export type { AppLayoutProps } from './organisms/AppLayout'
