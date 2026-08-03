# Product Requirements Document
# EcoMetric — Automated EPD & Life Cycle Assessment Platform

**Version:** 1.0  
**Status:** Ready for Engineering  
**Last Updated:** 2026-07-27  
**Audience:** AI Agent / Full-Stack Engineering Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & Success Metrics](#2-product-vision--success-metrics)
3. [Target Users & Personas](#3-target-users--personas)
4. [Design System Specification](#4-design-system-specification)
5. [Information Architecture & Navigation](#5-information-architecture--navigation)
6. [Page & Screen Specifications](#6-page--screen-specifications)
7. [Mathematical Computation Engine](#7-mathematical-computation-engine)
8. [Technical Architecture](#8-technical-architecture)
9. [Data Models & Schema](#9-data-models--schema)
10. [API Specifications](#10-api-specifications)
11. [Security & Access Control](#11-security--access-control)
12. [Regulatory Compliance Requirements](#12-regulatory-compliance-requirements)
13. [Performance Requirements](#13-performance-requirements)
14. [Error Handling & Edge Cases](#14-error-handling--edge-cases)
15. [Constraints & Assumptions](#15-constraints--assumptions)

---

## 1. Executive Summary

EcoMetric is an enterprise-grade, cloud-native web application that automates the creation, verification, and publication of Environmental Product Declarations (EPDs) in accordance with ISO 14025, ISO 14040/14044, and EN 15804+A2 standards. The platform replaces fragmented, manual desktop-based LCA workflows with a deterministic, matrix-algebra-powered computation engine backed by an ecoinvent v3.10 database.

**Core value proposition:** A manufacturer who previously spent 3–6 months and $20,000–$80,000 per EPD via consultancy engagement can complete a fully audit-ready EPD in a single software session — with zero formatting errors, automated PCR compliance, and complete digital traceability for third-party verifiers.

**Regulatory context served:**
- EU Construction Products Regulation (CPR) → EN 15804+A2 EPDs
- Ecodesign for Sustainable Products Regulation (ESPR) → Digital Product Passport (DPP) data layer
- Carbon Border Adjustment Mechanism (CBAM) → Scope 1/2/3 embedded emissions per functional unit

---

## 2. Product Vision & Success Metrics

### Vision Statement
To make rigorous, audit-grade Life Cycle Assessments as fast and reliable as running a financial report — no LCA expertise required, no manual formatting, no verification rejections.

### Primary KPIs

| Metric | Target |
|---|---|
| EPD generation time (end-to-end) | < 8 hours from BOM input to PDF export |
| Third-party verification pass rate | ≥ 95% first-submission success |
| Matrix computation time (full lifecycle) | < 10 seconds for ≤ 500-node supply chain |
| GWP result reproducibility (same inputs) | 100% deterministic — bit-identical output |
| WCAG AA compliance | All pages |
| Mobile responsiveness | All screens functional at 320px minimum width |

---

## 3. Target Users & Personas

### Persona A — Jay Singh, Sustainability Engineer (Primary)
- **Role:** Sustainability / environmental engineer at a mid-to-large manufacturing OEM
- **Goal:** Generate an EN 15804+A2-compliant EPD for a product without engaging an LCA consultancy
- **Pain points:** Current tools require manual ecoinvent database searches, manual table formatting, and produce unstructured PDF exports that fail verification
- **Technical fluency:** Moderate — familiar with BOM systems, ERP exports, basic data entry; not a programmer

### Persona B — LCA Consultant (Secondary)
- **Role:** Independent or agency-based LCA practitioner managing EPDs for multiple clients
- **Goal:** Run multiple EPD projects concurrently across clients from a single dashboard
- **Pain points:** Manually reconciling different PCR rules per product category; managing verifier correspondence

### Persona C — Third-Party Verifier (Read-only)
- **Role:** Accredited independent body reviewing EPD package for publication
- **Goal:** Trace every calculation back to elementary exchange level and confirm standard compliance
- **Pain points:** Incomplete background reports, missing data lineage, unreadable PDF formatting

### Persona D — Portfolio Manager / Sustainability Director (Executive)
- **Role:** Corporate sustainability team lead overseeing EPD compliance across a product catalog
- **Goal:** See portfolio-wide EPD status, carbon hotspots, and compliance deadlines in a single view

---

## 4. Design System Specification

> **Implementation note for AI agent:** All visual decisions in this PRD derive from the design token system defined below. Never deviate from these tokens. All components must match these exact specifications. The font stack falls back to Inter → Arial → Helvetica for the proprietary brand sans-serif.

### 4.1 Color Tokens

```css
:root {
  /* Brand & Accent */
  --color-primary:            #76b900;  /* Green — primary CTA, active states, corner squares */
  --color-primary-dark:       #5a8d00;  /* Green pressed state */
  --color-accent-green-pale:  #bff230;  /* Editorial highlight only — never on chrome */

  /* Surfaces */
  --color-ink:                #000000;  /* Headlines, body text on canvas */
  --color-canvas:             #ffffff;  /* Page body, card backgrounds */
  --color-surface-dark:       #000000;  /* Hero, footer, primary nav, dark CTA strips */
  --color-surface-soft:       #f7f7f7;  /* Breadcrumbs, sub-nav, alternating rows */
  --color-surface-elevated:   #1a1a1a;  /* Nested panels inside dark sections */
  --color-hairline:           #cccccc;  /* 1px card borders, table rules on light canvas */
  --color-hairline-strong:    #5e5e5e;  /* 1px dividers on dark surfaces */

  /* Text */
  --color-body:               #1a1a1a;  /* Long-form paragraph text */
  --color-mute:               #757575;  /* Metadata, breadcrumb separators */
  --color-stone:              #898989;  /* Low-emphasis text, disabled */
  --color-ash:                #a7a7a7;  /* Disabled icons, faint utility text */
  --color-on-dark:            #ffffff;  /* Primary text on surface-dark */
  --color-on-dark-mute:       rgba(255,255,255,0.7); /* Secondary text on dark */
  --color-on-primary:         #000000;  /* Text on green CTA buttons */
  --color-link-blue:          #0046a4;  /* Inline prose anchors ONLY */

  /* Semantic */
  --color-error:              #e52020;
  --color-error-deep:         #650b0b;
  --color-warning:            #df6500;
  --color-warning-bright:     #ef9100;
  --color-success-deep:       #3f8500;

  /* Editorial Accents (long-form content only) */
  --color-accent-purple:      #952fc6;
  --color-accent-purple-pale: #f9d4ff;
  --color-accent-yellow-pale: #feeeb2;
}
```

### 4.2 Typography Tokens

**Font stack:** `'Inter', 'Arial', 'Helvetica', sans-serif`  
**Icon library:** Font Awesome 6 Free (chevrons, social, search, menu icons at 14–22px)

```css
/* Type scale — size / weight / line-height */
--type-display-xl:   48px / 700 / 1.25;   /* Hero headline */
--type-display-lg:   36px / 700 / 1.25;   /* Section headline, large stat callouts */
--type-heading-xl:   24px / 700 / 1.25;   /* Sub-section title, CTA strip headline */
--type-heading-lg:   22px / 400 / 1.75;   /* Long-form intro paragraph heading */
--type-heading-md:   20px / 700 / 1.25;   /* Card group title, sub-nav anchor */
--type-heading-sm:   18px / 700 / 1.40;   /* Side-rail filter group, small section label */
--type-card-title:   17px / 700 / 1.47;   /* Resource card title, product card title */
--type-body-md:      16px / 400 / 1.50;   /* Default body copy, paragraphs */
--type-body-strong:  16px / 700 / 1.50;   /* Inline emphasis, nav links, labels */
--type-body-sm:      15px / 400 / 1.67;   /* Card descriptions, secondary copy */
--type-button-lg:    18px / 700 / 1.25;   /* Hero primary CTA */
--type-button-md:    16px / 700 / 1.25;   /* Standard buttons */
--type-button-sm:  14.4px / 700 / 1.00; letter-spacing: 0.144px; /* Pill tabs, compact CTAs */
--type-link-md:      15px / 400 / 1.50;   /* Inline anchor links */
--type-caption-md:   14px / 700 / 1.43; text-transform: uppercase; /* Eyebrows, breadcrumbs */
--type-caption-sm:   12px / 400 / 1.25;   /* Footnotes, metadata, table captions */
--type-caption-xs:   11px / 700 / 1.00;   /* Pill chip labels, utility-bar text */
--type-utility-xs:   10px / 700 / 1.50; text-transform: uppercase; /* Legal fine print */
```

### 4.3 Spacing Tokens

```css
--spacing-xxs:     2px;
--spacing-xs:      4px;
--spacing-sm:      8px;
--spacing-md:      12px;
--spacing-lg:      16px;
--spacing-xl:      24px;
--spacing-xxl:     32px;
--spacing-section: 64px;  /* Vertical gap between all major content blocks */
--spacing-hero-v:  80px;  /* Hero chapter vertical padding */
--spacing-hero-h:  48px;  /* Hero chapter horizontal padding */
```

### 4.4 Border Radius Tokens

```css
--radius-none: 0px;   /* Hero, footer, nav, dark CTA strips */
--radius-xs:   1px;   /* Decorative micro-rules */
--radius-sm:   2px;   /* ALL interactive elements — buttons, cards, inputs, tabs, badges */
--radius-full: 9999px; /* Avatar circles, social icons only */
```

> **Rule:** No element in the application may exceed 2px border radius except avatar/icon circles. The system reads as engineering-grade, not consumer.

### 4.5 Elevation & Shadow

```css
/* Level 0 — Flat: Canvas-on-canvas blocks, hero content, footer body */
/* No border, no shadow */

/* Level 1 — Hairline: All cards on canvas, table cells, comparison panels */
border: 1px solid var(--color-hairline);

/* Level 2 — Hairline Strong: Dividers on dark surfaces */
border: 1px solid var(--color-hairline-strong);

/* Level 3 — Soft Shadow: Sticky nav only */
box-shadow: 0 0 5px 0 rgba(0,0,0,0.3);
```

> **Rule:** Cards do NOT use drop shadows. Cards are flat rectangles with hairline borders only.

### 4.6 Component Specifications

#### Buttons

| Component | Background | Text | Border | Padding | Height | Radius |
|---|---|---|---|---|---|---|
| `button-primary` | `#76b900` | `#000000` | none | `11px 24px` | 44px | 2px |
| `button-primary-active` | `#5a8d00` | `#000000` | none | same | 44px | 2px |
| `button-outline` | transparent | `#000000` | 2px solid `#76b900` | `11px 13px` | 44px | 2px |
| `button-outline-on-dark` | transparent | `#ffffff` | 1px solid `#ffffff` | `11px 13px` | 44px | 2px |
| `button-ghost-link` | transparent | `#76b900` | none | 0 | auto | 0px |
| `button-disabled` | `#f7f7f7` | `#a7a7a7` | none | `11px 24px` | 44px | 2px |

#### Tabs & Chips

| Component | Background | Text | Typography | Padding | Radius |
|---|---|---|---|---|---|
| `pill-tab` | transparent | `#000000` | button-sm | `10px 18px` | 2px |
| `pill-tab-active` | `#000000` | `#ffffff` | button-sm | `10px 18px` | 2px |
| `badge-tag` | `#f7f7f7` | `#1a1a1a` | caption-md (uppercase) | `4px 10px` | 2px |

#### Inputs

| Component | Background | Text | Border | Height | Radius |
|---|---|---|---|---|---|
| `text-input` | `#ffffff` | `#000000` | 1px solid `#cccccc` | 44px | 2px |
| `text-input-focused` | `#ffffff` | `#000000` | 2px solid `#76b900` | 44px | 2px |
| `search-input` | `#ffffff` | `#000000` | 1px solid `#cccccc` | 40px | 2px |

#### Cards

| Component | Background | Border | Padding | Radius | Notes |
|---|---|---|---|---|---|
| `product-card` | `#ffffff` | 1px solid `#cccccc` | 24px | 2px | Corner square top-left |
| `feature-card` | `#ffffff` | 1px solid `#cccccc` | 32px | 2px | Icon + heading + body |
| `resource-card` | `#ffffff` | 1px solid `#cccccc` | 24px | 2px | Badge tag + thumbnail |
| `callout-stat` | `#ffffff` | 1px solid `#cccccc` | 32px | 2px | Large number in green |

#### Decorative Corner Square

```
Size:       12×12px (16×16px on hero callouts)
Color:      #76b900
Radius:     0px
Position:   Anchored to top-left OR bottom-right corner of card — never both
Usage:      Every reusable card component gets exactly one corner square
```

#### Navigation Chrome

| Component | Background | Text | Height |
|---|---|---|---|
| `utility-bar` | `#000000` | `#ffffff` | 32px |
| `primary-nav` | `#000000` | `#ffffff` | 64px |
| `breadcrumb-bar` | `#f7f7f7` | `#1a1a1a` | 48px |
| `sub-nav-strip` | `#f7f7f7` | `#000000` | 56px |

### 4.7 Page Rhythm Rules

1. Hero/footer chapters use `--color-surface-dark` (black). Body sections use `--color-canvas` (white). They **alternate in a predictable rhythm** down every page.
2. Every major content block is separated by `--spacing-section` (64px) vertical gap.
3. No decorative dividers between sections. Air comes from the contrast between black and white chapter blocks.
4. The `button-primary` (green fill) appears **once per fold maximum**. If two primary actions coexist, demote one to `button-outline`.
5. `--color-primary` (#76b900) is used only for: primary CTAs, active tab states, corner squares, ghost-link arrows.

### 4.8 Responsive Breakpoints

| Breakpoint | Width | Key Changes |
|---|---|---|
| ultrawide | 1920px+ | Content max-width 1280px; outer gutters ~80px |
| desktop-large | 1440px | Default — 4-up card grid, 6-col footer |
| desktop | 1280px | Same, slightly narrower gutters |
| desktop-small | 1024px | 4-up → 3-up cards; sub-nav stays horizontal |
| tablet | 768px | 3-up → 2-up; primary nav becomes hamburger drawer |
| mobile | 480px | Single-column; footer accordion |
| mobile-narrow | 320px | Hero display-xl scales 48px → 32px |

**Touch targets:** All interactive elements ≥ 44×44px (WCAG AA).

---

## 5. Information Architecture & Navigation

### 5.1 Route Map

```
/                          → Marketing Landing Page
/login                     → Authentication
/register                  → Account Creation
/dashboard                 → Project Dashboard (authenticated)
/projects/new              → New Project Wizard (Step 1: Setup)
/projects/:id/inventory    → BOM & Data Ingestion (Step 2)
/projects/:id/calculate    → LCA Results Viewer (Step 3)
/projects/:id/hotspots     → Hotspot Analytics Dashboard (Step 4)
/projects/:id/export       → EPD Generation & Preview (Step 5)
/projects/:id/publish      → Verification & Portfolio (Step 6)
/portfolio                 → Portfolio Overview
/verifier/:token           → Read-only Verifier Portal
/settings                  → Account & Organization Settings
/admin                     → Admin Console (internal)
```

### 5.2 Primary Navigation (Authenticated)

The top navigation bar (`primary-nav`) contains:
- **Left:** Product wordmark / logo
- **Center:** `Projects` · `Portfolio` · `Resources` · `Settings`
- **Right:** Search icon · User avatar with dropdown · `+ New Declaration` (button-primary)

A `breadcrumb-bar` sits directly below primary-nav on every interior page showing the current project path, e.g. `PROJECTS > AQUAEDGE 19DV > INVENTORY`.

### 5.3 In-Project Sub-Navigation

Within an active project, a `sub-nav-strip` persists beneath the breadcrumb showing the 6 workflow steps as sequential anchor links:

```
1. Setup  →  2. Inventory  →  3. Calculate  →  4. Hotspots  →  5. Export  →  6. Publish
```

Steps are displayed as `pill-tab` components. The current step is `pill-tab-active`. Steps ahead of the current progress are displayed in `--color-ash` and are non-clickable until the prior step is complete.

---

## 6. Page & Screen Specifications

### 6.1 Marketing Landing Page (`/`)

**Layout:** Dark hero chapter → Feature cards section → How-it-works section → Stat callouts → Regulatory compliance section → Dark CTA strip → Footer.

#### Hero Chapter (`hero-card-dark`)
- **Background:** `--color-surface-dark` with full-bleed abstract visualization of a supply chain network or molecular structure (SVG-based, no stock photos required)
- **Headline:** `display-xl` — "Audit-Ready EPDs. Generated Automatically."
- **Subheadline:** `heading-lg` — "From bill of materials to verified Environmental Product Declaration in a single session."
- **Primary CTA:** `button-primary` — "Start Your First EPD"
- **Secondary CTA:** `button-outline-on-dark` — "See How It Works"
- **Corner square:** 16×16px at bottom-right of hero copy block

#### Features Section (4-up `feature-card` grid)
Cards explaining the four platform pillars:
1. **Matrix-Powered LCA** — Icon: `fa-function` — Body: "Heijungs-Suh linear algebra engine solves complete supply chain networks in seconds."
2. **PCR Auto-Compliance** — Icon: `fa-shield-check` — Body: "Product Category Rules automatically enforced. System boundaries set without manual lookup."
3. **Ecoinvent Integration** — Icon: `fa-database` — Body: "Sub-millisecond semantic search across the full ecoinvent v3.10 background database."
4. **Verification-Ready Export** — Icon: `fa-file-certificate` — Body: "PDF output meets EN 15942 formatting requirements. Zero blank cells, zero rejections."

#### How-It-Works Section
Sequential numbered section (1→6) describing the six workflow steps. Use a horizontal timeline on desktop, vertical accordion on mobile. Eyebrow text: "THE WORKFLOW" in `caption-md` uppercase green.

#### Stat Callout Bar (3-up `callout-stat` grid)
- `display-lg` green number: **6 steps** / caption: "From setup to published EPD"
- `display-lg` green number: **95%** / caption: "First-submission verification pass rate"
- `display-lg` green number: **10× faster** / caption: "Versus manual LCA consultancy"

#### Regulatory Compliance Section
Three `resource-card` components referencing CPR, ESPR/DPP, and CBAM, each with a `badge-tag` label ("REGULATION"), brief body text explaining how the platform addresses it, and a `button-ghost-link` "Learn More →".

#### Dark CTA Strip (`cta-strip-dark`)
- Headline: `heading-xl` — "Ready to Generate Your First EPD?"
- Button: `button-primary` — "Get Started Free"

#### Footer (`footer-section`)
- 5-column link grid: Product · Resources · Standards · Company · Support
- Social icons row + legal fine-print in `utility-xs`

---

### 6.2 Authentication Pages (`/login`, `/register`)

**Layout:** Centered 420px card on `--color-surface-soft` background. No nav chrome on these pages.

#### Login (`/login`)
- Logo/wordmark centered at top
- Inputs: Email (`text-input`), Password (`text-input`)
- Primary CTA: `button-primary` full-width — "Sign In"
- Secondary link: `link-inline` — "Forgot your password?"
- SSO option: `button-outline` full-width — "Continue with Google"
- Link to register: `body-sm` + `link-inline`

#### Register (`/register`)
- Inputs: Full Name, Organization, Work Email, Password, Confirm Password
- Role selector: pill-tab row — "Sustainability Engineer" · "LCA Consultant" · "Portfolio Manager"
- Primary CTA: `button-primary` full-width — "Create Account"

---

### 6.3 Project Dashboard (`/dashboard`)

**Layout:** `sub-nav-strip` removed on this page. Shows the `primary-nav` + `breadcrumb-bar` ("PROJECTS") + full-width content grid.

#### Stats Bar (4-up `callout-stat` strip)
- Active Projects count (green number)
- EPDs Published this year (green number)
- Projects Pending Verification (warning amber number using `--color-warning`)
- Total Products in Portfolio (green number)

#### Project Cards Grid (3-up on desktop, responsive)
Each `product-card` contains:
- Top: 12×12 `corner-square` top-left
- `badge-tag`: status — "IN PROGRESS" / "PENDING VERIFICATION" / "PUBLISHED"
- `card-title`: Project name (e.g., "AquaEdge 19DV Centrifugal Chiller")
- `body-sm`: Standard (e.g., EN 15804+A2) · Functional unit · Last edited date
- Completion progress bar: thin green fill bar showing step progress (1–6)
- Footer: `button-ghost-link` "Open Project →"

#### Empty State (first-time user)
- Centered illustration of an empty grid
- `heading-md`: "No projects yet"
- `body-md`: "Create your first EPD declaration to get started."
- `button-primary`: "+ New Declaration"

---

### 6.4 Step 1 — Project Setup (`/projects/new`)

**Purpose:** User defines all project meta-parameters. System provisions the architecture.

#### Left Column (form, 60%)
Fields rendered as labeled `text-input` groups:

**Product Information**
- Product Name (text) — required
- Product Identifier / SKU (text)
- UN CPC Classification Code (searchable dropdown)
- Manufacturer Name (text)
- Manufacturing Country (dropdown)

**Standard & Scope**
- EPD Standard (radio card selector):
  - `EN 15804+A2` (European construction products)
  - `ISO 21930` (Global building materials)
  - `ISO 14025` (General Type III)
- EPD Program Operator (dropdown): International EPD System · EPD Hub · IBU · BRE
- PCR / c-PCR (auto-populated based on CPC code + standard; editable)

**Functional Unit**
- Declared Unit (text + unit dropdown): e.g., "1" + "ton of chilling capacity"
- Reference Service Life / RSL (number + unit): e.g., "75" + "years"

**System Boundaries** (auto-enforced based on selected standard — shown as read-only chips after selection)
- Module checkboxes: A1–A3, A4, A5, B1–B7, C1–C4, D

#### Right Column (live preview, 40%)
- `feature-card` showing a real-time system boundary diagram (SVG) that updates as standard is selected
- `callout-stat` showing the number of PCR rules auto-loaded
- Notification strip in `--color-accent-yellow-pale` if PCR is older than 5 years: "Warning: This PCR was last updated [date]. Verify currency with program operator."

**Footer Actions**
- `button-primary` — "Save & Continue to Inventory →"
- `button-outline` — "Save as Draft"

---

### 6.5 Step 2 — Inventory Input (`/projects/:id/inventory`)

**Purpose:** User inputs the Bill of Materials, energy data, transport, and end-of-life data. System continuously validates.

**Layout:** Three-pane. Left: life cycle module tree. Center: active module input table. Right: real-time compliance sidebar.

#### Left Pane — Module Tree
Collapsible tree of all active life cycle modules from Step 1:
```
▶ A1–A3  Product Stage
  ▶ A1   Raw Material Supply
  ▶ A2   Transport to Manufacturer
  ▶ A3   Manufacturing
▶ A4     Distribution
▶ B6     Operational Energy Use
▶ C1–C4  End-of-Life
▶ D      Beyond System Boundary
```
Each module shows: completion status icon (✓ green / ⚠ warning / ✗ incomplete) + item count badge.

#### Center Pane — Material Input Table

**BOM entry row (per material):**
- Material name — searchable `search-input` that triggers WebSocket query to ecoinvent database
- Quantity — `text-input` (numeric)
- Unit — dropdown (kg, m², m³, pieces)
- Matched LCI dataset — auto-populated from ecoinvent search result; editable dropdown
- Data quality — `badge-tag` (PRIMARY / SECONDARY / PROXY)
- Delete row button

**Add Material** — `button-ghost-link` "+ Add Material" at bottom of table

**Cut-Off Rule Monitor** (inline notification, shown automatically):
- Green bar: "Cut-off compliance: All omitted materials < 1% individual / < 5% aggregate ✓"
- Warning state: "⚠ Packaging adhesive film auto-excluded under 5% cut-off rule. Logged for verifier report."
- Error state: "✗ Omitted flows exceed 5% threshold. Action required."

**Transport Input** (Module A4):
- Distance (km) — `text-input`
- Transport mode — dropdown (Heavy truck / Rail / Ship / Air)
- Load capacity utilization (%) — `text-input`

**Energy Input** (Module A3, B6):
- Energy type (dropdown): Electricity · Natural gas · Steam · Compressed air
- Consumption — `text-input` + unit
- Grid mix — dropdown: ecoinvent region presets OR custom upload

**End-of-Life** (Modules C1–C4):
- Waste scenario — dropdown with preset scenarios (Landfill / Incineration / Recycling / Reuse)
- Percentage allocation per scenario — `text-input` fields that must sum to 100%

#### Right Pane — Compliance Sidebar (`feature-card` stack)
Live-updating validation panel:
- **Mass balance check:** "Total modeled mass: 847.3 kg. Declared unit: 1 ton. Ratio: 84.7% ✓"
- **Data quality score (DQI):** Progress bar, 0–100, based on primary vs secondary data ratio
- **Age check:** Warning if any secondary dataset reference year is > 10 years old
- **Missing modules:** List of any required modules with no data yet
- **Next action prompt:** Directive text telling user what to do next

---

### 6.6 Step 3 — LCA Calculation (`/projects/:id/calculate`)

**Purpose:** Single-click trigger of the Python computation engine; displays structured results.

#### Pre-Calculation State
- Summary card listing all inputs: material count, energy inputs, transport nodes
- Confirmation checklist: all required modules filled ✓ / cut-off compliant ✓ / DQI score shown
- `button-primary` (large, centered): "Calculate LCA"

#### During Calculation
- Full-page loading overlay on `--color-surface-dark`
- Progress indicator steps:
  1. "Building technology matrix A…"
  2. "Resolving multi-functional processes…"
  3. "Executing matrix inversion…"
  4. "Applying EF 3.1 characterization factors…"
  5. "Generating results…"
- Estimated time display

#### Results State
Results displayed as a structured data table per the EN 15942 mandatory format.

**Impact Results Table** — rows = impact categories, columns = life cycle modules:

| Impact Category | Unit | A1–A3 | A4 | B6 | C2 | C4 | D |
|---|---|---|---|---|---|---|---|
| GWP-total | kg CO₂e | 1.24E+02 | 3.41E+00 | 8.90E+02 | … | … | … |
| GWP-fossil | kg CO₂e | … | … | … | … | … | … |
| GWP-biogenic | kg CO₂e | … | … | … | … | … | … |
| AP | mol H⁺ eq. | … | … | … | … | … | … |
| EP-marine | kg N eq. | … | … | … | … | … | … |
| EP-freshwater | kg P eq. | … | … | … | … | … | … |
| EP-terrestrial | mol N eq. | … | … | … | … | … | … |
| POCP | kg NMVOC | … | … | … | … | … | … |
| ODP | kg CFC-11 eq. | … | … | … | … | … | … |
| ADPE | kg Sb eq. | … | … | … | … | … | … |
| ADPF | MJ | … | … | … | … | … | … |
| WDP | m³ depriv. | … | … | … | … | … | … |

Rules for table display:
- Values shown in scientific notation (e.g., 1.65E+02)
- "ND" (Not Declared) if module is outside system boundary
- Zero blank cells — system must populate every cell
- Column totals in `--color-primary` bold
- `badge-tag` in table header showing "EN 15804+A2 EF 3.1"

**Additional Resource Use Table** and **Waste Categories Table** follow same structure per EN 15804+A2 mandatory indicators.

---

### 6.7 Step 4 — Hotspot Analytics (`/projects/:id/hotspots`)

**Purpose:** Interactive visual analytics to identify emission drivers and run scenario comparisons.

#### Layout: Split — Charts Left (65%), Controls Right (35%)

#### Primary Chart: GWP Contribution by Module
- Bar chart (SVG, D3.js) — horizontal bars per life cycle module
- Bar fill: `--color-primary` for highest contributor, `--color-hairline` for others
- On click: drills into material-level breakdown for that module
- `corner-square` decorative element on chart card top-left

#### Secondary Chart: Material Mass vs. GWP Contribution Scatter
- X-axis: % of total product mass
- Y-axis: % of total GWP
- Points labeled with material name
- Red quadrant marker for "high impact, low mass" hotspot zone

#### Sensitivity Panel (Right Column)
For each material input flagged with high sensitivity coefficient (∂g/∂a_ij):
- `resource-card` showing:
  - Material name + `badge-tag` "HIGH SENSITIVITY"
  - Sensitivity value displayed as `callout-stat` mini format
  - Warning: "Primary data required. Secondary dataset introduces high result variance."
  - `button-ghost-link` "Update Data Source →"

#### Scenario Comparison Tool
- Dropdown: "Swap dataset for [material]" — triggers instant recalculation
- Side-by-side `callout-stat` cards: Baseline GWP vs. Scenario GWP with delta %
- `button-outline` — "Reset to Baseline"

---

### 6.8 Step 5 — EPD Generation (`/projects/:id/export`)

**Purpose:** One-click generation of the complete, verification-ready EPD documentation package.

#### Pre-Export Checklist
`feature-card` with bulleted checklist:
- ✓ All mandatory impact categories populated
- ✓ Data quality assessment complete (DQI: 87%)
- ✓ Cut-off criteria documented
- ✓ Allocation method documented (economic allocation, 60% ethanol / 40% biochemicals)
- ✓ EN 15804+A2 formatting rules validated
- ✓ Zero blank cells in impact table

Any failed check displayed in `--color-error` with an action link.

#### Export Actions

Two `feature-card` blocks side-by-side:

**Card 1 — Public EPD Document**
- `badge-tag`: "PUBLIC DOCUMENT"
- Body: "Standardized EN 15942 format EPD. Includes product description, material composition tables, system boundary diagram, and full LCIA results matrices."
- `button-primary`: "Generate Public EPD PDF"

**Card 2 — LCA Background Report**
- `badge-tag`: "CONFIDENTIAL"
- Body: "Comprehensive technical background report detailing modeling choices, cut-off justifications, data quality assessment, and primary vs. secondary data percentages."
- `button-outline`: "Generate Background Report PDF"

#### Download State
After generation:
- Both cards update to show a green ✓ confirmation
- `button-primary` becomes "Download EPD PDF"
- `button-ghost-link` "Preview in Browser →"
- PDF opens in embedded iframe preview

#### Machine-Readable Exports
- `button-outline`: "Export ILCD+EPD (XML)"
- `button-outline`: "Export OpenEPD (JSON)"

---

### 6.9 Step 6 — Publish & Portfolio (`/projects/:id/publish`)

**Purpose:** Submit for verification, manage verifier access, and scale to sibling EPDs.

#### Verifier Access Panel (`feature-card`)
- `heading-md`: "Share with Verifier"
- Input: Verifier email address (`text-input`)
- Permission: "Read-only access to all calculations down to elementary exchange level"
- `button-primary`: "Send Verifier Invitation"
- Active sessions list: verifier name + last accessed timestamp + `badge-tag` "ACTIVE"

#### Sibling EPD Generator (`feature-card`)
- `heading-md`: "Scale to Other Facilities"
- Description: "Clone this EPD's core topology for a product manufactured at a different facility. Only swap the localized electricity grid or transport datasets."
- `button-outline`: "Create Sibling EPD"
- Sibling cards list: existing siblings with completion status

#### DPP Registry Push (`feature-card`)
- `heading-md`: "Push to Digital Product Passport Registry"
- Description: "Export verified EPD dataset to ESPR-compliant DPP registry in machine-readable format with GS1 Digital Link."
- `button-outline`: "Connect DPP Registry"
- Status: `badge-tag` "NOT CONNECTED" / "CONNECTED ✓"

---

### 6.10 Verifier Portal (`/verifier/:token`)

**Access:** Read-only. No authentication — accessed via secure tokenized URL sent by project owner.

**Layout:** Identical to the authenticated project view but with:
- Persistent `badge-tag` "READ-ONLY ACCESS — VERIFIER MODE" in top utility bar
- No edit controls; all inputs shown as static text
- Full calculation trace panel showing: final demand vector f, technology matrix A dimensions, scaling vector s, characterization matrix Q applied, and final impact vector h values
- Downloadable audit log (CSV) of all data substitutions (proxy datasets used, cut-off exclusions)
- `button-primary`: "Download Complete Audit Package"

---

### 6.11 Portfolio Dashboard (`/portfolio`)

**Layout:** Stats header → regulatory deadline calendar → product catalog table → comparative charts.

#### Portfolio Stats Bar (4-up `callout-stat`)
- Total EPDs Published
- EPDs Expiring within 12 months (amber warning color)
- Average GWP across portfolio (kg CO₂e per functional unit)
- DPP Registrations complete

#### Compliance Deadline Tracker
Timeline component showing upcoming regulatory deadlines (CPR updates 2029–2032, ESPR battery 2027, etc.) with `badge-tag` labels and days-remaining countdown.

#### Product Table
Sortable, filterable table with columns: Product · Standard · GWP-total · Status · Expiry · Actions. Filter pills: All · Published · In Progress · Expired.

---

## 7. Mathematical Computation Engine

> **Implementation note:** The Python backend must implement these equations exactly and verifiably. All matrix operations must use `numpy` or `scipy.linalg` for performance. Results must be bit-identical given identical inputs (strict determinism).

### 7.1 Core Matrix Model

**Variables:**

| Symbol | Name | Dimension | Description |
|---|---|---|---|
| `f` | Final Demand Vector | (n_flows × 1) | Defines the functional unit — e.g., 1 ton chilling capacity |
| `A` | Technology Matrix | (n_flows × n_processes) | Element a_ij = economic flow i produced (+) or consumed (−) by process j |
| `B` | Intervention Matrix | (n_env_flows × n_processes) | Element b_kj = direct emission/extraction k associated with process j |
| `s` | Scaling Vector | (n_processes × 1) | Required output of each unit process to satisfy f |
| `g` | Inventory Vector | (n_env_flows × 1) | Total lifecycle inventory across supply chain |
| `Q` | Characterization Matrix | (n_impact_categories × n_env_flows) | Impact characterization factors (EF 3.1 / TRACI 2.1) |
| `h` | Impact Vector | (n_impact_categories × 1) | Final LCIA results — populates EPD tables |

**Core computation sequence:**

```python
# Step 1: Solve for scaling vector (matrix inversion)
s = np.linalg.solve(A, f)          # Preferred over explicit inversion for numerical stability

# Step 2: Calculate inventory vector
g = B @ s                           # Equivalent to B @ A^(-1) @ f

# Step 3: Apply characterization
h = Q @ g                           # Equivalent to Q @ B @ A^(-1) @ f
```

**Implementation requirements:**
- Use `scipy.sparse` for sparse matrix storage when n_processes > 1000 (typical for full ecoinvent background)
- Use `scipy.sparse.linalg.spsolve` for sparse system solving
- Validate matrix invertibility (check condition number) before solve; raise `SingularMatrixError` if `cond(A) > 1e12`
- All intermediate matrices must be logged to Firestore for verifier traceability

### 7.2 Multi-Functionality & Allocation

When the technology matrix A is non-square (fewer processes than products), apply the partitioning method:

**Inputs:**
- `A_raw`: original non-square technology matrix
- `C`: allocation matrix — user-defined factors (mass-based, economic, energy-based) per PCR
- `U`: unit/filtering matrix (identity matrix or PCR-specified filter)
- `B_0`: original intervention matrix before allocation

**Transformation:**

```python
# Compute allocated technology matrix
A_allocated = (U * (A_raw.T @ np.ones((A_raw.shape[0], 1)))) @ C

# Compute allocated intervention matrix
B_allocated = B_0.T @ C

# Resume standard computation with allocated matrices
s_allocated = np.linalg.solve(A_allocated, f)
h_allocated = Q @ B_allocated @ s_allocated
```

**Validation after allocation:**
- Assert `A_allocated` is square
- Assert `np.linalg.matrix_rank(A_allocated) == A_allocated.shape[0]` (full rank)
- Sum of allocation factors per process must equal 1.0 (tolerance: ±0.001)

### 7.3 Sensitivity & Perturbation Analysis

For each technology matrix element a_ij, compute the analytical sensitivity coefficient:

```python
def sensitivity_coefficient(B, A_inv, delta_A, f):
    """
    Compute ∂g/∂a_ij = -B @ A^(-1) @ ΔA @ A^(-1) @ f
    where ΔA is a perturbation matrix with 1 in position (i,j) and 0 elsewhere.
    """
    return -B @ A_inv @ delta_A @ A_inv @ f
```

**Hotspot flagging rule:** If |sensitivity_coefficient| for a material input exceeds 2 standard deviations above the mean sensitivity across all inputs → flag as "HIGH SENSITIVITY" in the UI and require primary data confirmation.

### 7.4 Cut-Off Criteria Enforcement

```python
def validate_cutoff(flows, total_mass, total_energy):
    """
    ISO 14044 / GPI cut-off rules:
    - Any single omitted flow must be < 1% of total mass OR energy
    - Aggregate of all omitted flows must be < 5% of total mass OR energy
    """
    for flow in flows:
        if flow.omitted:
            assert flow.mass / total_mass < 0.01, f"Flow {flow.name} exceeds 1% individual cutoff"
    
    total_omitted_mass = sum(f.mass for f in flows if f.omitted)
    assert total_omitted_mass / total_mass < 0.05, "Aggregate omitted mass exceeds 5% threshold"
```

---

## 8. Technical Architecture

### 8.1 System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  ReactJS 18 + TypeScript + Tailwind CSS                 │
│  State: Redux Toolkit / React Query                     │
│  Charts: D3.js + Recharts                               │
│  PDF Preview: react-pdf                                 │
└────────────────────┬───────────────────────────────────┘
                     │ HTTPS REST API + WebSocket
┌────────────────────▼───────────────────────────────────┐
│                   API Gateway                           │
│  FastAPI (Python 3.11+) — async                         │
│  Auth middleware: Firebase Admin SDK JWT validation     │
│  Rate limiting: 100 req/min per user                    │
└────────┬──────────────────────┬────────────────────────┘
         │                      │
┌────────▼────────┐    ┌────────▼─────────────────────────┐
│  Computation    │    │   Data & Storage Layer            │
│  Engine         │    │                                   │
│  Python / NumPy │    │  Cloud Firestore (NoSQL)          │
│  SciPy Sparse   │    │  Firebase Auth                    │
│  lxml.etree     │    │  Firebase Storage (PDF outputs)   │
│  xmlschema      │    │  Indexed ecoinvent LCI database   │
└────────┬────────┘    └──────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────┐
│              PDF Export Engine                          │
│  WeasyPrint (HTML/CSS → PDF, server-side)               │
│  Puppeteer / Playwright (SVG chart rendering)           │
│  ILCD+EPD XML generator                                 │
│  OpenEPD JSON generator                                 │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Frontend Stack

| Layer | Technology | Version |
|---|---|---|
| Framework | ReactJS | 18.x |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.x |
| State management | Redux Toolkit + React Query | latest |
| Routing | React Router | 6.x |
| Charts | D3.js + Recharts | latest |
| Tables | TanStack Table | 8.x |
| Forms | React Hook Form + Zod | latest |
| PDF preview | react-pdf | 7.x |
| WebSocket | native browser WebSocket API | — |
| Icons | Font Awesome 6 Free (via npm) | 6.x |
| Build | Vite | 5.x |

### 8.3 Backend Stack

| Layer | Technology | Notes |
|---|---|---|
| API framework | FastAPI (Python 3.11+) | Async; OpenAPI docs auto-generated |
| Matrix math | NumPy + SciPy | `scipy.sparse.linalg.spsolve` for large systems |
| XML parsing | `lxml.etree` | Streaming SAX parser for large ecoSpold2 files |
| XML validation | `xmlschema` | Full XSD 1.0/1.1 validation against official ecoSpold2 schema |
| PDF generation | WeasyPrint | Server-side HTML/CSS → PDF |
| Headless browser | Playwright (Python) | SVG/chart capture for PDF embedding |
| Database client | `google-cloud-firestore` | Admin SDK |
| Auth | `firebase-admin` | JWT verification |
| Task queue | Celery + Redis | For long-running LCA computations |
| Deployment | Railway / Google Cloud Run | Containerized via Docker |

### 8.4 Database Schema (Firestore)

**Collection hierarchy:**

```
organizations/{org_id}
  └── users/{user_id}
  └── projects/{project_id}
        ├── setup_config       (document)
        ├── materials          (sub-collection)
        │     └── {material_id} (document)
        ├── energy_inputs      (sub-collection)
        │     └── {energy_id}
        ├── transport_nodes    (sub-collection)
        │     └── {transport_id}
        ├── lca_results        (sub-collection)
        │     └── {run_id}     (document — immutable after creation)
        ├── sensitivity        (sub-collection)
        │     └── {run_id}
        ├── exports            (sub-collection)
        │     └── {export_id}  (document + Storage URL)
        └── audit_log          (sub-collection)
              └── {event_id}

lci_database/{dataset_id}               (indexed ecoinvent v3.10 — read-only)
```

### 8.5 ecoinvent Integration

- **Source format:** ecoSpold2 XML (parsed using `lxml.etree` streaming SAX)
- **Indexing:** All unit processes pre-ingested and indexed into Firestore with full-text search fields on: dataset name, activity name, geography, reference product
- **Update cycle:** ecoinvent version updates ingested on release; new version flagged to users with active projects
- **Search endpoint:** `GET /api/v1/lci/search?q={query}&geography={code}&version=3.10` — returns top 10 ranked matches with preview

---

## 9. Data Models & Schema

### 9.1 Project Document

```typescript
interface Project {
  id: string;
  org_id: string;
  created_by: string;
  created_at: Timestamp;
  updated_at: Timestamp;
  status: 'draft' | 'in_progress' | 'pending_verification' | 'published';
  current_step: 1 | 2 | 3 | 4 | 5 | 6;
  
  setup: {
    product_name: string;
    sku: string;
    cpc_code: string;
    manufacturer: string;
    manufacturer_country: string;
    standard: 'EN_15804_A2' | 'ISO_21930' | 'ISO_14025';
    program_operator: string;
    pcr_id: string;
    pcr_version: string;
    functional_unit: {
      quantity: number;
      unit: string;
      description: string;
    };
    rsl: {
      value: number;
      unit: 'years' | 'cycles';
    };
    active_modules: string[];  // e.g. ['A1','A2','A3','A4','B6','C1','C2','C3','C4']
  };
}
```

### 9.2 Material Document

```typescript
interface Material {
  id: string;
  project_id: string;
  module: string;        // e.g., 'A1', 'A3'
  name: string;          // User-entered name
  quantity: number;
  unit: string;
  lci_dataset_id: string;        // ecoinvent UUID
  lci_dataset_name: string;
  lci_dataset_geography: string;
  lci_dataset_reference_year: number;
  data_quality: 'primary' | 'secondary' | 'proxy';
  is_omitted_cutoff: boolean;
  cutoff_justification?: string;
  sensitivity_coefficient?: number;   // Populated after calculation
}
```

### 9.3 LCA Result Document

```typescript
interface LCAResult {
  id: string;
  project_id: string;
  run_timestamp: Timestamp;
  run_by: string;
  is_final: boolean;
  
  // Matrix dimensions logged for audit
  matrix_A_dimensions: [number, number];
  matrix_B_dimensions: [number, number];
  functional_unit: string;
  allocation_method: 'none' | 'mass' | 'economic' | 'energy';
  lcia_methodology: 'EF_3_1' | 'TRACI_2_1' | 'ReCiPe_2016';
  
  // Core output — nested by impact category and module
  impact_results: {
    [impact_category: string]: {
      unit: string;
      values: {
        [module: string]: number | 'ND';
      };
      total: number;
    };
  };
  
  // Raw inventory vector g (for audit trace)
  inventory_vector: Record<string, number>;
  
  // Hotspot data
  hotspots: Array<{
    material_id: string;
    sensitivity_coefficient: number;
    gwp_contribution_pct: number;
    mass_contribution_pct: number;
  }>;
}
```

### 9.4 Export Document

```typescript
interface Export {
  id: string;
  project_id: string;
  lca_result_id: string;
  generated_at: Timestamp;
  generated_by: string;
  
  public_epd: {
    pdf_url: string;        // Firebase Storage URL
    pdf_sha256: string;     // Integrity hash
    format: 'EN_15942';
  };
  
  background_report: {
    pdf_url: string;
    pdf_sha256: string;
  };
  
  machine_readable: {
    ilcd_epd_xml_url?: string;
    open_epd_json_url?: string;
  };
  
  verifier_token?: string;  // Secure random token for verifier portal
  verifier_email?: string;
  verifier_accessed_at?: Timestamp;
}
```

---

## 10. API Specifications

### 10.1 Base URL & Auth

```
Base URL:   https://api.ecometric.com/v1
Auth:       Bearer {Firebase ID Token} in Authorization header
Content:    application/json
```

### 10.2 Endpoints

#### Projects

```
GET    /projects                    → List all projects for authenticated user/org
POST   /projects                    → Create new project (body: setup config)
GET    /projects/:id                → Get single project with all sub-documents
PATCH  /projects/:id                → Update project metadata
DELETE /projects/:id                → Delete project (soft delete, 30-day recovery)
```

#### Inventory

```
GET    /projects/:id/materials              → List all material entries
POST   /projects/:id/materials              → Add material entry
PATCH  /projects/:id/materials/:mat_id      → Update material entry
DELETE /projects/:id/materials/:mat_id      → Remove material entry
GET    /projects/:id/energy                 → List energy inputs
POST   /projects/:id/energy                 → Add energy input
GET    /projects/:id/transport              → List transport nodes
POST   /projects/:id/transport              → Add transport node
```

#### LCI Database Search

```
GET    /lci/search?q={query}&geo={code}&version={ver}
       → Returns: Array<{ id, name, activity, geography, reference_year, data_quality_score }>
GET    /lci/:dataset_id
       → Returns: Full dataset metadata including elementary exchanges (summary level)
```

#### Computation

```
POST   /projects/:id/calculate
       → Triggers async LCA computation job
       → Returns: { job_id, status: 'queued' }
       
GET    /projects/:id/jobs/:job_id
       → Returns: { status: 'queued'|'running'|'complete'|'failed', progress_pct, result_id? }

GET    /projects/:id/results/:result_id
       → Returns: Full LCAResult document
       
GET    /projects/:id/results/:result_id/sensitivity
       → Returns: Sensitivity coefficients per material
```

#### Export

```
POST   /projects/:id/export
       → Triggers async PDF generation
       Body: { type: 'public_epd' | 'background_report' | 'both', lca_result_id }
       → Returns: { job_id }
       
GET    /projects/:id/exports/:export_id
       → Returns: Export document with signed download URLs
       
POST   /projects/:id/exports/:export_id/share-verifier
       Body: { email: string }
       → Sends tokenized verifier invitation email; returns { token }
       
GET    /verifier/:token
       → Public endpoint — validates token, returns read-only project snapshot
```

#### Portfolio

```
GET    /portfolio/summary
       → Returns: Aggregate stats across all org projects
GET    /portfolio/compliance-calendar
       → Returns: Upcoming regulatory deadlines with project mapping
```

### 10.3 WebSocket API (Real-Time Sync)

```
ws://api.ecometric.com/v1/projects/:id/live

Events emitted by server:
- { type: 'material_updated', payload: Material }
- { type: 'cutoff_check', payload: CutoffStatus }
- { type: 'validation_warning', payload: { field, message, severity } }
- { type: 'calculation_progress', payload: { step, pct } }
- { type: 'calculation_complete', payload: { result_id } }
```

---

## 11. Security & Access Control

### 11.1 Role-Based Access Control (RBAC)

| Role | Permissions |
|---|---|
| `org_admin` | Full CRUD on all org projects; manage users; view billing |
| `engineer` | Full CRUD on own projects; read own org's projects |
| `consultant` | Full CRUD on projects where explicitly invited; cannot view other projects |
| `verifier` | Read-only access via tokenized URL; no auth required; token expires after 90 days |
| `viewer` | Read-only on projects where invited |

### 11.2 Data Security

- All data encrypted at rest (Firestore native AES-256)
- All data encrypted in transit (TLS 1.3)
- Firebase ID tokens validated server-side on every API request
- Verifier tokens: 256-bit cryptographically random, stored as bcrypt hash in Firestore
- PDF exports stored in Firebase Storage with signed URLs (1-hour expiry)
- Audit log: all data mutations (who, what, when, old value, new value) stored immutably in Firestore

### 11.3 Data Isolation

- All Firestore queries are scoped by `org_id` — cross-organization data access is architecturally impossible
- ecoinvent LCI database is read-only; no user can modify background datasets

---

## 12. Regulatory Compliance Requirements

The platform must produce outputs that satisfy these regulatory frameworks:

### 12.1 EN 15804+A2 (Construction Products, EU CPR)

**Mandatory EPD content checklist (auto-validated by system before export):**
- [ ] Product name and description
- [ ] UN CPC classification code
- [ ] Functional unit / declared unit with RSL
- [ ] System boundary diagram (auto-generated SVG)
- [ ] Cut-off criteria declaration with aggregate mass/energy %
- [ ] Data quality assessment (DQI score by module)
- [ ] All mandatory environmental indicators (GWP-total, GWP-fossil, GWP-biogenic, GWP-luluc, ODP, AP, EP-freshwater, EP-marine, EP-terrestrial, POCP, ADPE, ADPF, WDP)
- [ ] Resource use indicators (PERE, PERM, PERT, PENRE, PENRM, PENRT, SM, RSF, NRSF, FW)
- [ ] Waste categories (HWD, NHWD, RWD)
- [ ] Output flows (CRU, MFR, MER, EEE, EET)
- [ ] Module D data (if applicable)
- [ ] All values in scientific notation with correct SI units
- [ ] "ND" (Not Declared) in all out-of-scope module cells

### 12.2 ESPR / Digital Product Passport

Export format must include:
- Unique Product Identifier (UPI)
- GS1 Digital Link compatible identifier
- Recycled content % per material
- All EPD LCIA results in machine-readable JSON (OpenEPD format)

### 12.3 CBAM (Carbon Border Adjustment Mechanism)

For products in scope (steel, aluminum, cement, fertilizers, electricity, hydrogen):
- Explicit Scope 1 (direct manufacturing A3) emissions per ton of output
- Scope 2 (electricity A3, B6) emissions with grid mix source declared
- Upstream Scope 3 (A1–A2) emissions mapped from LCA matrix result
- CBAM reporting format: XML export aligned with EU registry template

### 12.4 ISO 14044 Data Quality Requirements

- Primary data must be collected within 10-year reference window
- System must warn if any secondary dataset reference year is > 10 years old
- Data quality indicator (DQI) must be calculated and documented for each module
- Multi-functionality must be resolved via system expansion first; allocation only if expansion is not feasible — system enforces this hierarchy

---

## 13. Performance Requirements

| Requirement | Target | Hard Limit |
|---|---|---|
| LCA computation (≤ 50-node supply chain) | < 3 seconds | 10 seconds |
| LCA computation (≤ 500-node supply chain) | < 10 seconds | 30 seconds |
| LCA computation (full ecoinvent background, ~18k processes) | < 60 seconds | 120 seconds |
| ecoinvent search query response | < 200ms | 500ms |
| PDF generation (public EPD) | < 15 seconds | 45 seconds |
| PDF generation (background report) | < 30 seconds | 90 seconds |
| Page load (First Contentful Paint) | < 1.5 seconds | 3 seconds |
| WebSocket latency (real-time sync) | < 100ms | 500ms |
| Firestore write latency | < 200ms | 1 second |
| Concurrent users per org | ≥ 20 | — |

---

## 14. Error Handling & Edge Cases

### 14.1 Computation Errors

| Error | User Message | System Action |
|---|---|---|
| `SingularMatrixError` (non-invertible A) | "The supply chain model contains a circular dependency that cannot be resolved. Check for duplicate processes." | Return 422; log matrix condition number |
| `AllocationSumError` (factors ≠ 1.0) | "Allocation factors for [process] do not sum to 100%. Please review your allocation inputs." | Prevent calculation; highlight offending process |
| `CutoffViolation` | "Omitted materials exceed the 5% aggregate cut-off threshold. Add the missing data or justify the exclusion." | Block export until resolved |
| `DatasetAgeWarning` (> 10 years) | "The dataset '[name]' is from [year] and exceeds the 10-year reference limit. Consider updating to a more recent dataset." | Non-blocking warning; logged in background report |
| `MatrixDimensionMismatch` | Internal error — do not expose to user | Log to Sentry; return 500 with generic message |

### 14.2 PDF Generation Errors

- If WeasyPrint fails: retry once, then fall back to Playwright
- If both fail: notify user with error detail; preserve all data; allow retry

### 14.3 Concurrent Editing

- Firestore optimistic locking on material documents: `version` field incremented on each write
- If version conflict detected: show "Another team member updated this entry. Review their changes before saving yours."
- WebSocket broadcasts material updates in real-time so conflicts are rare

### 14.4 Large File Imports (BOM CSV/ERP export)

- Maximum import file size: 10 MB
- Supported formats: CSV, XLSX, JSON (BIM IFC subset)
- Async processing with progress indicator
- Validation errors shown in table format: row number · column · error description
- Import does not overwrite existing data — appends only; user confirms before apply

---

## 15. Constraints & Assumptions

### Constraints

1. The ecoinvent v3.10 database is accessed from a pre-ingested, indexed Firestore collection — not via direct ecoinvent API calls. License restrictions apply.
2. PDF generation must be server-side (WeasyPrint/Playwright) — no client-side jsPDF or html2canvas.
3. No third-party AI/LLM calls for LCA calculations — all math is deterministic, implemented in-house.
4. Firebase is the sole auth and primary database provider (no swap to PostgreSQL or Supabase).
5. The characterization matrix Q (EF 3.1) is hardcoded from the official EU JRC dataset — user cannot modify characterization factors.

### Assumptions

1. Users have basic familiarity with their product's BOM (weights, materials, energy consumption at manufacturing stage).
2. The organization has agreed to ecoinvent licensing terms; the platform is not responsible for database licensing.
3. Third-party verifiers are engaged by the customer independently; the platform provides access infrastructure only.
4. Machine-readable export formats (ILCD+EPD, OpenEPD) conform to schemas as of 2025; schema updates require a versioned migration.
5. CBAM reporting format is subject to regulatory change; the XML export template must be versioned and easily replaceable.

### Out of Scope (v1.0)

- Consequential LCA (only attributional LCA is supported)
- Monte Carlo uncertainty analysis (analytical sensitivity only)
- Social LCA (S-LCA)
- Life Cycle Cost (LCC)
- Mobile native applications (iOS/Android)
- Direct EPD program operator API submission (manual upload by user required)

---

*End of Product Requirements Document — EcoMetric v1.0*

*This document is complete and self-contained. An AI agent implementing this PRD should have all specifications needed to build the full application without requesting additional clarification on core requirements.*
