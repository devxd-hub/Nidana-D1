"""Service layer for 5-question mini-mock orchestration and authoritative grading."""

import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.constants import AttemptLifecycle, ClassLevel
from app.core.errors import APIErrorCode, APIException
from app.core.security import AuthenticatedUser
from app.models import Attempt, Chapter, DiagnosticRun, Question
from app.schemas.mock_test import (
    MockAnswerSubmission,
    MockResultResponse,
    MockSessionResponse,
    MockStartRequest,
    MockSubmitRequest,
    QuestionResultOutcome,
)
from app.schemas.question import QuestionPublic


class MockService:
    def __init__(self, db: Session):
        self.db = db

    def start_mini_mock(
        self, user: AuthenticatedUser, payload: MockStartRequest
    ) -> MockSessionResponse:
        """Starts a 5-question mini-mock. Conceals answer keys completely."""
        if payload.class_level not in [c.value for c in ClassLevel]:
            raise APIException(
                code=APIErrorCode.INVALID_CLASS_LEVEL,
                message=f"Class level {payload.class_level} is invalid. Must be 9, 10, or 12.",
                status_code=400,
            )

        query = (
            self.db.query(Question)
            .join(Chapter, Question.chapter_id == Chapter.id)
            .filter(Chapter.class_level == payload.class_level)
        )
        if payload.subject_id:
            query = query.filter(Chapter.subject_id == payload.subject_id)

        questions = query.limit(5).all()

        if len(questions) < 5:
            # Fallback to any 5 approved questions to ensure the mock is always playable
            questions = self.db.query(Question).limit(5).all()

        if not questions:
            raise APIException(
                code=APIErrorCode.RESOURCE_NOT_FOUND,
                message="Insufficient questions available to construct a mini-mock.",
                status_code=404,
            )

        session_id = f"mock_{uuid.uuid4().hex[:12]}"
        public_questions = [QuestionPublic.model_validate(q) for q in questions]
        total_marks = sum(q.marks for q in questions)

        return MockSessionResponse(
            session_id=session_id,
            class_level=payload.class_level,
            questions=public_questions,
            total_questions=len(public_questions),
            total_marks=total_marks,
        )

    def submit_mini_mock(
        self,
        session_id: str,
        user: AuthenticatedUser,
        payload: MockSubmitRequest,
    ) -> MockResultResponse:
        """Authoritatively grades the mini-mock submission and initiates diagnostics for incorrect answers."""
        now = datetime.now(timezone.utc)
        results: List[QuestionResultOutcome] = []
        diagnostic_runs: List[str] = []

        total_score = 0.0
        max_score = 0.0
        correct_count = 0
        incorrect_count = 0
        unanswered_count = 0

        for item in payload.answers:
            question = self.db.query(Question).filter_by(id=item.question_id).first()
            if not question:
                continue

            max_score += question.marks
            correct_opt = (
                question.correct_answer.get("selected_option")
                if isinstance(question.correct_answer, dict)
                else None
            )

            is_correct = False
            marks_awarded = 0.0

            if not item.selected_option:
                unanswered_count += 1
            elif item.selected_option == correct_opt:
                is_correct = True
                marks_awarded = question.marks
                total_score += marks_awarded
                correct_count += 1
            else:
                is_correct = False
                marks_awarded = -question.negative_marks
                total_score += marks_awarded
                incorrect_count += 1

            # Authoritative attempt recording (idempotent lookup or create)
            attempt_id = f"att_{session_id}_{question.id}"
            attempt = self.db.query(Attempt).filter_by(id=attempt_id).first()
            if not attempt:
                attempt = Attempt(
                    id=attempt_id,
                    user_id=user.id,
                    question_id=question.id,
                    lifecycle_state=AttemptLifecycle.SUBMITTED.value,
                    submitted_response={"selected_option": item.selected_option},
                    is_correct=is_correct,
                    marks_obtained=marks_awarded,
                    started_at=now,
                    submitted_at=now,
                    time_taken_seconds=item.time_taken_seconds or 0,
                    learning_signals=item.learning_signals or {},
                )
                self.db.add(attempt)
                self.db.flush()

            # Trigger diagnostic run if answer is incorrect and not already diagnosed
            if item.selected_option and not is_correct:
                existing_run = self.db.query(DiagnosticRun).filter_by(attempt_id=attempt.id).first()
                if not existing_run:
                    diag_run = DiagnosticRun(
                        id=f"diag_{uuid.uuid4().hex[:12]}",
                        attempt_id=attempt.id,
                        user_id=user.id,
                        status="PENDING",
                        primary_hypothesis="MISCONCEPTION",
                        confidence_score=0.8,
                        hypotheses_data=[
                            {
                                "hypothesis": "MISCONCEPTION",
                                "score": 0.8,
                                "reason": f"Selected distractor '{item.selected_option}' instead of expected '{correct_opt}'.",
                            }
                        ],
                        selected_probe_ids=[],
                        evidence_refs=[],
                        trace_summary=f"Diagnostic initiated for question {question.id} on incorrect response {item.selected_option}.",
                        recovery_eligible=True,
                    )
                    self.db.add(diag_run)
                    self.db.flush()
                    diagnostic_runs.append(diag_run.id)
                else:
                    diagnostic_runs.append(existing_run.id)

            results.append(
                QuestionResultOutcome(
                    question_id=question.id,
                    attempt_id=attempt.id,
                    selected_option=item.selected_option,
                    is_correct=is_correct,
                    marks_obtained=marks_awarded,
                    correct_option=correct_opt or "N/A",
                    explanation_en=question.explanation_en,
                    explanation_or=question.explanation_or,
                )
            )

        self.db.commit()

        return MockResultResponse(
            session_id=session_id,
            total_score=total_score,
            max_possible_score=max_score,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            unanswered_count=unanswered_count,
            results=results,
            diagnostic_runs_triggered=diagnostic_runs,
        )
