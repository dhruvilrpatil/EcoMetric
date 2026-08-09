# EcoMetric — Automated, Verified EPD Generation Platform

EcoMetric is an enterprise-grade platform for automated, third-party verifiable Environmental Product Declarations (EPDs) conforming to **ISO 14025**, **ISO 21930**, and **EN 15804+A2**.

---

## 📁 Repository Structure

```
EcoMetric/
├── frontend/               # React + TypeScript + Vite + Tailwind CSS application
│   ├── src/                # UI Pages, components, hooks, state store
│   ├── package.json        # Frontend dependencies & scripts
│   ├── .env.example        # Frontend environment variables template
│   └── README.md           # Detailed frontend development guide
│
├── backend/                # FastAPI + SQLAlchemy + PostgreSQL + Ecoinvent 3.12
│   ├── api/                # REST endpoints
│   ├── app/engine/         # LCA calculation engine & transport scenario
│   └── data/               # SPOLD and background dataset structures
│
├── docker-compose.yml      # Containerized local services (Postgres, Redis)
└── .env.example            # Backend & global environment variables template
```

---

## ⚡ Quick Start: Frontend UI Development

To work directly on the UI without setting up backend databases:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

> [!NOTE]
> The frontend includes a development auth bypass, allowing immediate access to all workflow steps and UI components right after cloning.

For more frontend-specific instructions, see [frontend/README.md](frontend/README.md).

---

## ⚙️ Full-Stack Setup (Frontend + Backend)

### 1. Backend Setup
```bash
# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt  # Or active environment dependencies

# Start FastAPI dev server
uvicorn main:app --reload
```

### 2. Environment Variables
Copy `.env.example` to `.env` in the root and in `frontend/` if you need custom API URLs or live cloud credentials.
