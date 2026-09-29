# Plan: enforce one curriculum, then add two state-safe learning projections

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** f00c07837c40f407848cfa040b4eea886a78d70c
- **Status:** accepted

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time. It binds review to protected
`main` after the responsive closeout, not to this branch's artifact commits.

## Files changed (in order of work)

1. `.sdlc/active` — already points at `mentor-self-paced-modes`.
2. `intent/mentor-self-paced-modes/intent.md` — accepted Stage 1 artifact linked to Issue #14.
3. `intent/mentor-self-paced-modes/spec.md` — signed-off learning-mode, accessibility, storage and
   evidence contract.
4. `intent/mentor-self-paced-modes/plan.md` — this implementation plan and merge-base binding.
5. `verify.py` — red-first `learning modes` checks, canonical-content markers, storage/schema
   assertions, no-JavaScript/print contracts and the accepted 85,000-byte cap.
6. `index.html` — mode chooser, six Mentor guides, six Self-paced recaps/check mounts, shared
   controls, local-only state, reset dialog, CSS and progressive-enhancement JavaScript.

Explicitly unchanged: README, privacy scanner/hooks/allowlist, all GitHub workflows, PR template,
branch protection, figures and their text/geometry, table contents, source links, every shipped chain,
and Issue #12's commit-metadata scanner scope.

No Playwright script or screenshot is committed. Short verification scripts and rendered captures use
the session's isolated output/scratch area and immutable public commit URL.

## Work order

### A. Accept the plan and establish the red contract

1. **Reconfirm state.** Verify intent is accepted, spec is signed off, Build gate is open, merge base
   equals `Accepted-for`, privacy scan is clean, Portal baseline is 262/262, local Git identity is the
   established GitHub noreply identity, and `.kiro/settings/` is the only unrelated untracked data.
2. **Accept this plan.** The owner replaces `pending`/`draft`, commits acceptance, and the Test gate
   must open before `verify.py` or `index.html` changes.
3. **Add a dedicated verifier group.** Implement `learning_mode_checks(html, page)` and call it from
   `main()` after existing responsive checks and before figure checks. The group must emit named
   findings when markup is absent; it must not throw because implementation does not exist.
4. **Assert the single-source model.** Require exactly one lifecycle tablist, six tabs, six canonical
   panels and semantic stage ids `plan`, `design`, `build`, `test`, `deploy`, `maintain`. Require all
   added guidance nodes to carry `data-learning-addition`; reject a second mode tablist or duplicate
   panel/stage id.
5. **Assert mode and Mentor contracts.** Require one labeled mode group, exactly two pressed-state
   buttons, Self-paced default, six Mentor guides, integer duration metadata totaling 45–60 minutes,
   and one objective/ask/demonstrate marker per guide. Require one shared Mentor Previous/Next bar
   and one position output rather than controls duplicated in every panel.
6. **Assert Self-paced contracts.** Require one progress region, one accessible progress value,
   Continue, Mark Complete and Reset actions; exactly six recaps; exactly six unique question mounts;
   and one canonical six-entry question array mapped to all six semantic stage ids.
7. **Assert storage and reset boundaries.** Require the exact key `ai-native-sdlc.learning.v1`, schema
   version 1, the four allowed field names, explicit rejection of unknown keys/invalid values, wrapped
   get/set/remove operations, session-only fallback text, one dialog with Cancel/Reset, focus return,
   and no `window.confirm`, `alert` or `prompt`.
8. **Assert explicit completion.** Require completion mutation to be bound only to Mark Complete and
   confirmed Reset code paths. Reject completion writes in tab, scroll, timer and question-answer
   handlers by checking isolated named functions/handlers rather than a bare token count.
9. **Assert progressive enhancement and print.** Require both guidance kinds visible by default,
   selection only under an applied learning-mode attribute/class, accurate noscript wording, one
   polite live region, mode/progress controls hidden in print, and all guides/recaps/canonical panels
   visible in print.
10. **Assert privacy/weight/isolation.** Reject persisted field names for answer, correctness, score,
    timestamp, duration, identity or analytics; retain existing no-fetch/XHR/import checks; change
    only the page-size expectation from 75,000 to exactly 85,000 bytes.
11. **Observe the red run.** `python3 verify.py` must fail only with named `learning modes` findings
    plus the old 75KB-cap expectation being intentionally replaced. Existing governance, privacy,
    structure, isolation, content, honesty, responsive and figure checks remain green.
12. **Commit the red verifier alone.** Record actual check/failure counts. Do not add placeholder
    implementation just to reduce the red count.

### B. Add semantic markup and mode content

13. **Add mode CSS.** Define compact mode-choice layout, pressed state, Mentor/Self-paced guide cards,
    shared control bars, progress/status, check mounts and dialog. Consume `--touch-target`, existing
    colors and focus-visible conventions. Add no fixed page width or new breakpoint unless rendered
    evidence proves the existing 48rem/64rem rules insufficient.
14. **Preserve progressive enhancement.** Base CSS displays both `data-mode-content` values. Only a
    JavaScript-applied `data-learning-mode` attribute hides the non-selected guidance. Print overrides
    the attribute to expose Mentor guides and Self-paced recaps while hiding mutation controls.
15. **Add one mode shell.** Before the lifecycle tabs, add one `data-learning-addition` region with
    Mentor and Self-paced buttons, visible descriptions, one shared polite live region and the shared
    Mentor/Self-paced control regions. Buttons use `aria-pressed`; no second `role=tablist` is added.
16. **Annotate the canonical controls.** Add matching semantic `data-stage` ids to the six existing
    tabs and panels without changing their ids, labels, ordering or canonical text.
17. **Add six Mentor guides.** In each canonical panel add one `data-learning-addition` Mentor guide
    with duration, objective, ask and demonstrate fields. Select concise prompts specific to the
    existing stage content. Choose integer times totaling 50 minutes unless copy review shows a
    clearer 45–60-minute allocation.
18. **Add six Self-paced blocks.** In each panel add one `data-learning-addition` recap that summarizes
    but does not contradict the canonical section and one stage-keyed empty question mount. Do not
    copy the panel's full explanation, lists, diagrams or tables.
19. **Transform the Self-check section.** Preserve its heading/navigation target and existing six
    question meanings. Replace the one global render target with a progress/check index that points
    to the six stage panels and an accurate noscript explanation. Do not render a duplicate question.
20. **Add one reset dialog.** Place it once near the shared learning shell or end of main. Include a
    clear consequence, Cancel and Reset buttons, focusable semantics and no form/network action.

### C. Implement one state/render path

21. **Define stable data.** Add one `STAGES` array for six semantic ids/tabs/panels and add a `stage`
    field to each existing question entry. Keep each existing question/options/correct index/
    explanation unchanged and render each entry once into its matching mount.
22. **Isolate state validation.** Implement `defaultLearningState`, `validateLearningState`,
    `loadLearningState`, `saveLearningState` and `clearLearningState`. Validation requires exactly
    four keys, schema 1, valid mode/stage, array type, unique valid completions and no unknown key.
23. **Handle storage honestly.** Wrap each storage operation in `try/catch`. On any failure set a
    one-way session-only flag, continue against memory, display the fallback message and suppress all
    later claims that state was saved. Do not log the record or exception contents.
24. **Use one stage selector.** Extend existing `select(tab, options)` as the only panel-selection
    path. It updates tabs/panels, current semantic stage, Mentor position, Self-paced position and
    optional focus. Stage clicks and Arrow/Home/End use the same function.
25. **Render mode state.** `setMode(mode)` validates the mode, applies the root/document attribute,
    updates both pressed states and shared controls, persists only approved state and announces the
    visible mode. First load defaults to Self-paced unless a valid record restores another mode.
26. **Implement Mentor controls.** Previous/Next find the adjacent `STAGES` entry and call `select`.
    Boundary buttons are disabled correctly. Mentor navigation never mutates `completedStages`.
27. **Implement explicit completion.** Mark Complete inserts the current stage id into a unique set,
    serializes it in stage order, updates progress/count/button text, persists approved state and
    announces the count. No question or viewing event calls this function.
28. **Render six checks once.** For each existing question, locate the matching mount and build the
    current accessible question/options/status markup there. Keep answered/correct counters only if
    their label remains accurate; do not persist them or use them to complete a stage.
29. **Implement reset dialog behavior.** Opening records the invoking control and moves focus into
    the dialog. Cancel/Escape closes without mutation. Confirm clears only the learning key, restores
    Self-paced/Plan/zero-complete memory state, updates all controls, announces reset and restores
    focus. Provide the signed-off non-modal fallback when `showModal` is unavailable.
30. **Initialize once.** Parse storage once, choose valid/default state, apply enhancement/mode, render
    questions, select current stage and update controls. Do not add timers, polling, history routing,
    URL progress or network code.

### D. Prove static behavior and preserve prior content

31. **Green Portal verification.** Run `python3 verify.py`; every new learning-mode finding and all
    prior checks pass. Output prints Mentor duration total, canonical panel/question counts, storage
    field count and current page bytes.
32. **Prove canonical text preservation.** Mark every new Mentor/Self-paced/mode/reset node with
    `data-learning-addition`. Parse `origin/main:index.html` and the new page with the same stdlib
    extractor; remove addition subtrees from the new page, normalize whitespace, and require the
    remaining pre-existing text to match except the signed-off Self-check/noscript transformation.
    Review that small exception explicitly rather than allowing a broad text mismatch.
33. **Prove question preservation.** Extract all six current question stems, options, correct indexes
    and explanations from `origin/main:index.html`; require the new array to match those values in
    order, with only the accepted semantic `stage` field added.
34. **Run all repository checks.** Privacy unit tests, privacy mutation proof, full tracked-tree scan,
    Portal verifier, SDLC CI gate, Python compilation and `git diff --check` all pass. Stage intended
    files before the full-tree privacy scan so new content is actually included.
35. **Inspect the diff.** Every path is listed in this plan. `index.html` changes only accepted CSS,
    mode/guide/recap/control/dialog markup, question placement metadata and learning-state script.
    Figures, tables, source URLs, governance/privacy files and shipped chains have zero diff.
36. **Measure weight.** `index.html` is no more than 85,000 bytes. Report actual increase and largest
    sections. Do not minify existing canonical prose to manufacture room.
37. **Commit implementation separately.** Red verifier history precedes the implementation commit.
    Any test correction discovered after implementation receives its own explanation and must not
    weaken the signed-off contract.

### E. Publish a Draft PR and execute real behavior

38. **Exercise the real pre-push hook.** Simulate all outgoing commits with the checked-in hook and
    confirm tree privacy. Separately inspect author/committer metadata until Issue #12 ships, using
    the configured GitHub noreply identity.
39. **Owner pushes the named branch.** The agent does not run `git push`. After remote SHA matches,
    create a Draft PR linked to Issue #14 with red/green evidence and the remaining rendered gate.
40. **Use immutable rendered bytes.** After the green commit is public, load its full commit-SHA URL
    in an isolated Playwright Chromium context. Do not use the mutable branch preview as evidence.
41. **Capture both modes.** At 360px, 768px and 1440px capture Mentor and Self-paced (six screenshots)
    and record `scrollWidth/clientWidth`. At 1024px record overflow metrics. Inspect mode chooser,
    controls, prompts, progress, recaps, checks, existing tables/figures and dialog.
42. **Keyboard-only run.** Starting from reload, exercise first focus/skip link, mode buttons, existing
    tab Arrow/Home/End, Mentor Previous/Next, Self-paced Continue/Mark Complete, one correct and one
    incorrect check, Reset open/Cancel/Escape/Confirm, and focus return. Record active element and
    visible focus at each boundary.
43. **Persistence run.** Clear the namespaced key, verify default Self-paced/Plan/zero progress,
    complete Plan and Test, switch to Mentor on Test, reload, and require restored mode/stage/two
    completions. Return to Self-paced, confirm reset, reload, and require default/zero state.
44. **Invalid-state matrix.** In fresh contexts inject malformed JSON, unknown version, extra field,
    invalid mode, invalid stage, wrong completion type and duplicate completion. Each must load the
    safe default without console errors and without treating the record as valid.
45. **Storage-disabled run.** Before page script, make storage get/set/remove throw. Verify mode/stage,
    checks, completion and reset remain operable in memory; the session-only message is visible; no
    success copy claims persistence; console/page errors remain zero.
46. **Progressive/print runs.** With JavaScript disabled, verify six panels, six Mentor guides, six
    recaps, three figures, two tables, lab, limits and sources visible plus accurate noscript text.
    Emulate reduced motion. Emulate print and verify all panels/guides/recaps visible, mutation controls
    hidden, no clipping and successful PDF generation.
47. **Update PR evidence.** Record engine, immutable SHA, metrics, screenshots and observed behavior.
    Keep PR Draft until all checks above and required GitHub checks are green.
48. **Required checks.** `portal verify`, `privacy scan`, and `sdlc-gate / sdlc-gate` all conclude
    `SUCCESS`; no new required context is added by this PR.
49. **Mark ready and hand off.** Only after static, dynamic and CI evidence is complete, mark Ready.
    The owner reviews and merges; the agent neither approves nor merges.
50. **Verify publication and close.** Confirm Pages serves the merge, repeat core mode/storage/console
    smoke checks on the public URL, then open an artifact-only closeout PR marking this chain shipped
    before Playbook coverage PR 3 begins.

## Tests that prove it

### Red target

```sh
python3 verify.py
```

Pass condition for the red phase: non-zero with only named `learning modes` findings. Existing 262
checks stay green; no ImportError, parser traceback or implementation placeholder is accepted.

### Green local targets

```sh
python3 verify.py
python3 -m unittest discover -s scripts -p 'test_privacy*.py'
python3 scripts/privacy_mutation_proof.py
python3 scripts/privacy_scan.py --repo .
python3 -m py_compile verify.py scripts/privacy_scan.py scripts/privacy_pretooluse_hook.py
git diff --check
```

Run the installed SDLC CI gate with `--require-active`, the real changed-file list and base SHA
`f00c07837c40f407848cfa040b4eea886a78d70c`.

Quantified pass conditions:

- Portal verifier exits 0 with a non-zero expanded check count;
- exactly six canonical panels, Mentor guides, recaps and question mounts;
- Mentor duration sum is 45–60 minutes;
- exactly two mode choices and four persisted fields;
- all six original question definitions are semantically unchanged and rendered once;
- 31 privacy tests pass and 10/10 current privacy mutants are killed;
- staged full-tree privacy scan reports 0 findings;
- SDLC gate reports `verify.py` and `index.html` named in this plan;
- `index.html` bytes are no more than 85,000;
- canonical pre-existing text comparison passes with only the reviewed Self-check/noscript exception;
- commit author/committer use the established GitHub noreply identity;
- `.kiro/settings/` remains unstaged.

### Static learning-mode cases

- mode group count/label/button/pressed-state contract;
- one lifecycle tablist and six canonical semantic stages;
- six uniquely keyed Mentor guides with 45–60-minute sum;
- objective/ask/demonstrate marker per stage;
- six recaps and six unique question mounts;
- one shared Mentor bar, Self-paced progress region, live region and reset dialog;
- exact storage key/schema/four fields and explicit invalid-state rejection;
- no persisted answer/score/time/identity/analytics field;
- storage get/set/remove error handling and visible session-only fallback;
- explicit-only completion and idempotent ordered set;
- no browser-native confirm/alert/prompt;
- default-visible no-JavaScript guidance and print visibility;
- no network/analytics/service-worker code;
- exact 85,000-byte verifier cap.

### Rendered matrix

- viewports: 360, 768, 1024 metrics, 1440;
- modes: Mentor and Self-paced;
- storage: empty, valid persisted, malformed/unknown/extra/invalid/duplicate, and unavailable;
- input: pointer smoke plus complete keyboard-only route;
- media: JavaScript disabled, reduced motion and print;
- evidence: six mode screenshots, overflow metrics, state snapshots, active-focus readings, PDF
  generation and zero console/page errors.

## Risks

- **Mode blocks could become duplicate curriculum.** Keep additions short and machine-marked; compare
  baseline text after removing additions.
- **Static checks could overclaim state behavior.** Treat Playwright reload/error/dialog evidence as a
  separate blocking gate.
- **Storage validation could accept unknown data.** Require exact key-set equality and test every
  invalid shape independently.
- **Storage errors could break page startup.** Override storage before script execution and exercise
  every action in the fallback context.
- **Completion could mutate from a quiz handler.** Isolate completion in one named function and assert
  no call from selection/question paths.
- **Mode and lifecycle controls could conflict.** Keep pressed buttons separate from the one ARIA
  tablist and route every stage change through `select`.
- **Dialog focus could escape or return incorrectly.** Record active element through open,
  Cancel/Escape/Confirm and fallback behavior.
- **Moving questions could change meaning or duplicate them.** Compare all original question fields
  and count one render target per stage.
- **Print could hide mode content under screen selectors.** Override mode visibility explicitly and
  inspect a real print-media render/PDF.
- **New content could exceed weight.** Enforce the signed-off 85KB cap and report actual byte budget;
  do not minify canonical content.
- **Mutable preview could be stale.** Evidence uses only immutable commit SHA.
- **Commit metadata remains outside the shipped scanner.** Inspect it manually until Issue #12 is
  implemented; do not read tree-scan green as metadata proof.

## Rejected alternatives

Duplicate mode-specific curricula, a second tablist, inferred completion, persisted quiz answers or
scores, timestamps/analytics/identity fields, browser-native confirm, account/cloud sync, service
workers, external state libraries, URL progress, mutable-preview evidence, a 100KB cap without
measurement, and static-only storage/accessibility proof are rejected by the signed-off spec.

---
Gate: the owner accepts BEFORE `verify.py` or `index.html` is edited. Any departure requires a plan
amendment and renewed acceptance.
