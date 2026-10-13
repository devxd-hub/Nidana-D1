"""Service layer for offline packs and idempotent event synchronization."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.constants import ApprovalState, AttemptLifecycle
from app.core.security import AuthenticatedUser
from app.models import (
    Attempt,
    Chapter,
    Concept,
    ContentChunk,
    Question,
    SyncReceipt,
)
from app.schemas.question import QuestionPublic
from app.schemas.sync import (
    ContentPackBundle,
    ContentPackManifest,
    SyncBatchRequest,
    SyncBatchResponse,
    SyncEvent,
    SyncEventResult,
)


class SyncService:
    def __init__(self, db: Session):
        self.db = db

    def list_packs(self) -> List[ContentPackManifest]:
        """Lists available offline content packs across curriculum tiers."""
        now = datetime.now(timezone.utc)
        manifests = [
            ContentPackManifest(
                pack_id="pack_c10_sci_v1",
                class_level=10,
                subject_id="sub_science",
                language="bilingual",
                version="1.0.0",
                content_version="2026.1",
                checksum="f4c2e1a9b8d7",
                generated_at=now,
                item_counts={"chapters": 2, "concepts": 2, "questions": 10, "chunks": 3},
            ),
            ContentPackManifest(
                pack_id="pack_c9_motion_v1",
                class_level=9,
                subject_id="sub_science",
                language="bilingual",
                version="1.0.0",
                content_version="2026.1",
                checksum="e3b1c9a8d2f5",
                generated_at=now,
                item_counts={"chapters": 1, "concepts": 1, "questions": 5, "chunks": 1},
            ),
            ContentPackManifest(
                pack_id="pack_c12_optics_v1",
                class_level=12,
                subject_id="sub_physics",
                language="bilingual",
                version="1.0.0",
                content_version="2026.1",
                checksum="c9a8b7d6e5f4",
                generated_at=now,
                item_counts={"chapters": 1, "concepts": 1, "questions": 5, "chunks": 1},
            ),
        ]
        return manifests

    def get_pack_bundle(self, pack_id: str) -> ContentPackBundle:
        """Assembles a bounded, self-contained offline bundle.

        Answer keys are strictly stripped to prevent test compromise.
        """
        now = datetime.now(timezone.utc)
        class_level = 10
        if "c9" in pack_id:
            class_level = 9
        elif "c12" in pack_id:
            class_level = 12

        # Fetch curriculum items for this class level
        chapters = self.db.query(Chapter).filter(Chapter.class_level == class_level).all()
        chapter_ids = [c.id for c in chapters]

        concepts = self.db.query(Concept).filter(Concept.chapter_id.in_(chapter_ids)).all()
        concept_ids = [c.id for c in concepts]

        questions = (
            self.db.query(Question)
            .filter(
                Question.chapter_id.in_(chapter_ids),
                Question.approval_state == ApprovalState.APPROVED.value,
            )
            .all()
        )
        chunks = (
            self.db.query(ContentChunk)
            .filter(
                ContentChunk.chapter_id.in_(chapter_ids),
                ContentChunk.approval_state == ApprovalState.APPROVED.value,
            )
            .all()
        )

        public_questions = [QuestionPublic.model_validate(q) for q in questions]

        manifest = ContentPackManifest(
            pack_id=pack_id,
            class_level=class_level,
            subject_id=chapters[0].subject_id if chapters else None,
            language="bilingual",
            version="1.0.0",
            content_version="2026.1",
            checksum=hashlib.sha256(pack_id.encode()).hexdigest()[:16],
            generated_at=now,
            item_counts={
                "chapters": len(chapters),
                "concepts": len(concepts),
                "questions": len(public_questions),
                "chunks": len(chunks),
            },
        )

        return ContentPackBundle(
            manifest=manifest,
            chapters=[{"id": c.id, "title_en": c.title_en, "title_or": c.title_or, "chapter_number": c.chapter_number} for c in chapters],
            concepts=[{"id": cp.id, "name_en": cp.name_en, "name_or": cp.name_or, "code": cp.code} for cp in concepts],
            questions=public_questions,
            learning_chunks=[
                {
                    "id": ch.id,
                    "title": ch.source_title,
                    "locator": ch.source_locator,
                    "language": ch.language,
                    "text": ch.text_content,
                }
                for ch in chunks
            ],
            offline_rules={
                "evaluation_mode": "deferred_authoritative_server_sync",
                "local_diagnostics": "supported_deterministic_probes_only",
                "max_probes_per_session": 2,
            },
        )

    def process_sync_batch(
        self, user: AuthenticatedUser, payload: SyncBatchRequest
    ) -> SyncBatchResponse:
        """Processes client offline events with strict idempotency and duplicate deduplication."""
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        results: List[SyncEventResult] = []
        accepted = 0
        duplicate = 0
        rejected = 0

        for event in payload.events:
            # 1. Idempotency check against existing SyncReceipts
            receipt = self.db.query(SyncReceipt).filter_by(client_event_id=event.client_event_id).first()
            if receipt:
                duplicate += 1
                results.append(
                    SyncEventResult(
                        client_event_id=event.client_event_id,
                        status="DUPLICATE",
                        server_receipt_id=receipt.id,
                        message="Event was already processed previously. Replaying existing receipt.",
                        processed_data=receipt.details,
                    )
                )
                continue

            # 2. Process new event based on event_type
            payload_str = json.dumps(event.payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()
            receipt_id = f"rcpt_{uuid.uuid4().hex[:12]}"

            if event.event_type == "ATTEMPT_SUBMIT":
                q_id = event.payload.get("question_id")
                selected_opt = event.payload.get("selected_option")
                question = self.db.query(Question).filter_by(id=q_id).first() if q_id else None

                if not question:
                    rejected += 1
                    results.append(
                        SyncEventResult(
                            client_event_id=event.client_event_id,
                            status="REJECTED",
                            message=f"Question '{q_id}' not found on server.",
                        )
                    )
                    continue

                # Server-authoritative scoring
                correct_opt = (
                    question.correct_answer.get("selected_option")
                    if isinstance(question.correct_answer, dict)
                    else None
                )
                is_correct = selected_opt == correct_opt if selected_opt else False
                marks = question.marks if is_correct else (-question.negative_marks if selected_opt else 0.0)

                attempt_id = f"att_sync_{event.client_event_id}"
                attempt = Attempt(
                    id=attempt_id,
                    user_id=user.id,
                    question_id=question.id,
                    lifecycle_state=AttemptLifecycle.SUBMITTED.value,
                    submitted_response={"selected_option": selected_opt},
                    is_correct=is_correct,
                    marks_obtained=marks,
                    started_at=event.client_timestamp,
                    submitted_at=now,
                    time_taken_seconds=event.payload.get("time_taken_seconds", 0),
                    learning_signals=event.payload.get("learning_signals", {}),
                )
                self.db.add(attempt)

                processed_info = {
                    "attempt_id": attempt_id,
                    "is_correct": is_correct,
                    "marks_obtained": marks,
                }

                # Record sync receipt
                new_receipt = SyncReceipt(
                    id=receipt_id,
                    client_event_id=event.client_event_id,
                    user_id=user.id,
                    event_type=event.event_type,
                    payload_hash=payload_hash,
                    status="ACCEPTED",
                    details=processed_info,
                    processed_at=now,
                )
                self.db.add(new_receipt)
                accepted += 1

                results.append(
                    SyncEventResult(
                        client_event_id=event.client_event_id,
                        status="ACCEPTED",
                        server_receipt_id=receipt_id,
                        message="Attempt processed and saved authoritatively.",
                        processed_data=processed_info,
                    )
                )

            else:
                # Other generic telemetry or probe events
                new_receipt = SyncReceipt(
                    id=receipt_id,
                    client_event_id=event.client_event_id,
                    user_id=user.id,
                    event_type=event.event_type,
                    payload_hash=payload_hash,
                    status="ACCEPTED",
                    details=event.payload,
                    processed_at=now,
                )
                self.db.add(new_receipt)
                accepted += 1
                results.append(
                    SyncEventResult(
                        client_event_id=event.client_event_id,
                        status="ACCEPTED",
                        server_receipt_id=receipt_id,
                        message="Event accepted.",
                        processed_data=event.payload,
                    )
                )

        self.db.commit()

        return SyncBatchResponse(
            batch_id=batch_id,
            accepted_count=accepted,
            duplicate_count=duplicate,
            rejected_count=rejected,
            event_results=results,
        )
