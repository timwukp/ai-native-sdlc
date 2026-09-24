# Intent: add mentor-led and self-paced learning paths

- **Slug:** mentor-self-paced-modes
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Date:** 2026-09-24
- **Status:** draft
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/14

## Problem

The portal currently exposes one reading path. Its six stage tabs organize the curriculum, but they
do not distinguish two materially different learning jobs:

- a mentor needs a bounded 45–60 minute facilitation route, explicit objectives, suggested pacing,
  questions to ask, and failure scenarios to demonstrate;
- a self-paced learner needs a clear start or resume point, visible progress, concise recaps, short
  checks, and a deliberate way to mark work complete and return later.

The existing single quiz does not establish stage-level understanding or progress. The page also has
no browser-local persistence. Adding separate copies of the curriculum for each audience would create
two sources of truth and allow explanations, claims, accessibility text and governance guidance to
drift.

## Desired outcome

One canonical six-stage curriculum supports two explicit projections:

1. **Mentor mode** presents a 45–60 minute teaching route with stage objectives, suggested timing,
   discussion prompts, demonstration prompts, and previous/next presentation controls.
2. **Self-paced mode** presents Start/Continue, explicit stage completion, progress, recap, one short
   scenario check per stage, Resume and Reset Progress.

Mode-specific guidance augments rather than duplicates the canonical stage content. Self-paced state
stays entirely in the browser, contains no learner-authored content, and is never transmitted. If
storage or JavaScript is unavailable, the complete curriculum remains readable and the missing
enhancements are explained honestly.

## Affected users / systems

- Mentors facilitating a live workshop from a laptop or projected display.
- Individual learners using phones, tablets or laptops across several visits.
- Keyboard-only, screen-reader, reduced-motion and print users.
- The existing six-stage tab interface and quiz behavior in `index.html`.
- `verify.py`, which must enforce mode structure, canonical-content integrity, storage limits,
  progressive enhancement and accessibility contracts.
- Existing Portal, privacy and SDLC workflows, which must remain green.

## Constraints

- Preserve one canonical instance of every stage explanation. Mode views may add metadata and prompts
  but must not copy the stage curriculum into parallel mentor/self-paced sections.
- Keep the portal as one dependency-free `index.html` with inline CSS and JavaScript, no build step,
  account, analytics, server, runtime request or external asset.
- Browser persistence is local-only and minimal. Do not store quiz answers, free text, names, email,
  timestamps, analytics identifiers or content copied from the page.
- Storage access can throw or be unavailable. The page must fail safely, remain operable in-memory,
  and avoid claiming progress was saved when it was not.
- Completion is explicit user intent. Do not infer completion from scrolling, time-on-page, opening a
  panel or selecting a quiz answer.
- Reset Progress is a destructive local action and requires a clear confirmation before deleting
  saved state.
- JavaScript-disabled rendering exposes all six canonical stage panels, figures, tables, lab,
  limitations and sources. A noscript explanation identifies only the unavailable mode/progress
  enhancements.
- Maintain the responsive contracts shipped in PR #11: no page overflow at 360px, 768px, 1024px or
  1440px; at least 44px compact targets; local table/code overflow; bounded diagrams.
- Maintain semantic tabs, visible focus, skip navigation, labeled regions, status announcements and
  logical keyboard order. Mode controls must not create a second conflicting tab system.
- `prefers-reduced-motion` remains respected. Progress and mode changes must not require animation to
  convey state.
- Print renders the complete canonical curriculum with useful mentor prompts and no misleading
  interactive progress controls.
- Preserve current source attribution, governance claims, honest limitations and the 75,000-byte
  page budget unless a signed-off specification explicitly demonstrates that a small increase is
  necessary.
- Existing privacy scanning remains active. Rendered evidence and fixtures must not contain personal
  data, local machine paths or credential-shaped values.
- The agent does not push, accept its own artifacts, approve the PR or merge.

## Success criteria

1. A prominent, keyboard-accessible mode control exposes Mentor and Self-paced without hiding access
   to the canonical course.
2. The DOM contains exactly one canonical set of six stage panels. Both modes reference and augment
   those panels rather than cloning their content.
3. Mentor mode provides a total suggested duration within 45–60 minutes and, for every stage, at
   least one objective, discussion prompt and demonstration/failure prompt.
4. Mentor previous/next controls update the selected canonical stage, preserve focus semantics and
   expose position within the six-stage route.
5. Self-paced mode provides Start/Continue, current position, completed-stage progress, explicit
   Mark Complete behavior, Resume and Reset Progress.
6. Every stage has a concise recap and one scenario-based check with accessible feedback. A check may
   inform learning but does not silently mark a stage complete.
7. Saved state uses one versioned, namespaced local-storage record containing only the approved
   minimal fields. Invalid, unknown-version or malformed data is ignored or safely reset.
8. Storage success, unavailable storage and reset outcomes are announced accurately. No state leaves
   the browser and no runtime network request is introduced.
9. With JavaScript disabled, all six panels and essential supporting content are visible and the
   noscript message accurately describes unavailable enhancements.
10. Keyboard-only users can choose a mode, navigate stages, answer checks, mark completion, resume
    and initiate/cancel/confirm reset with visible focus and meaningful announcements.
11. Both modes have no page-level horizontal overflow at 360px, 768px, 1024px and 1440px. Mentor
    prompts, progress UI and checks remain readable without overlapping existing figures or tables.
12. Print, reduced-motion and existing diagram typography guarantees continue to pass.
13. Verification is added red-first and proves mode semantics, single-source content, storage schema,
    storage-failure fallback, no-JavaScript behavior, reset confirmation, keyboard contracts and
    absence of network/analytics code.
14. Existing 262 Portal checks, privacy tests/mutations/full-tree scan and SDLC gate remain green.
15. Rendered evidence covers Mentor and Self-paced at 360px, 768px and 1440px plus keyboard-only,
    JavaScript-disabled, storage-disabled, reduced-motion, print and console checks.
16. After merge, an artifact-only pull request marks this chain shipped before Playbook coverage PR 3
    begins.

## Recommended decisions awaiting owner acceptance

1. **First-visit route:** default to Self-paced with both mode choices always visible; restore the
   last selected mode only when the minimal saved record is valid.
2. **Completion model:** require an explicit Mark Stage Complete action. Quiz correctness and viewing
   activity never change completion automatically.
3. **Persistence schema:** store only schema version, selected mode, current stage id and completed
   stage ids in one namespaced `localStorage` record. Do not store answers, text or timestamps.
4. **Mentor state:** navigation is session-only except for the shared selected-mode/current-stage
   fields; Mentor mode does not write completion progress.
5. **Knowledge checks:** add one scenario-based check and concise explanation per stage without a
   cumulative score or certificate.
6. **Reset behavior:** use an in-page confirm/cancel dialog with focus return, not `window.confirm`,
   and announce the successful local reset.
7. **Verification route:** use an isolated Playwright context against an immutable commit URL for
   both modes and storage/no-storage cases; mutable branch-preview bytes are not accepted evidence.

---
Gate: product owner accepts. The accepting commit is the record.
