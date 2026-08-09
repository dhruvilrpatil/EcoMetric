# EcoMetric Frontend

Automated, verified Environmental Product Declaration (EPD) platform built with React, TypeScript, Vite, Tailwind CSS, and TanStack Query.

---

## 🚀 Quick Start for UI Development

You can run and work on the frontend UI locally in **less than 2 minutes** without setting up Firebase or the backend database.

### 1. Prerequisites
- **Node.js** 18+ or 20+
- **npm** (or `pnpm` / `yarn`)

### 2. Install Dependencies
```bash
cd frontend
npm install
```

### 3. Start Development Server
```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

> [!TIP]
> **Dev Auth Bypass**: In development mode, the frontend automatically initializes a mock user session (`dev@ecometric.test`). You can immediately navigate and design any page without needing Firebase accounts or login credentials.

---

## ⚙️ Environment Configuration (Optional)

If you need custom API URLs or live Firebase integration:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Adjust environment variables:
   - `VITE_API_BASE_URL`: URL of the FastAPI backend (`http://localhost:8000/api/v1` by default).
   - `VITE_FIREBASE_*`: Your Firebase project credentials (only needed if testing live Firebase production auth).

---

## 🧭 Page & Route Directory

All pages are located in `src/pages/` and structured per the ISO 14025 / EN 15804+A2 EPD workflow:

| Route | Component | Description |
|---|---|---|
| `/` | `LandingPage.tsx` | Marketing and product overview landing page |
| `/login`, `/register` | `LoginPage.tsx`, `RegisterPage.tsx` | Authentication pages |
| `/dashboard` | `DashboardPage.tsx` | User workspace, stats, and project list |
| `/projects/new` | `ProjectSetupPage.tsx` | Step 1: Functional unit, PCR, and system boundaries |
| `/projects/:id/inventory` | `InventoryPage.tsx` | Step 2: Bill of Materials (BOM) & LCI matching |
| `/projects/:id/transportation` | `TransportationPage.tsx` | Step 3: Module A4 transport logistics scenario |
| `/projects/:id/calculate` | `CalculatePage.tsx` | Step 4: LCA calculation engine trigger & status |
| `/projects/:id/hotspots` | `HotspotsPage.tsx` | Step 5: Contribution analysis, charts & Pareto breakdown |
| `/projects/:id/export` | `ExportPage.tsx` | Step 6: Pre-export verification & EPD PDF generation |
| `/projects/:id/publish` | `PublishPage.tsx` | Step 7: Verifier review workflow & token generation |
| `/portfolio` | `PortfolioPage.tsx` | Multi-product portfolio benchmarking |
| `/verifier/:token` | `VerifierPage.tsx` | Third-party verifier audit portal |
| `/settings` | `SettingsPage.tsx` | User profile & organization preferences |

---

## 🧱 Design System & Components

Located in `src/components/` following atomic design:

- **Atoms (`src/components/atoms/`)**: `Button`, `TextInput`, `BadgeTag`, `Select`, etc.
- **Molecules (`src/components/molecules/`)**: `ProductCard`, `CalloutStat`, `NotificationCard`, etc.
- **Organisms (`src/components/organisms/`)**: `AppLayout`, `PrimaryNav`, `ProjectNav` (step progress bar).

Styling is configured in `tailwind.config.ts` using custom tokens (`colors.primary`, `surface-soft`, `hairline`, `spacing`, `typography`).

---

## 🛠️ Available Scripts

- `npm run dev`: Starts local Vite dev server with Hot Module Replacement (HMR).
- `npm run build`: Type-checks and builds the production bundle into `dist/`.
- `npm run type-check`: Runs TypeScript compiler check (`tsc --noEmit`).
- `npm run lint`: Runs ESLint across the codebase.
- `npm run preview`: Previews the built production bundle locally.
