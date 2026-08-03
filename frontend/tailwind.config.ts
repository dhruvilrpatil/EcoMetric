import type { Config } from 'tailwindcss'

/**
 * EcoMetric Design System — Tailwind Configuration
 *
 * All tokens are sourced directly from PRD Section 4.
 * CRITICAL RULES:
 *  - All spacing must reference named tokens — no arbitrary values.
 *  - Border radius max is rounded-sm (2px) except avatar circles (rounded-full).
 *  - No drop shadows on cards — hairline borders only.
 *  - button-primary appears maximum once per visible fold.
 */
const config: Config = {
  content: [
    './index.html',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    // ── Override Tailwind defaults completely for strict token discipline ──
    screens: {
      // PRD §4.8 Responsive Breakpoints
      'mobile-narrow': '320px',   // Hero display-xl scales 48px → 32px
      'mobile':        '480px',   // Single-column; footer accordion
      'tablet':        '768px',   // 3-up → 2-up; primary nav hamburger
      'desktop-small': '1024px',  // 4-up → 3-up cards
      'desktop':       '1280px',  // Same, slightly narrower gutters
      'desktop-large': '1440px',  // Default 4-up grid, 6-col footer
      'ultrawide':     '1920px',  // Content max-width 1280px; outer gutters ~80px
    },

    // Override default border radius — PRD §4.4 only allows these four values
    borderRadius: {
      // --radius-none: 0px — Hero, footer, nav, dark CTA strips
      'none': '0px',
      // --radius-xs: 1px — Decorative micro-rules
      'xs':   '1px',
      // --radius-sm: 2px — ALL interactive elements
      'sm':   '2px',
      // --radius-full: 9999px — Avatar circles, social icons ONLY
      'full': '9999px',
      // Default (maps to sm so class="rounded" is safe)
      'DEFAULT': '2px',
    },

    extend: {
      // ── §4.1 Color Tokens ────────────────────────────────────────────
      colors: {
        // Brand & Accent
        primary:            '#76b900',
        'primary-dark':     '#5a8d00',
        'accent-green-pale':'#bff230',

        // Surfaces
        ink:                '#000000',
        canvas:             '#ffffff',
        'surface-dark':     '#000000',
        'surface-soft':     '#f7f7f7',
        'surface-elevated': '#1a1a1a',
        hairline:           '#cccccc',
        'hairline-strong':  '#5e5e5e',

        // Text
        body:               '#1a1a1a',
        mute:               '#757575',
        stone:              '#898989',
        ash:                '#a7a7a7',
        'on-dark':          '#ffffff',
        'on-dark-mute':     'rgba(255,255,255,0.7)',
        'on-primary':       '#000000',
        'link-blue':        '#0046a4',

        // Semantic
        error:              '#e52020',
        'error-deep':       '#650b0b',
        warning:            '#df6500',
        'warning-bright':   '#ef9100',
        'success-deep':     '#3f8500',

        // Editorial Accents (long-form content only)
        'accent-purple':       '#952fc6',
        'accent-purple-pale':  '#f9d4ff',
        'accent-yellow-pale':  '#feeeb2',
      },

      // ── §4.2 Typography Tokens ───────────────────────────────────────
      fontFamily: {
        // Font stack: Inter → Arial → Helvetica
        sans: ['Inter', 'Arial', 'Helvetica', 'sans-serif'],
      },

      fontSize: {
        // Named exactly as PRD token names
        // Format: [fontSize, { lineHeight, fontWeight, letterSpacing }]
        'display-xl':   ['48px',   { lineHeight: '1.25', fontWeight: '700' }],
        'display-lg':   ['36px',   { lineHeight: '1.25', fontWeight: '700' }],
        'heading-xl':   ['24px',   { lineHeight: '1.25', fontWeight: '700' }],
        'heading-lg':   ['22px',   { lineHeight: '1.75', fontWeight: '400' }],
        'heading-md':   ['20px',   { lineHeight: '1.25', fontWeight: '700' }],
        'heading-sm':   ['18px',   { lineHeight: '1.40', fontWeight: '700' }],
        'card-title':   ['17px',   { lineHeight: '1.47', fontWeight: '700' }],
        'body-md':      ['16px',   { lineHeight: '1.50', fontWeight: '400' }],
        'body-strong':  ['16px',   { lineHeight: '1.50', fontWeight: '700' }],
        'body-sm':      ['15px',   { lineHeight: '1.67', fontWeight: '400' }],
        'button-lg':    ['18px',   { lineHeight: '1.25', fontWeight: '700' }],
        'button-md':    ['16px',   { lineHeight: '1.25', fontWeight: '700' }],
        'button-sm':    ['14.4px', { lineHeight: '1.00', fontWeight: '700', letterSpacing: '0.144px' }],
        'link-md':      ['15px',   { lineHeight: '1.50', fontWeight: '400' }],
        'caption-md':   ['14px',   { lineHeight: '1.43', fontWeight: '700' }],
        'caption-sm':   ['12px',   { lineHeight: '1.25', fontWeight: '400' }],
        'caption-xs':   ['11px',   { lineHeight: '1.00', fontWeight: '700' }],
        'utility-xs':   ['10px',   { lineHeight: '1.50', fontWeight: '700' }],
        // Mobile hero scale-down (PRD §4.8 mobile-narrow)
        'display-xl-mobile': ['32px', { lineHeight: '1.25', fontWeight: '700' }],
      },

      // ── §4.3 Spacing Tokens ──────────────────────────────────────────
      spacing: {
        // Named spacing tokens — these are the ONLY allowed spacing values
        // (Tailwind's default scale is extended, not overridden, so px numbers
        //  still work for utility generation but named tokens take precedence
        //  in all application code.)
        'xxs':     '2px',
        'xs':      '4px',
        'sm':      '8px',
        'md':      '12px',
        'lg':      '16px',
        'xl':      '24px',
        'xxl':     '32px',
        'section': '64px',   // Vertical gap between all major content blocks
        'hero-v':  '80px',   // Hero chapter vertical padding
        'hero-h':  '48px',   // Hero chapter horizontal padding
      },

      // ── §4.5 Elevation & Shadow ──────────────────────────────────────
      boxShadow: {
        // Level 0 — Flat: No shadow (default none)
        'none':        'none',
        // Level 3 — Soft Shadow: Sticky nav only
        'nav':         '0 0 5px 0 rgba(0,0,0,0.3)',
        // Cards: NO shadows — use border only (hairline)
      },

      // ── Navigation chrome heights (PRD §4.6) ─────────────────────────
      height: {
        // Utility-bar: 32px
        'utility-bar':    '32px',
        // Primary-nav: 64px
        'primary-nav':    '64px',
        // Breadcrumb-bar: 48px
        'breadcrumb-bar': '48px',
        // Sub-nav-strip: 56px
        'sub-nav-strip':  '56px',
        // Button heights per PRD §4.6
        'btn-lg':  '44px',   // All buttons — min 44px for WCAG AA touch target
        'btn-auto': 'auto',
        // Corner square
        'corner-sq-sm': '12px',
        'corner-sq-lg': '16px',
      },

      width: {
        'corner-sq-sm': '12px',
        'corner-sq-lg': '16px',
        // Auth card width
        'auth-card': '420px',
        // Max content width (ultrawide)
        'content-max': '1280px',
      },

      minHeight: {
        // WCAG AA minimum touch target
        'touch': '44px',
      },

      minWidth: {
        // WCAG AA minimum touch target
        'touch': '44px',
      },

      // ── Outline (focus ring — PRD §4 CRITICAL RULE) ──────────────────
      outlineColor: {
        DEFAULT: '#76b900',
        focus:   '#76b900',
      },
      outlineWidth: {
        DEFAULT: '2px',
        focus:   '2px',
      },
      outlineStyle: {
        DEFAULT: 'solid',
      },

      // ── Border widths ─────────────────────────────────────────────────
      borderWidth: {
        DEFAULT: '1px',
        '0':     '0',
        '2':     '2px',
      },

      borderColor: {
        DEFAULT:        '#cccccc',
        hairline:       '#cccccc',
        'hairline-strong': '#5e5e5e',
        primary:        '#76b900',
        error:          '#e52020',
      },

      // ── Letter spacing ────────────────────────────────────────────────
      letterSpacing: {
        // caption-md is uppercase per PRD
        'caption': '0',
        'button-sm': '0.144px',
      },

      // ── Z-index layers ────────────────────────────────────────────────
      zIndex: {
        'nav':     '100',
        'overlay': '200',
        'modal':   '300',
        'toast':   '400',
      },

      // ── Transitions ───────────────────────────────────────────────────
      transitionDuration: {
        'fast':   '150ms',
        'normal': '250ms',
        'slow':   '400ms',
      },
    },
  },
  plugins: [],
}

export default config
