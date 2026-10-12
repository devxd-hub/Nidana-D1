# NIDANA Backend Changelog

All backend architectural changes, migrations, API contracts, environment updates, and test results are tracked here.

---

## [Locked v2 Architecture: SQLite Hardening, ChromaDB, Offline Sync & LangGraph WHY Engine] - 2026-10-12

### 1. Scope & Stack Alignment (Prompts 1 – 6)
- **Stack Lockdown:** Replaced legacy Supabase/PostgreSQL/pgvector runtime reliance with a local-first, highly reliable foundation:
  - **Relational Core:** SQLite (via SQLAlchemy 2.x + Alembic) with WAL mode, foreign keys enforced on connection, and a 5000ms busy timeout.
  - **Vector Retrieval:** ChromaDB persistent client managing rebuildable curriculum chunks with exact pre-filters.
  - **Diagnostic Agent:** LangGraph StateGraph orchestrating hypothesis formulation, probe selection (max 2), grounded evidence retrieval, and Mark Recovery Report generation.
  - **LLM Integration:** Isolated Gemini adapter with deterministic fallback heuristics ensuring tests run offline without network access or live credentials.
  - **Client Offline Synchronization:** Bounded content pack distribution and idempotent batch event synchronization with conflict deduplication via `sync_receipts`.

### 2. Files Added & Modified
- **Documentation & Configuration:**
  - `docs/TECH_STACK.md` — Authoritative component matrix, responsibilities, and data boundaries.
  - `docs/backend-state-audit.md` — Initial repository audit, component inventory, and migration risks.
  - `docs/api-contracts.md` — Complete endpoint contracts for mini-mock, RAG, and diagnosis workflows.
  - `docs/offline-sync.md` — Specification for offline packs, client Dexie separation, and sync receipts.
  - `backend/.env.example` — Documented environment variables for SQLite, ChromaDB, Gemini, and optional Langfuse.
  - `backend/requirements.txt` & `backend/pyproject.toml` — Added `chromadb>=1.5.0` and `langgraph>=1.2.0`, removed Postgres binaries.
  - `.gitignore` (root & backend) — Added strict exclusions for local database files, vector store data, and prompt instruction files.
- **Database & Migrations:**
  - `backend/app/db/session.py` — Engine setup with SQLite connect listener executing `PRAGMA foreign_keys=ON;`, `PRAGMA journal_mode=WAL;`, `PRAGMA busy_timeout=5000;`.
  - `backend/alembic/versions/0002_diagnosis_and_sync_schema.py` — Migration adding `diagnostic_runs`, `diagnostic_probes`, `recovery_reports`, `sync_receipts`, and `content_chunks` provenance fields.
  - `backend/app/models/diagnostic.py` — `DiagnosticRun`, `DiagnosticProbe`, and `RecoveryReport` domain models.
  - `backend/app/models/sync_receipt.py` — `SyncReceipt` domain model for idempotency ledger.
  - `backend/app/models/content_chunk.py` — Provenance extensions (`source_locator`, `checksum`, `class_level`, `subject_id`).
  - `backend/app/db/seed_demo_data.py` — Seeder populating 25 reviewed bilingual questions across Class 9, 10, and 12 with approved content chunks.
- **Mini-Mock & Assessment:**
  - `backend/app/schemas/mock_test.py` — `MockStartRequest`, `MockSessionResponse`, `MockSubmitRequest`, and `MockResultResponse`.
  - `backend/app/services/mock_service.py` — 5-question mini-mock orchestration, answer key concealment, server-side grading, and diagnosis triggering.
  - `backend/app/api/v1/endpoints/mock_exam.py` — `/api/v1/mock/start` and `/api/v1/mock/{session_id}/submit`.
- **RAG & ChromaDB:**
  - `backend/app/rag/embedding.py` — Pinned 384-dimensional embedding adapter with deterministic projection fallback.
  - `backend/app/rag/chroma_client.py` — Persistent ChromaDB store wrapper with SQLite reconciliation (`rebuild_from_sqlite`), metadata pre-filters, and keyword fallback.
  - `backend/app/rag/provenance.py` — Structured citation and grounded context formatter.
  - `backend/app/api/v1/endpoints/rag.py` — `/api/v1/rag/health`, `/api/v1/rag/reindex`, and `/api/v1/rag/query`.
- **Offline Content Packs & Sync:**
  - `backend/app/schemas/sync.py` — `ContentPackManifest`, `ContentPackBundle`, `SyncEvent`, and `SyncBatchResponse`.
  - `backend/app/services/sync_service.py` — Pack assembler (omitting answer keys) and idempotent batch processing engine.
  - `backend/app/api/v1/endpoints/sync.py` — `/api/v1/sync/packs`, `/api/v1/sync/packs/{id}`, and `/api/v1/sync/batch`.
- **LangGraph WHY Engine:**
  - `backend/app/why_engine/gemini_adapter.py` — Provider adapter with bounded hypotheses scoring and explanation generation.
  - `backend/app/why_engine/graph.py` — LangGraph diagnosis StateGraph (`evaluate_attempt` -> `retrieve_rag_evidence` -> `formulate_hypotheses` -> `select_probes` -> `generate_recovery_report`).
  - `backend/app/why_engine/service.py` — Execution coordinator and recovery verification manager.
  - `backend/app/api/v1/endpoints/diagnosis.py` — `/api/v1/diagnosis/run/{attempt_id}`, `/api/v1/diagnosis/reports/{report_id}`, and `/api/v1/diagnosis/reports/{report_id}/verify`.
- **Test Suite:**
  - `backend/tests/test_sqlite_hardening.py` — Tests for foreign keys enforcement, session rollback, and unique constraints.
  - `backend/tests/test_mock_test.py` — Tests for mini-mock answer key concealment and authoritative grading.
  - `backend/tests/test_rag.py` — Tests for ChromaDB health, SQLite re-indexing, and curriculum query filters.
  - `backend/tests/test_sync.py` — Tests for offline pack bundle structure and idempotent duplicate handling.
  - `backend/tests/test_why_engine.py` — Tests for diagnostic graph execution and mark recovery verification loop.

### 3. Tests Executed & Actual Results
- **Command:** `pytest backend/tests -v` (executed via `backend\.venv\Scripts\pytest.exe`)
- **Result:** **32 passed, 0 failed, 4 warnings in 2.37s**
- **Test Coverage Summary:**
  - 4 attempt scoring & ownership tests
  - 5 authentication & role verification tests
  - 4 configuration validation tests
  - 3 centralized error handling tests
  - 1 database health check test
  - 1 Alembic multi-version migration upgrade test
  - 2 mini-mock answer concealment & scoring tests
  - 2 public question representation tests
  - 2 curriculum schema validation tests
  - 3 SQLite PRAGMA & rollback hardening tests
  - 1 app boot & OpenAPI startup test
  - 2 ChromaDB RAG health & query tests
  - 2 offline pack download & duplicate sync tests
  - 1 LangGraph WHY Engine diagnosis & mark recovery verification test

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
