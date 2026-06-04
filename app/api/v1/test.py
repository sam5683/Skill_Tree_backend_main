# app/api/v1/test.py

from fastapi import APIRouter

from app.tasks.test_task import add

router = APIRouter()


@router.get("/celery-test")
def celery_test():

    task = add.delay(
        5,
        10
    )

    return {
        "task_id": task.id
    }