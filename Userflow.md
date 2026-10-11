# NIDANA User Flow

## 1. Primary persona

An Odia-medium Class 12 learner preparing for a competitive exam, often using a shared Android phone, with limited mobile data and intermittent connectivity. The app must be mobile-first, low-friction, respectful, and useful in Odia without hiding English technical terms needed for exams.

## 2. Main navigation

Use the five destinations described in the UI guide:
- **Home:** next recovery action, meaningful progress, offline/sync state.
- **Practice:** mocks, diagnostic packs, recovery drills.
- **Map:** concept mastery and diagnostic relationships (can be deferred if not implemented).
- **Plan:** daily tasks, reasons, and follow-up checks.
- **Profile:** language, exam target, account/session, offline packs, and progress.

Do not show navigation to a feature that is not implemented. MVP may simplify this navigation while preserving the primary flow.

## 3. Primary journey: from wrong answer to recovery

```text
Open app
  ↓
Sign in / restore session
  ↓
Choose preferred language and exam target (if needed)
  ↓
Home: see “Your next recovery”
  ↓
Start 5-question mini-mock
  ↓
Answer questions; optionally set confidence; switch Odia/English
  ↓
Submit
  ↓
Result summary: score + marks lost
  ↓
Select important wrong answer
  ↓
WHY Engine: show possible causes, not a premature verdict
  ↓
Probe 1: e.g. clarify terminology in Odia
  ↓
Probe 2: e.g. untimed retry / prerequisite / transfer, selected by evidence
  ↓
Diagnosis result: verified, provisional, or insufficient evidence
  ↓
Mark Recovery Report: evidence + uncertainty + next action
  ↓
Complete targeted repair task
  ↓
Study Plan updates with reason and follow-up
  ↓
Download/confirm offline diagnostic pack
  ↓
Later: answer a new recovery question
  ↓
Recovery rule passes? ── Yes → mark recovered
          │
          └── No → keep active and adapt the next repair
  ↓
When online: sync queued evidence and reconcile server state
```

## 4. Screen requirements

### Login / sign-up
- Odia and English labels.
- Clear loading, error, and retry states.
- No secrets or account tokens shown.
- On shared devices, avoid silently retaining another learner's visible private reports.

### Home
- Show one recommended next action and why it matters.
- Show real progress values only; no fabricated recoverable-mark totals.
- Show online/offline and pending-sync state.
- Keep the most important action visible without excessive scrolling.

### Practice / test
- One question per clear interaction, readable options, large touch targets.
- Timer state must be visible and accurate; allow the documented language toggle without losing the answer.
- Capture answer changes and optional confidence without distracting from the test.
- Distinguish “saved on this device” from “synced to account.”
- On refresh or app closure, restore from persisted state where supported.

### Results
- Show score calculated from the actual marking scheme.
- Distinguish lost marks from estimated recoverable marks.
- Do not present a diagnosis as certain before the diagnostic process runs.

### Diagnostic investigation
- Explain why the system is asking each probe in plain language.
- Provide a clear skip/exit path where product policy allows it.
- Keep progress and prior answers when switching language or navigating back.
- Do not reveal raw internal model reasoning or hidden answer keys.

### Mark Recovery Report
- What happened.
- What NIDANA suspects or has verified.
- Evidence from the attempt and probes.
- What remains uncertain.
- The smallest next repair and expected duration.
- The follow-up that will test recovery.
- A clear note that estimated recoverable marks are not guaranteed marks.

### Study Plan
- Every task has a reason, evidence reference, target, action, and follow-up.
- Status changes reflect real events.
- Avoid duplicate active tasks for the same unresolved issue.
- Let the student understand what to do next without needing to interpret technical agent terminology.

### Offline mode
- Show downloaded pack versions and readiness.
- State which features work offline and which require connectivity.
- Show queued, syncing, synced, and failed/conflict statuses (using the implementation's canonical names).
- Do not imply remote AI is running offline.

### Profile
- Language preference, exam target, sign-out/session handling, progress, and pack management.
- Offer safe shared-device behavior and clear account identity.
- Avoid exposing sensitive diagnostic details in public/shared views.

## 5. Offline journey

```text
While online
  ↓
Download an approved diagnostic pack
  ↓
Confirm pack stored locally
  ↓
Network becomes unavailable
  ↓
Open cached test / continue local branch
  ↓
Record answer locally and enqueue stable event IDs
  ↓
Run packaged rules and variants only
  ↓
Show local result and “awaiting sync” if needed
  ↓
Network returns
  ↓
Upload idempotently; server returns per-event result
  ↓
Resolve conflicts and refresh authoritative report
```

If the required question, variant, or rule is not packaged, show an honest unavailable state and preserve progress.

## 6. Key UX states

Every important screen should have:
- loading;
- success;
- empty state;
- validation error;
- network unavailable;
- local save pending/confirmed;
- sync pending/failed/conflict where applicable;
- retry action when useful.

Use color as a supplement, never the only signal. Keep touch targets at least 44×44 CSS pixels where practical, use clear focus states, and test Odia script rendering on actual mobile devices.

## 7. Recovery and uncertainty wording

Preferred:
- “This answer may have been affected by the English term.”
- “The untimed retry suggests time pressure may have contributed.”
- “We need one more check before confirming the cause.”
- “You completed the repair. Let's test it with a new question.”
- “Your recovery estimate is based on the evidence available so far.”

Avoid:
- “You are weak at Physics.”
- “The AI knows exactly why you failed.”
- “You will recover 4 marks for sure.”
- “You have mastered this” after one repeated question.
- Any status that claims sync, save, or recovery before it actually succeeds.

## 8. MVP flow checklist

- [ ] Sign-in works.
- [ ] Five-question mock works in Odia/English.
- [ ] Wrong answer produces candidate causes.
- [ ] Two probes run and record outcomes.
- [ ] Report distinguishes evidence and uncertainty.
- [ ] One targeted task is created and plan updates.
- [ ] Trace shows actual decisions.
- [ ] A prepared branch works offline.
- [ ] Sync restores evidence without loss/duplication.
- [ ] A new question verifies or fails recovery according to a defined rule.
