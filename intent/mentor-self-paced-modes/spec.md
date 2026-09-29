# Spec: two learning modes over one canonical curriculum

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** shipped

## Measured baseline

The merged responsive portal is one 62,917-byte `index.html` with:

- one ARIA tablist controlling exactly six canonical `.panel` tabpanels;
- all six panels visible in source, then five hidden progressively by JavaScript;
- six scenario questions held in one JavaScript `QUESTIONS` array and rendered into one empty
  `#quiz` container;
- no Mentor or Self-paced mode control;
- no stage timing, mentor objective, discussion prompt, demonstration prompt or stage recap;
- no progress UI and no `localStorage` or `sessionStorage` use;
- a noscript message that only describes the current global self-check;
- responsive, keyboard, reduced-motion, print, privacy and governance controls already enforced by
  262 Portal checks.

The existing six questions align one-to-one with the six lifecycle stages closely enough to remain
one canonical question set. This change relocates each rendered question into its corresponding
stage rather than writing a second set for Self-paced mode.

The current 75,000-byte cap leaves 12,083 bytes. Two mode controls, twelve mode-guidance blocks,
storage/error/reset behavior, shared navigation/progress controls, accessible feedback and their CSS
are expected to require 16–18KB even after reusing the existing questions and panels. This spec
therefore raises the enforceable `index.html` cap to **85,000 bytes**. It does not permit dependencies,
external assets, duplicated curriculum or unrelated content expansion.

## Requirements

### One canonical curriculum

1. Keep exactly one lifecycle tablist and exactly six canonical stage panels with ids `p1` through
   `p6`. Do not create parallel Mentor and Self-paced copies of a panel, stage explanation, figure,
   table, source or honest limitation.
2. Give each canonical panel one stable semantic stage id from `plan`, `design`, `build`, `test`,
   `deploy`, `maintain`. Storage and mode metadata use these ids rather than DOM position alone.
3. Add mode-specific guidance inside or adjacent to each canonical panel using explicit attributes
   equivalent to `data-mode-content="mentor"` and `data-mode-content="self-paced"`. These blocks
   augment the panel; they do not restate its canonical explanation.
4. Without JavaScript, both kinds of guidance and all six panels are visible in source order. Script
   adds the enhancement state that selects one mode and one current panel.

### Mode selection

5. Add one prominent mode chooser before the lifecycle stage controls. It contains exactly two
   buttons: Mentor and Self-paced. Use one accessible group label and `aria-pressed` state; do not
   introduce a second ARIA tablist.
6. Both mode choices remain visible in both modes, have at least the existing 44px compact target,
   retain visible focus and expose the selected mode without relying on color alone.
7. On a first valid JavaScript visit, select Self-paced. When a valid saved record exists, restore
   its selected mode and current stage. An invalid record never overrides the default.
8. Changing mode preserves the selected canonical stage, updates `aria-pressed`, updates visible
   mode-specific guidance and announces the mode change through one polite live region.

### Mentor mode

9. Every stage has exactly one Mentor guide containing:
   - a suggested duration in whole minutes;
   - at least one concise learning objective;
   - at least one question the mentor can ask;
   - at least one failure or demonstration prompt.
10. The six suggested durations total between 45 and 60 minutes. Verification reads and sums the
    machine-readable duration values instead of trusting a prose total.
11. One shared Mentor control bar shows `Stage N of 6` and provides Previous and Next buttons. It
    operates the existing lifecycle tab selection; it does not maintain another stage state.
12. Previous is disabled at Stage 1 and Next is disabled at Stage 6. A control activation selects
    the canonical stage, updates the existing tab semantics and moves focus to the selected panel
    heading or panel without causing a keyboard trap.
13. Mentor navigation may persist the shared selected mode/current stage fields, but it never adds,
    removes or rewrites completed-stage progress.

### Self-paced mode

14. Show one shared Self-paced progress region containing Start/Continue wording, current stage,
    completed count, a native progress element or equivalent accessible value, Mark Stage Complete
    and Reset Progress.
15. Completion changes only when the learner activates Mark Stage Complete or confirms Reset.
    Selecting a stage, scrolling, elapsed time, opening a detail, answering a question or choosing
    the correct answer never changes completion automatically.
16. Mark Stage Complete is idempotent. Repeating it does not duplicate an id or raise the completed
    count above six. The action announces the new count through the shared polite live region.
17. Every stage has exactly one concise recap and one mount point for its corresponding scenario
    question. The six existing questions and explanations remain the single question source and are
    each rendered exactly once into the matching canonical panel.
18. Question state remains in memory only. Do not save selected answers, correctness, score or
    feedback. Returning to a stage in the same page session may preserve its in-memory answer state;
    reload may reset it.
19. The existing Self-check navigation destination becomes a course-check/progress summary or index
    that points learners to the six stage checks. It must not render a duplicate seventh copy of any
    question.

### Local-only state

20. Use one namespaced key: `ai-native-sdlc.learning.v1`.
21. The serialized object contains exactly these fields:

```json
{
  "version": 1,
  "mode": "self-paced",
  "currentStage": "plan",
  "completedStages": []
}
```

    `mode` is `mentor` or `self-paced`; `currentStage` is one of the six semantic ids;
    `completedStages` is a unique subset of those ids. No additional field is permitted.
22. Never persist a name, email, free text, quiz answer, correctness, score, timestamp, duration,
    user/device identifier, analytics value, page content or URL.
23. Parse and validate every loaded field before use. Malformed JSON, non-object data, unknown schema
    versions, unknown fields, invalid modes/stages, duplicate completions or wrong field types are
    ignored as one invalid record and replaced only after a later explicit state-changing action.
24. Wrap storage read, write and remove operations. If access throws or is unavailable, retain
    in-memory operation, show `Progress is available for this session only`, and never claim a save
    succeeded.
25. The page performs no network request, beacon, analytics call, form submission or cross-origin
    synchronization. Progress never leaves the browser.

### Reset confirmation

26. Reset Progress opens one in-page modal dialog with a clear title, consequence, Cancel and Reset
    buttons. Do not call `window.confirm`, `alert` or `prompt`.
27. Opening the dialog moves focus inside it; Cancel and Escape leave state unchanged; confirmed
    reset clears only the namespaced learning key, restores the default Self-paced/Plan/zero-complete
    state, announces success and returns focus to the initiating control.
28. The reset control remains operable in the storage-unavailable fallback and resets in-memory
    state without claiming persistent storage was cleared.

### Progressive enhancement and accessibility

29. Preserve panels visible in markup. JavaScript may hide non-selected panels only after the
    enhancement class/state is applied.
30. Replace the current noscript statement with an accurate explanation: all curriculum, Mentor
    guides, Self-paced recaps, figures, tables, lab, limitations and sources remain visible; mode
    switching, interactive checks and saved progress require JavaScript.
31. Mode, navigation, progress, completion, check and dialog controls use native buttons or native
    dialog/progress semantics where available, accessible names, visible focus and at least 44px
    compact targets.
32. Use a single polite live region for mode, stage, completion, storage and reset announcements.
    Static instructions and visible labels carry the meaning; announcements do not become the only
    source of state.
33. Preserve the existing tab ArrowLeft/ArrowRight/Home/End behavior. Clicking shared Mentor or
    Self-paced navigation updates the same tabs and panels, not a hidden parallel index.
34. Respect `prefers-reduced-motion`. Mode/stage/progress state cannot depend on animation.

### Responsive and print behavior

35. At 360px, 768px, 1024px and 1440px neither mode introduces page-level horizontal overflow.
    Mode buttons, Mentor controls, progress, completion, recap, checks and dialog fit or wrap within
    the existing responsive content box.
36. Compact mode controls use one or two intentional columns without truncating Mentor or Self-paced
    labels. Progress text and buttons wrap without reducing touch targets.
37. Figures remain 298px compact/360px wide with effective type between 12px and 18px. Existing
    table/code local overflow and Hero/header gutters remain unchanged.
38. Print hides mode switching, progress mutation, reset, quiz option buttons and shared navigation
    controls. It prints all six canonical panels, every Mentor guide, every Self-paced recap, figures,
    captions, tables, lab, honest limits and sources on the existing light print theme.
39. Print does not claim completion state or show a stale interactive score. Stage checks may print
    their stem/explanation only if the output remains meaningful without an interactive answer.

### Deterministic verification

40. Extend `verify.py` before implementation. The red run must fail for absent mode/progress/storage/
    dialog/guidance contracts while all existing 262 checks remain green; missing implementation is
    reported as named findings, not a traceback.
41. Add a dedicated `learning modes` verifier group that checks:
    - one mode group, two choices, correct labels and `aria-pressed` contract;
    - exactly six canonical panels and no duplicated panel/stage ids;
    - six Mentor guides with objective/question/demo markers and a 45–60 minute total;
    - six Self-paced recaps and six unique question mount points;
    - one shared Mentor control bar, progress region, live region and reset dialog;
    - exact storage key, schema version, four-field allowlist and forbidden-field absence;
    - explicit completion events and no completion calls from tab/scroll/time/quiz handlers;
    - storage validation/error fallback and no `window.confirm`/alert/prompt;
    - no-JavaScript and print contracts;
    - continued absence of runtime network/analytics code.
42. The static verifier must not claim to prove dynamic behavior. Playwright evidence separately
    exercises persistence across reload, malformed records, storage exceptions, reset cancel/confirm,
    keyboard focus and both learning modes.
43. Existing privacy unit tests, privacy mutation proof, tracked-tree scan, Portal checks and SDLC
    gate remain green. New test text uses only reserved/synthetic identities and no host-local data.
44. Preserve current source claims, question meanings, figure accessibility, governance wording and
    honest limitations. Any copy change is reviewed as learning guidance, not silently mixed with
    unrelated Playbook expansion.
45. Raise the verifier page-size cap from 75,000 to exactly 85,000 bytes. A later change cannot raise
    it again without a newly accepted intent/spec.

### Rendered evidence

46. Capture Mentor and Self-paced at 360px, 768px and 1440px from an immutable commit URL. Record
    `scrollWidth`/`clientWidth`; screenshots without overflow readings are incomplete evidence.
47. Keyboard evidence covers mode switching, existing stage tabs, Mentor Previous/Next, Self-paced
    Mark Complete, all six checks, Reset dialog Cancel/Escape/Confirm and visible focus return.
48. Persistence evidence starts from empty storage, completes at least two non-adjacent stages,
    reloads, restores mode/current/completions, resets, reloads again and proves only default state
    remains.
49. Invalid-storage evidence covers malformed JSON, unknown version, extra field, invalid stage and
    duplicate completion. Storage-disabled evidence forces get/set/remove to throw and proves the
    page remains usable with an honest session-only message.
50. JavaScript-disabled evidence confirms all six panels, six Mentor guides, six Self-paced recaps,
    three figures, two tables, lab, honest limits and sources are visible, with the enhanced-only
    features accurately disclosed.
51. Reduced-motion, print and console evidence remain separate. Console must contain zero warnings,
    errors and page errors in both valid-storage and storage-disabled runs.
52. The pull request stays Draft until all rendered evidence is attached or recorded. Static source
    inspection does not satisfy the Human Deploy Gate.

## Non-functional requirements

- **Accessibility:** semantic controls, one tab system, visible focus, 44px targets, accurate pressed/
  disabled/progress/dialog states, polite announcements and complete no-JavaScript content.
- **Privacy:** approved four-field local record only; no identity, answers, timestamps, analytics or
  network egress; storage failure is explicit.
- **Performance:** one dependency-free page, no external asset/request, synchronous state below a few
  hundred bytes, and no polling or timer loop.
- **Weight:** `index.html` is at most 85,000 bytes; the increase is exclusively for accepted learning
  modes and their verification-friendly semantics.
- **Compatibility:** standard DOM, `localStorage`, buttons, progress and dialog with a documented
  fallback where needed; no framework, module loader or build step.
- **Maintainability:** semantic stage ids and one state/render path; no duplicated curriculum,
  question bank or navigation model.
- **Truthfulness:** progress is local and best-effort, completion is user-declared, checks are
  formative, and no score/certificate implies mastery.
- **Evidence:** dynamic storage/accessibility claims require Playwright against immutable bytes.

## Design

### 1. Mode shell

Place one `.learning-modes` region before the existing lifecycle tablist. Two ordinary buttons carry
`data-mode-choice` and `aria-pressed`; they are not tabs. A visible description explains Mentor as a
facilitation route and Self-paced as local progress. A single live region follows the shared controls.

JavaScript applies `data-learning-mode` to the document after loading/validating state. CSS hides only
the non-selected mode guidance when this attribute exists. Without it, both guidance types display.

### 2. Stage metadata

Add `data-stage` to each existing panel and matching tab. Each panel receives:

- one static Mentor guide with `data-minutes`, objective, ask and demonstrate markers;
- one static Self-paced block with a recap and one empty question mount keyed to that stage.

The canonical stage heading, explanation, comparison, artifact, gate, evidence and measure remain in
the same panel and are not copied into either mode block.

### 3. Shared state and controls

Use one in-memory object matching the four-field serialized schema. Existing `select(tab)` becomes the
only stage-selection function and updates tab/panel state, Mentor position, Self-paced position and
`currentStage`. Mentor Previous/Next and Self-paced Continue invoke it.

A Set-backed completion helper changes only `completedStages` when Mark Stage Complete is activated.
Rendering derives progress value/count and button state from the validated in-memory object.

### 4. Question placement

Keep one six-entry question array. Add a stable stage id to each entry and render it exactly once into
the matching Self-paced mount. The existing click/feedback logic remains formative and in-memory.
The course Self-check section becomes an index/summary rather than a second render target.

### 5. Storage boundary

`loadLearningState`, `validateLearningState`, `saveLearningState` and `clearLearningState` isolate the
storage boundary. Validation rejects unknown keys as well as invalid values. Storage exceptions set a
session-only flag and visible status; UI actions continue against memory.

No code serializes quiz state. No storage event, beacon, fetch, form action or remote endpoint is used.

### 6. Reset dialog

Use one native `<dialog>` with Cancel and Reset actions and explicit focus return. If modal-dialog APIs
are unavailable, an accessible non-modal fallback exposes the same controls and consequence without
calling browser-native confirm/alert/prompt.

### 7. Print and no-JavaScript

Default markup is the complete readable document. Enhanced screen CSS selects one mode; print CSS
overrides selection to show Mentor guides and Self-paced recaps while hiding mutation controls and
option buttons. Noscript text names precisely what is unavailable.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| Two modes could create two copies of the curriculum | Content owner | Keep exactly six canonical panels; mode blocks contain metadata/prompts only; verifier counts both. |
| Progress can be mistaken for measured mastery | Learning owner | Completion is explicitly learner-declared; formative checks produce no persisted score or certificate. |
| Local storage can fail or be blocked | Privacy owner | Validate and catch every boundary operation; retain in-memory use and display a session-only message. |
| Saved state could become a tracking record | Privacy owner | One namespaced object with exactly four non-identity fields; reject extra fields; no timestamps or network. |
| Reset destroys learner state | Product owner | In-page dialog requires confirm/cancel, supports Escape and returns focus. |
| A second mode tabset could conflict with lifecycle tabs | Accessibility owner | Mode chooser uses pressed buttons in one labeled group, never `role=tab`. |
| Questions could be duplicated between panels and Self-check | Content owner | One array, one stage id per entry, one mount per stage, one render per question. |
| Moving checks could hide content without JavaScript | Accessibility owner | Question interaction remains enhanced-only, but all canonical content plus recaps/guides is static and visible. |
| New controls could regress compact layout | Design owner | Both modes require 360/768/1440 captures plus four-width overflow readings. |
| 75KB is insufficient for accepted scope | Repository owner | Raise once to 85KB from a measured 62,917-byte baseline; no dependency or unrelated expansion. |
| Static checks could overclaim storage/accessibility proof | Repository owner | Keep PR Draft until Playwright executes valid, invalid, unavailable-storage, keyboard, no-JS, print and console cases. |
| Mutable preview may serve stale code | Repository owner | Final evidence uses the immutable commit-SHA URL only. |

## Rejected alternatives

- Separate Mentor and Self-paced copies of every stage; a second ARIA tablist; inferred completion
  from scroll/time/quiz; persisted answers/scores/timestamps; accounts or cloud sync; analytics;
  `window.confirm`; certificates; external state libraries; service workers; URL-encoded progress;
  raising the cap to 100KB without measurement; treating static verifier output as rendered proof.

## Out of scope

- Expanding the Portal to every play in the source Playbook, glossary work or terminology-map changes
  reserved for PR 3.
- A complete worked example or assessment redesign beyond one formative scenario check per stage,
  reserved for PR 4.
- Cross-device sync, user accounts, analytics, instructor dashboards, cohorts, certificates,
  localization, server APIs or database storage.
- Fixing commit-metadata privacy scanning tracked in Issue #12.
- Changes to privacy rules, SDLC gate, branch protection, workflows or deployment infrastructure.

---
Gate: owner signs off; flagged concerns worked first. Applied org skill: `ai-native-sdlc`.
