# NIDANA Workflow

## 1. Purpose

This document defines the end-to-end product workflow and the internal diagnostic workflow. NIDANA's central loop is:

`Attempt → Diagnose → Repair → Replan → Prepare Offline Pack → Verify Recovery`

Build and test one complete loop before expanding breadth.

## 2. Student lifecycle

### A. Sign in and setup
1. Authenticate the student.
2. Load the student's profile, preferred language, exam target, and available offline packs.
3. If the device is shared, show the signed-in account clearly and provide a safe sign-out path.
4. Do not block practice solely because a non-essential profile field is missing.

### B. Choose and start a test
1. Load only published, approved tests that the student can access.
2. Confirm test version, language, time limit, and marking scheme.
3. Create an attempt with status `in_progress`.
4. Cache the test and required variants locally when supported.
5. Record the test/version identifiers so grading remains reproducible even after the bank changes.

### C. Capture each answer
Record the minimum useful evidence:
- attempt/question/version IDs;
- first and final answer;
- answer changes and revisits;
- time spent, using a monotonic client measurement where possible;
- language shown/selected;
- optional confidence response;
- local event ID and timestamp.

Persist locally before showing a durable-save confirmation. Do not trust client correctness or score fields.

### D. Submit and grade
1. Mark the attempt submission event.
2. Server validates attempt ownership, lifecycle, question IDs, and selected options.
3. Grade with the answer key and marking rules for that question version.
4. Calculate score and lost marks deterministically.
5. Store result and return the report inputs.
6. If offline, grade only using the approved local pack's versioned rules and reconcile after sync.

## 3. Diagnostic workflow

### Step 1: Prioritize an error
Choose an important wrong answer based on configured marks, curriculum importance, or recurring evidence. Explain why it was selected. Do not diagnose every trivial event if doing so would overwhelm the learner.

### Step 2: Load context
Collect the attempt signals, question DNA, approved variants, concept prerequisites, relevant prior diagnoses, and outcomes of previous interventions. Respect privacy boundaries and avoid sending unnecessary personal data to the model.

### Step 3: Form competing hypotheses
Potential causes include:
- concept gap;
- English terminology or language friction;
- missing prerequisite;
- time pressure;
- procedural error;
- attention/selection slip;
- mixed cause;
- insufficient evidence.

Each hypothesis should have evidence for, evidence against/limitations, and a confidence or ranking. Avoid treating confidence as a calibrated probability unless calibration has been measured.

### Step 4: Select the next probe
Select the lowest-cost probe likely to distinguish the leading hypotheses. Typical probes:
- language/terminology bridge;
- simplified wording;
- untimed retry;
- prerequisite check;
- distractor reasoning;
- concept transfer;
- explain-back.

Check availability online/offline before selection. A probe must test a meaningful distinction, not merely repeat the same question.

### Step 5: Run probe and capture result
Show one clear action. Store the exact variant ID, language, response, correctness, timing where relevant, and probe version. A missing response is not equivalent to an incorrect response.

### Step 6: Interpret evidence
Update the hypothesis set using the probe result and known limitations. If evidence is confounded, contradictory, or insufficient, remain provisional and choose another probe or stop with uncertainty. Never force verification simply to complete the flow.

### Step 7: Retrieve approved learning support
Query the approved RAG corpus with concept, language, difficulty, prerequisite, and diagnosis metadata. Use only relevant retrieved sources. If no approved support exists, use a reviewed bank explanation or explicitly state that a grounded intervention is unavailable.

### Step 8: Select and validate intervention
Map the supported cause to the smallest repair:
- terminology/language friction → short Odia-English bridge;
- time pressure → timed micro-drills and pacing;
- prerequisite gap → prerequisite explanation and return question;
- concept misconception → short concept repair, worked example, transfer item;
- procedural/selection slip → answer-checkpoint habit;
- mixed cause → ordered short actions, each with a reason.

Validate content, expected outcome, and follow-up before adding it to the plan.

### Step 9: Update study plan
Create or update a task with:
- target weakness/cause;
- evidence and diagnosis reference;
- reason it is recommended;
- estimated duration;
- action/content references;
- expected result;
- due date or suggested sequence;
- follow-up question/probe;
- status and recovery state.

Avoid duplicate active tasks for the same diagnosis unless the new task is intentionally a distinct step.

### Step 10: Prepare offline branch
Package the original question, approved variants, probe rules, remediation material, follow-up question, version IDs, and event schema. Confirm the pack is actually stored locally before showing it as ready.

### Step 11: Verify recovery
At the appropriate later point, present a new approved question that tests the diagnosed weakness. Compare against the defined mastery/recovery rule. Mark the cause `recovered` only when that rule passes. Otherwise keep it active and adjust the intervention.

### Step 12: Report and trace
Show the student:
- what was observed;
- what NIDANA suspected;
- which probe was used and why;
- what the result suggests;
- what action comes next;
- what remains uncertain.

Persist a structured internal trace of node/tool execution, source IDs, validation, retries, fallbacks, and state changes. Do not expose raw private model reasoning.

## 4. Offline workflow

1. Download/build a pack while connected.
2. Validate pack version and content integrity.
3. Store it in IndexedDB.
4. When offline, serve cached tests and variants, record answer events locally, run deterministic grading/rules, and queue sync events.
5. Show accurate offline and queue status.
6. On reconnect, send idempotent events with IDs and schema versions.
7. Server validates and deduplicates, applies events in dependency-safe order, and returns per-event status.
8. Resolve conflicts without deleting local evidence.
9. If server-side AI processing is pending, mark it as pending; do not fabricate a diagnosis.
10. Update the local report after authoritative reconciliation.

## 5. Recommended state machines

### Attempt
`created → in_progress → submitted → graded`

Optional terminal states should be added only if the code needs them (e.g., `cancelled`). Define whether a submitted attempt can ever be reopened; default is no.

### Diagnosis
`not_started → investigating → provisional → verified`

Alternative terminal outcome: `insufficient_evidence`. Recovery state should be modeled separately from diagnostic certainty.

### Intervention / task
`proposed → validated → active → completed → recovery_check_pending → recovered`

Failure/retry states should be explicit. Completing a task does not automatically mean recovered.

### Sync event
`queued → syncing → synced`

Failure branches: `retryable_failed`, `permanent_failed`, or `conflict`. The exact names must match implementation and remain consistent across client/server.

## 6. Workflow failure policy

- If AI is unavailable: run only supported deterministic/cached branches and mark the fallback.
- If no useful probe exists: return provisional/insufficient evidence.
- If RAG is empty: do not invent a lesson or source.
- If generated output fails validation: discard it and fall back to approved content.
- If storage or sync fails: preserve local evidence and make status visible.
- If the student exits mid-flow: restore the last persisted state without duplicating events.
- If a question version is no longer current: grade the attempt against the version actually served.

## 7. MVP acceptance workflow

A demo is complete only when a learner can:
1. sign in;
2. take a five-question Odia/English mini-mock;
3. submit at least one high-value wrong answer;
4. see competing causes and complete two diagnostic probes;
5. receive a supported diagnosis or honest uncertainty;
6. see a Mark Recovery Report;
7. receive one targeted repair task and an updated plan;
8. inspect a real decision trace;
9. continue a prepared diagnostic branch with network disabled;
10. reconnect and sync queued evidence without loss or duplication;
11. answer a new follow-up question and see recovery status updated according to a defined rule.
