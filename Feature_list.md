# NIDANA Feature List

## 1. Product definition

NIDANA is an Odia-first, bilingual, offline-first learning companion for Class 12 competitive-exam aspirants. It helps learners understand **why** important marks were lost, repairs the supported cause, and checks whether the learner can now solve a new question.

**Core promise:** diagnose before recommending, repair the smallest supported gap, and verify recovery.

## 2. Scope labels

- **MVP:** required for the first credible end-to-end hackathon demonstration.
- **Next:** valuable after the core loop is reliable.
- **Later:** explicitly deferred to prevent scope creep.

## 3. MVP features

| Feature | Priority | Expected behavior / acceptance condition |
|---|---|---|
| Sign-in and learner profile | MVP | Student can sign in; language and exam target are stored; private records are access-controlled |
| Odia/English mini-mock | MVP | A five-question test can be completed in either supported language or a mixed mode |
| Question DNA | MVP foundation | Every question has concept, answer key, marks, difficulty, expected time, language variants, and distractor metadata where available |
| Deterministic grading | MVP | Server or approved offline rules calculate correctness and marks; client cannot submit authoritative scores |
| Attempt signal capture | MVP | Selected answer, timing, answer changes, language, confidence when enabled, and revisit signals are recorded |
| WHY Engine | MVP | Produces competing hypotheses and selects a discriminating probe; does not infer a verified cause from one wrong answer alone |
| Diagnostic probe library | MVP | At least two suitable probes run for the demo, using approved question variants |
| Diagnosis status and evidence | MVP | Diagnosis shows observations, probe result, evidence, limitations, and provisional/verified state |
| Mark Recovery Report | MVP | Shows marks lost, estimated recoverable marks with caveats, likely causes, next action, and follow-up |
| Targeted intervention | MVP | One validated repair task is created from the supported cause |
| Living study plan | MVP | Plan updates from diagnosis and contains reason, evidence source, target, action, and follow-up |
| Agent decision trace | MVP | Student-readable summary and internal trace record actual workflow events, not fabricated “thinking” |
| Offline diagnostic pack | MVP | Preloaded questions/variants/rules permit a defined diagnostic branch without network |
| Local persistence and sync queue | MVP | Attempts/events survive refresh and connectivity loss; sync is idempotent and status is visible |
| Recovery check | MVP | A new suitable follow-up question determines whether recovery criteria pass |

## 4. Diagnostic and learning features

| Feature | Priority | Description |
|---|---|---|
| Mark-Loss Autopsy / “Why did I lose this mark?” | MVP | Explains the observed error and tests competing causes |
| Counterfactual probe library | MVP | Language, terminology, simplified wording, untimed retry, prerequisite, distractor, transfer, explain-back |
| Causal Error Map | Next | Tracks likely and verified causes over time; preserves evidence and uncertainty |
| Learner Diagnostic Graph | Next | Connects concepts, prerequisites, language friction, prior errors, and intervention outcomes |
| Error Replay | Next | Replays the original response and diagnostic sequence |
| Adaptive Question Generation | Next | Produces targeted candidate questions, subject to strict validation and approval |
| Personalized Mock Generator | Next | Builds diagnostic, recovery, language-friction, speed, confidence, or full exam simulations |
| Event-driven replanning | Next | Replans after meaningful new evidence, repeated errors, missed tasks, or approaching exam |
| Autonomous Study Agent | Next | Selects next task within bounded policies, with traceable reasons and user control |
| Follow-up scheduler | Next | Schedules targeted review and recovery checks |
| Exam-readiness estimate | Next | Directional view across concept mastery, language comfort, timing, and consistency; never a guaranteed score |

## 5. Language and regional support

| Feature | Priority | Description |
|---|---|---|
| Odia-first UI | MVP | Core flows, buttons, feedback, and reports can be understood in Odia |
| English mode | MVP | Student can practice English exam terminology |
| Mixed-language mode | MVP | Odia explanations can preserve English technical terms needed in exams |
| Human-reviewed glossary | MVP foundation | Maintains approved subject terminology mappings |
| Terminology bridge | MVP | Tests and repairs English-term friction without unnecessarily reteaching the concept |
| Translation quality workflow | Next | Machine translation is reviewed; corrections and provenance are retained |
| Odia voice input/output | Later | Only after real-device and real-speaker quality testing |
| Additional regional languages | Later | Do not expand before Odia and English quality is reliable |

## 6. Offline features

| Feature | Priority | Description |
|---|---|---|
| Installable PWA | MVP | Can be installed on supported mobile browsers |
| Cached tests and question variants | MVP | Approved pack content is available offline |
| Local attempt recording | MVP | Answer events persist locally through refresh and network loss |
| Local objective grading | MVP | Uses versioned answer rules included in the pack |
| Rule-based offline diagnosis | MVP | Runs only diagnostic branches supported by packaged rules and variants |
| Event queue and reconnect sync | MVP | Stable IDs, schema versions, deduplication, bounded retry, visible status |
| Smart cache and pack management | Next | Prioritizes relevant content while respecting storage/data limits |
| On-device AI inference | Later | Out of initial MVP; do not claim it exists without implementation |

## 7. Reporting and gamification

| Feature | Priority | Description |
|---|---|---|
| Recovery-focused home | MVP | Shows the next useful action and meaningful learning progress |
| Mark Recovery Report | MVP | Explains causes, evidence, repair, and verification |
| Recovery Points | Next | Award only for meaningful repair plus successful follow-up, not app opens |
| Investigation streak | Next | Encourages consistency without punitive streak loss |
| Concept mastery map | Next | Shows concept-level progress with accessible non-color-only cues |
| Language Bridge Level | Next | Measures demonstrated comfort with exam terminology |
| Pacing badge | Later | Award only after evidence of timed performance improvement |
| Four-part readiness indicator | Next | A preparation signal, not a score guarantee |

## 8. Teacher and operations features

| Feature | Priority | Description |
|---|---|---|
| Teacher dashboard | Later | Class trends and evidence-backed interventions with strict student privacy |
| Content review/admin tools | Next | Approve questions, glossary terms, RAG sources, and generated candidates |
| Agent observability | MVP engineering | Trace graph nodes, tool calls, source IDs, validation, retries, fallbacks, and recovery outcomes |
| Feedback and correction reporting | Next | Let learners/teachers flag incorrect explanations or translations |

## 9. Explicitly out of MVP scope

- Full teacher analytics dashboard.
- Large-scale content ingestion pipeline.
- Voice-based Odia interaction or automatic speech generation.
- On-device generative AI.
- Fully autonomous unbounded multi-step agents.
- Advanced adaptive difficulty modeling.
- Languages beyond Odia and English.
- Building all feature ideas before the complete mark-recovery loop works.

## 10. Release principle

A feature is not “done” because its screen exists. It is done when:
1. its data contract and authorization are defined;
2. its primary and failure paths work;
3. offline behavior is honest and tested where applicable;
4. outputs are validated;
5. evidence and traceability exist;
6. tests cover its acceptance conditions;
7. student-facing wording is accessible in Odia/English.
