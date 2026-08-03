"""
Root-level entry point — allows running uvicorn from G:\EcoMetric.

Usage (from project root):
    uvicorn main:app --reload

Strategy: load backend/main.py by its file path using importlib.util,
giving it a unique internal module name so there is no circular import.
"""

import sys
import importlib.util
from pathlib import Path
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load backend/main.py by path, register it under a unique name
backend_main_path = Path(__file__).resolve().parent / "backend" / "main.py"
backend_dir = backend_main_path.parent

# Add backend/ to sys.path so relative imports inside backend/main.py work
sys.path.insert(0, str(backend_dir))

spec = importlib.util.spec_from_file_location("backend_main", backend_main_path)
_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_mod)

# Re-export the FastAPI app so uvicorn resolves `main:app` to this object
app = _mod.app
