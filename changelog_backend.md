# NIDANA Backend Changelog

All backend architectural changes, migrations, API contracts, environment updates, and test results are tracked here.

---

## [Initial MVP Backend Foundation] - 2026-10-11

### 1. Files Added & Modified
- **Backend Configuration & Setup:**
  - `backend/.gitignore` — Python, venv, sqlite, and cache exclusions.
  - `backend/.env.example` — Typed environment variable template with placeholders only; never commits secrets.
  - `backend/requirements.txt` — Pinned production and test dependencies.
  - `backend/pyproject.toml` — Standard packaging configuration and pytest options.
  - `backend/README.md` — Complete architecture, setup, migration, and testing guide.
  - `backend/alembic.ini` — Alembic migration config.
  - `changelog_backend.md` — Authoritative backend changelog.
- **Core Layer (`backend/app/core/`):**
  - `config.py` — Strongly typed `Settings` using `pydantic-settings`. Normalizes database URLs, enforces production security (rejecting CORS `*` and insecure JWT secrets).
  - `constants.py` — Controlled enums: `ClassLevel` (9, 10, 12), `UserRole`, `PreferredLanguage`, `ExamTarget`, `QuestionType`, `QuestionDifficulty`, `ApprovalState`, `VariantPurpose`, `AttemptLifecycle`, `TaskStatus`.
  - `errors.py` — Stable machine-readable `APIErrorCode` values and centralized exception handlers for `APIException`, `RequestValidationError`, `HTTPException`, and unhandled errors.
  - `logging.py` — Structured JSON logging with automatic redaction of bearer tokens, passwords, and sensitive keys.
  - `security.py` — Server-side Supabase JWT token verification, expiration check, audience enforcement, `get_current_user` dependency, role checks, and `enforce_ownership()`.
- **Database & Models (`backend/app/db/` & `backend/app/models/`):**
  - `db/base.py` — SQLAlchemy 2.0 `DeclarativeBase` with timezone-aware `TimestampMixin`.
  - `db/session.py` — Engine setup, thread-safe session generator with rollback protection, safe DB health check.
  - `models/user.py` — Learner and educator identity with minimal PII.
  - `models/subject.py` — Stable subject codes and bilingual names.
  - `models/chapter.py` — Class-level constrained chapters (`CheckConstraint("class_level IN (9, 10, 12)")`).
  - `models/concept.py` — Atomic concept nodes with Odia-English terminology mappings and prerequisite IDs.
  - `models/question.py` — `Question` and `QuestionVariant` models with server-only answer keys and distractor metadata.
  - `models/content_chunk.py` — Educational text chunks for approved RAG grounding.
  - `models/attempt.py` — Authoritative attempt records storing computed correctness, marks, and learning signals.
  - `models/study_plan.py` — `StudyPlan` and `StudyPlanTask` models for post-autopsy repair tasks.
- **Schemas (`backend/app/schemas/`):**
  - `common.py` — Uniform `HealthResponse` and `APIErrorResponse` structures.
  - `user.py` — Profile read/update schemas.
  - `subject.py`, `chapter.py`, `concept.py` — Curriculum schemas with ClassLevel validation.
  - `question.py` — `QuestionPublic` (answer keys and explanations strictly stripped for active testing) vs `QuestionWithAnswer` (admin/teacher only).
  - `attempt.py` — `AttemptStartRequest`, `AnswerSubmitRequest` (forbids client score tampering), `AttemptResponse`.
  - `study_plan.py` — Intervention and repair task schemas.
- **Repositories & Services (`backend/app/repositories/` & `backend/app/services/`):**
  - Repositories for all 10 domain entities providing clean data-access separation.
  - `user_service.py` — Token synchronization and profile persistence.
  - `content_service.py` — Syllabus hierarchy and validation.
  - `question_service.py` — Active-test retrieval with answer concealment.
  - `attempt_service.py` — Authoritative server-side grading, negative marking calculation, idempotency protection against resubmission, and ownership verification.
  - `study_plan_service.py` — Intervention tracking.
- **Master API (`backend/app/api/` & `backend/app/main.py`):**
  - `deps.py` — Dependency injection tree.
  - `v1/router.py` & `v1/endpoints/` — Mounted endpoints under `/api/v1` for health, users, subjects, chapters, concepts, questions, attempts, and study plans.
  - `main.py` — FastAPI app with CORS middleware, lifespan logging, centralized error handlers, and OpenAPI documentation.
- **Migrations (`backend/alembic/`):**
  - `versions/0001_initial_schema.py` — Initial migration creating all 10 domain tables, indexes, unique constraints, and foreign keys.
- **Tests (`backend/tests/`):**
  - `conftest.py`, `test_startup.py`, `test_health.py`, `test_config.py`, `test_errors.py`, `test_schemas.py`, `test_auth.py`, `test_questions.py`, `test_attempts.py`, `test_migrations.py`.

---

### 2. Migrations
- `0001_initial_schema.py`:
  - Tables created: `users`, `subjects`, `chapters`, `concepts`, `questions`, `question_variants`, `content_chunks`, `attempts`, `study_plans`, `study_plan_tasks`.
  - Constraints & indexes: Foreign keys on all child entities, check constraint on `chapters.class_level IN (9, 10, 12)`, composite index on `(subject_id, class_level)`, indexes on question difficulty/approval state, and unique indexes on email and codes.

---

### 3. API & Architectural Decisions
1. **Frontend / Backend Boundary:**
   - Frontend: Responsible for UI, local IndexedDB caching (Dexie), offline pack storage, local response capture. Never calculates scores or decides recovery.
   - Backend: Authoritative for identity, permissions, question correctness, marks, persisted records, and sync acceptance.
2. **Answer Key Protection:**
   - Active-test responses return `QuestionPublic`, which strictly omits `correct_answer`, `explanation_en`, `explanation_or`, and `distractor_metadata`.
3. **Deterministic Grading:**
   - Client submission (`POST /api/v1/attempts/{id}/submit`) accepts only learner response representations (e.g. `{"selected_option": "A"}`). Client-supplied scores or correctness values are discarded. The backend evaluates against trusted answer keys, applies marks (+4.0) or negative marks (-1.0), and closes the attempt.
4. **Authentication & Ownership:**
   - Supabase Auth tokens are cryptographically verified server-side using `PyJWT` against `SUPABASE_JWT_SECRET`, checking expiry and audience. Learner attempts and personal records enforce `enforce_ownership()`, rejecting foreign user access with 403 `OWNERSHIP_VIOLATION`.
5. **Class Level Policy:**
   - Validated strictly to `[9, 10, 12]`. Any attempt to request or insert chapters outside these values triggers a validation error (`INVALID_CLASS_LEVEL`).

---

### 4. Environment Requirements
- `APP_ENV`: `development` | `staging` | `production`
- `DATABASE_URL`: PostgreSQL or SQLite connection string.
- `CORS_ORIGINS`: Explicit list of allowed domains; wildcard disallowed in production.
- `SUPABASE_JWT_SECRET`: Secret key for server-side JWT verification.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`: Supabase project metadata.

---

### 5. Tests Executed & Actual Results
- Command: `pytest -v` (executed via `backend\.venv\Scripts\pytest.exe -v`)
- Summary: **22 passed, 0 failed, 4 warnings in 1.54s**
- Test breakdown:
  - `tests/test_startup.py`: 1 passed (App boot & OpenAPI schema)
  - `tests/test_health.py`: 1 passed (Liveness, database readiness, credential concealment)
  - `tests/test_config.py`: 4 passed (Defaults, postgres URL normalization, production CORS guard, production secret guard)
  - `tests/test_errors.py`: 3 passed (404 error envelope, 422 validation structure, safe 500 error sanitization)
  - `tests/test_schemas.py`: 2 passed (Class level 9, 10, 12 validation, public question answer concealment)
  - `tests/test_auth.py`: 5 passed (Missing token, invalid token, expired token, valid token profile sync, role enforcement)
  - `tests/test_questions.py`: 1 passed (Public active-test endpoints strip answer keys and explanations)
  - `tests/test_attempts.py`: 4 passed (Authoritative scoring, negative marking, resubmission rejection, ownership boundary)
  - `tests/test_migrations.py`: 1 passed (Alembic migration upgrade and table reflection)

---

### 6. Unfinished / Deferred Work (Next Phases)
- **WHY Engine / LangGraph:** Diagnostic state machine with probe selection and hypothesis formation (intentionally deferred per prompt constraints).
- **RAG & pgvector:** Vector embeddings on `content_chunks` and semantic retrieval pipelines (deferred until pgvector is provisioned).
- **Offline Pack Generation & Sync:** Idempotent event batch upload (`POST /api/v1/sync/events`) and offline pack serialization (deferred per prompt constraints).
