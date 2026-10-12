# NIDANA API Contracts Specification

**Version:** 0.2.0 (Locked SQLite + ChromaDB + LangGraph Stack)  
**Base URL:** `/api/v1`

---

## 1. 5-Question Mini-Mock Assessment

### `POST /api/v1/mock/start`
Starts a 5-question bilingual mini-mock for the requested Class Level.
- **Request Body (`MockStartRequest`):**
  ```json
  {
    "class_level": 10,
    "subject_id": "sub_science",
    "language": "bilingual"
  }
  ```
- **Response (`MockSessionResponse`):**
  - **Security Invariant:** Answer keys (`correct_answer`), full teacher explanations, and distractor metadata are strictly stripped.
  ```json
  {
    "session_id": "mock_a1b2c3d4e5f6",
    "class_level": 10,
    "total_questions": 5,
    "total_marks": 20.0,
    "questions": [
      {
        "id": "q_c10_rxn_01",
        "chapter_id": "chap_c10_chem_rxn",
        "concept_id": "cpt_c10_redox",
        "type": "single_choice",
        "difficulty": "easy",
        "marks": 4.0,
        "negative_marks": 1.0,
        "expected_time_seconds": 60,
        "language": "bilingual",
        "stem_en": "In the reaction CuO + H2 -> Cu + H2O, which substance is being reduced?",
        "stem_or": "CuO + H2 -> Cu + H2O ରାସାୟନିକ ପ୍ରତିକ୍ରିୟାରେ କେଉଁ ପଦାର୍ଥଟି ବିଜାରିତ ହେଉଛି?",
        "options": [
          {"id": "A", "text_en": "CuO (Copper oxide)", "text_or": "CuO (କପର ଅକ୍ସାଇଡ୍)"},
          {"id": "B", "text_en": "H2 (Hydrogen)", "text_or": "H2 (ହାଇଡ୍ରୋଜେନ୍)"}
        ]
      }
    ]
  }
  ```

### `POST /api/v1/mock/{session_id}/submit`
Submits student answers for authoritative server-side evaluation.
- **Request Body (`MockSubmitRequest`):**
  ```json
  {
    "answers": [
      {
        "question_id": "q_c10_rxn_01",
        "selected_option": "B",
        "time_taken_seconds": 45,
        "learning_signals": {"answer_changes": 1, "confidence_rating": 3}
      }
    ]
  }
  ```
- **Response (`MockResultResponse`):**
  - Evaluates scores (+4.0 for correct, -1.0 for incorrect).
  - Automatically initializes a persisted `DiagnosticRun` for incorrect answers.
  - Reveals correct answers and bilingual explanations only after submission.
  ```json
  {
    "session_id": "mock_a1b2c3d4e5f6",
    "total_score": -1.0,
    "max_possible_score": 4.0,
    "correct_count": 0,
    "incorrect_count": 1,
    "unanswered_count": 0,
    "results": [
      {
        "question_id": "q_c10_rxn_01",
        "attempt_id": "att_mock_a1b2c3d4e5f6_q_c10_rxn_01",
        "selected_option": "B",
        "is_correct": false,
        "marks_obtained": -1.0,
        "correct_option": "A",
        "explanation_en": "CuO loses oxygen to form Cu, hence it is reduced.",
        "explanation_or": "CuO ରୁ ଅମ୍ଳଜାନ ଅପସାରିତ ହୋଇ Cu ଗଠନ ହୁଏ, ତେଣୁ ଏହା ବିଜାରିତ ହୁଏ ।"
      }
    ],
    "diagnostic_runs_triggered": ["diag_87ab6c54e321"]
  }
  ```

---

## 2. RAG & ChromaDB Pipeline

### `GET /api/v1/rag/health`
Returns readiness of the persistent ChromaDB collection without leaking system filesystem paths.
```json
{
  "status": "healthy",
  "collection": "nidana_curriculum_chunks",
  "indexed_records": 4,
  "embedding_model": "all-MiniLM-L6-v2",
  "dimensions": 384
}
```

### `POST /api/v1/rag/reindex`
Rebuilds the ChromaDB vector index from authoritative SQLite `content_chunks`.

### `POST /api/v1/rag/query`
Executes semantic retrieval with exact curriculum scope pre-filtering.
- **Request Body:**
  ```json
  {
    "query_text": "oxidation and reduction reaction definition",
    "class_level": 10,
    "subject_id": "sub_science",
    "language": "bilingual",
    "top_k": 3
  }
  ```
- **Response:**
  Returns grounded context and citations with source titles, locators, and page numbers.

---

## 3. WHY Engine & Mark Recovery Flow

### `POST /api/v1/diagnosis/run/{attempt_id}`
Executes the LangGraph diagnosis pipeline for an incorrect attempt.
- Evaluates hypotheses (`MISCONCEPTION`, `PREREQUISITE_GAP`, etc.).
- Retrieves 3–5 grounded ChromaDB chunks with provenance.
- Deploys up to 2 targeted diagnostic probes.
- Generates a `RecoveryReport` and schedules a repair task in the student's study plan.

### `POST /api/v1/diagnosis/reports/{report_id}/verify`
Verifies whether mark loss was recovered via follow-up mastery check.
- **Request Body:** `{"is_mastery_correct": true}`
- **Response:**
  ```json
  {
    "report_id": "rep_98f7e6d5",
    "is_verified": true,
    "verified_at": "2026-10-12T17:00:00Z",
    "status": "RECOVERED"
  }
  ```
