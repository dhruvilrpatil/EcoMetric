from celery_worker import celery_app
from api.nlp import calibrate_confidence_model

@celery_app.task(name="tasks.nlp_tasks.calibrate_nlp_weights_job")
def calibrate_nlp_weights_job() -> dict:
    """
    Celery task to calibrate NLP composite confidence weights
    based on user correctness logs in the database.
    """
    result = calibrate_confidence_model(project_id="00000000-0000-0000-0000-000000000000")
    return {"status": "success", "result": result}
