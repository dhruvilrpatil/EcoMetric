"""
tasks/pdf_generate.py — Celery task for async WeasyPrint PDF generation.
Stub for Phase 5 — full implementation uses WeasyPrint server-side.
"""
from celery_worker import celery_app


@celery_app.task(bind=True, name="tasks.pdf_generate.generate_pdf_job")
def generate_pdf_job(self, project_id: str, export_id: str, doc_type: str) -> dict:
    """
    Async PDF generation job using WeasyPrint (server-side only).
    No jsPDF, no html2canvas — PRD critical rule.
    Full implementation in Phase 5.
    """
    return {"status": "complete", "export_id": export_id, "doc_type": doc_type}
