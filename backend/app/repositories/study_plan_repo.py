"""StudyPlan and StudyPlanTask repository."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.study_plan import StudyPlan, StudyPlanTask
from app.repositories.base import BaseRepository


class StudyPlanRepository(BaseRepository[StudyPlan]):
    def __init__(self, db: Session):
        super().__init__(StudyPlan, db)

    def get_by_user(self, user_id: str) -> Optional[StudyPlan]:
        stmt = select(StudyPlan).where(StudyPlan.user_id == user_id)
        return self.db.scalars(stmt).first()

    def get_task(self, task_id: str) -> Optional[StudyPlanTask]:
        return self.db.get(StudyPlanTask, task_id)

    def list_tasks_for_plan(self, plan_id: str) -> List[StudyPlanTask]:
        stmt = (
            select(StudyPlanTask)
            .where(StudyPlanTask.study_plan_id == plan_id)
            .order_by(StudyPlanTask.created_at)
        )
        return list(self.db.scalars(stmt).all())

    def create_task(self, task: StudyPlanTask) -> StudyPlanTask:
        self.db.add(task)
        self.db.flush()
        return task
