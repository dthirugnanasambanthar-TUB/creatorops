import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "creatorops",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL"),
    include=["workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True
)