# Plan: correct the box model first, then constrain both ends of diagram scale

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** fbbf85ed592fb186ba7cf015ed9e65811a028853
- **Status:** accepted

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time. It binds review to protected
`main` after the privacy closeout, not to this branch's artifact commits.

## Files changed (in order of work)

1. `.sdlc/active` — already points at `responsive-portal-layout`.
2. `intent/responsive-portal-layout/intent.md` — accepted Stage 1 artifact linked to Issue #10.
3. `intent/responsive-portal-layout/spec.md` — signed-off responsive and accessibility contract.
4. `intent/responsive-portal-layout/plan.md` — this accepted implementation plan and binding.
5. `verify.py` — corrected diagram box-model calculation plus red-first responsive, touch, table,
   motion, print and device-detection checks.
6. `index.html` — CSS tokens/behavior, two table wrappers and figure font-size attributes. No prose,
   diagram meaning, JavaScript behavior or source claim changes.

Explicitly unchanged: README, privacy scanner/hooks/allowlist, all GitHub workflows, PR template,
branch protection, and every shipped artifact chain.

## Work order

### A. Accept the plan and make the current layout fail correctly

1. **Reconfirm state.** Verify the accepted intent and signed-off spec are committed, Build gate is
   open, merge base equals `Accepted-for`, privacy scan is clean, all three required checks remain
   configured, and local `.kiro/settings/` is the only unrelated untracked content.
2. **Accept this plan.** The owner replaces `pending`/`draft`, commits acceptance, and the Test gate
   must open before `verify.py` or `index.html` changes.
3. **Refactor figure verification around actual rendered bounds.** Replace `figure_checks(...,
   content_px)` with inputs derived from named CSS tokens. Parse compact gutter, figure padding,
   figure border, figure cap and SVG cap. For each SVG calculate:

```text
compact available = 360 - 2*gutter - 2*figure_padding - 2*border
compact rendered  = min(compact available, diagram_max)
compact min type  = min_font * compact_rendered / viewBox_width

wide inner        = figure_max - 2*figure_padding - 2*border
wide rendered     = min(wide_inner, diagram_max)
wide max type     = max_font * wide_rendered / viewBox_width
```

4. **Add red responsive assertions.** Independently check:
   - named tokens and exact accepted values;
   - compact and medium gutter consumption by `.wrap`;
   - medium/wide breakpoint count and removal of 700px/760px one-offs;
   - 70ch prose measure and `clamp()` spacing;
   - compact two-column nav, 44px link/button targets and medium flex restoration;
   - compact no-wrap/local-overflow stage tabs and medium wrap restoration;
   - exactly two `.table-scroll` regions, each `role=region`, labeled and focusable;
   - table-local and code-local overflow, with no fixed page width;
   - figure/card caps and centered rules;
   - reduced-motion and print rules, including all hidden panels forced visible;
   - absence of `navigator.userAgent`, `navigator.platform`, `maxTouchPoints` and equivalent device
     sniffing.
5. **Observe red against current `index.html`.** `python3 verify.py` must fail with named responsive
   findings, including current compact effective type near 11.28px and wide type near 36.9px. All
   existing governance, privacy, structure, isolation, content and honesty checks stay green.
6. **Commit the red verifier alone.** Record actual check/failure counts, not predicted values.

### B. Implement the mobile-first foundation

7. **Add root tokens.** Introduce `--page-gutter:16px`, `--measure:70ch`,
   `--touch-target:44px`, `--figure-padding:14px`, `--figure-max:420px` and
   `--diagram-max:360px`. At `min-width:48rem`, change only page gutter to 20px.
8. **Consume layout tokens.** Change `.wrap` to use page gutter; constrain only top-level prose to
   the measure; use `clamp()` for hero and section vertical spacing. Keep cards and panels full
   component width.
9. **Implement compact navigation.** Base `nav.top` becomes two-column grid. Links become flex items
   with minimum 44px height and safe wrapping. At 48rem navigation returns to horizontal flex.
10. **Implement compact tabs.** Base tablist becomes one non-wrapping horizontal local scroll region
    with non-shrinking, snap-aligned buttons and 44px minimum height. At 48rem restore wrapping and
    normal overflow when tabs fit. Do not change the existing click/Arrow/Home/End script.
11. **Wrap the two tables.** Add one labeled/focusable `.table-scroll` wrapper around the enforcement
    table and one around the adoption table. Do not change table, caption, header or cell text.
    Apply local overflow, focus style and a compact minimum table width only inside the region.
12. **Bound code and long text.** Keep `pre` local overflow and max-width 100%; add safe wrapping for
    links/inline code where it does not change code-block content.
13. **Bound figure cards and SVGs.** Center figure cards with 420px maximum border-box width and
    tokenized 14px padding. Center SVGs with 360px maximum width. Keep viewBoxes, coordinates,
    descriptions, titles, captions and ids unchanged.
14. **Raise only figure type.** Inside `figure#dg1`, `figure#dg2` and `figure#dg3`, change every
    `font-size="14"` to 15 and every `font-size="15"` to 16. Do not change the 34px brand SVG or
    any non-figure text. If rendered evidence later shows clipping, adjust only the affected text
    coordinate in a plan amendment or same-plan correction with the reason recorded.
15. **Add reduced-motion and print rules.** Reduced motion changes smooth scrolling to auto. Print
    uses light paper colors, removes interaction-only navigation where safe, prevents clipping and
    forces every `.panel[hidden]` to display. Essential stages, limits, sources, figures and captions
    remain printed.

### C. Prove the implementation without confusing static and visual evidence

16. **Green static verification.** Run `python3 verify.py`. For each figure it must print compact
    minimum ≥12px and wide maximum ≤18px. All responsive contracts and all previous checks pass.
17. **Prove text preservation.** Parse `origin/main:index.html` and the working `index.html` with the
    same stdlib HTML text extractor, excluding style/script, normalize whitespace, and require exact
    equality. This permits table wrappers and CSS/font attributes while refusing a silent prose or
    quiz-copy change.
18. **Run complete repository checks.** Privacy unit tests, mutation proof, full tracked-tree scan,
    Portal verifier, SDLC CI gate, Python compilation and `git diff --check` all pass. Confirm
    `index.html` remains ≤75,000 bytes.
19. **Inspect the diff.** Every path is in this plan; only CSS, two table wrapper pairs and figure
    font-size attributes change in `index.html`; no JavaScript, URL, source text or privacy/governance
    file changes; local `.kiro/settings/` remains unstaged.
20. **Commit implementation separately from red verification.** The history must show the corrected
    check failing before CSS changes make it green.

### D. Render, publish and close

21. **Test Browser again.** Attempt the dashboard Browser route. If it remains unavailable, owner
    setup in Settings → Browser is required and the PR remains Draft. Do not substitute source
    inspection for screenshots.
22. **Rendered viewport evidence.** At 360px, 768px and 1440px record screenshots plus actual page
    `scrollWidth/clientWidth`; inspect nav, tabs, selected state, two table regions, four code blocks,
    three figures and captions. At 1024px record overflow dimensions even if no extra screenshot is
    needed.
23. **Interaction evidence.** Keyboard-only navigate all controls; exercise ArrowLeft/Right/Home/End
    tabs and both table regions; verify visible focus. Disable JavaScript and confirm all six panels,
    tables and figures remain. Emulate reduced motion and inspect print preview with all panels shown.
24. **Open or update the PR.** If rendered evidence is unavailable, create a Draft PR with static
    evidence and the named blocker. Mark ready only after the accepted rendered evidence exists.
25. **Require all existing checks.** `portal verify`, `privacy scan`, and
    `sdlc-gate / sdlc-gate` must all conclude `SUCCESS`. This PR adds no new required context.
26. **Human review and merge.** The owner reviews visual evidence and merges; the agent neither
    approves nor merges.
27. **Verify publication.** Confirm Pages serves the merged `index.html`, Portal checks remain green,
    and no console error/warning or page-level overflow appears on the public URL.
28. **Close the chain.** Create and merge an artifact-only PR marking responsive intent/spec/plan
    shipped before mentor/self-paced PR 2 begins.

## Tests that prove it

### Red target

```sh
python3 verify.py
```

Pass condition for the red phase: non-zero with responsive-only findings; existing privacy,
governance, content and accessibility checks remain green. Output names each figure and reports the
current wrong compact/wide effective sizes.

### Green local targets

```sh
python3 verify.py
python3 -m unittest discover -s scripts -p 'test_privacy*.py'
python3 scripts/privacy_mutation_proof.py
python3 scripts/privacy_scan.py --repo .
python3 -m py_compile verify.py scripts/privacy_scan.py scripts/privacy_pretooluse_hook.py
git diff --check
```

Quantified pass conditions:

- Portal verifier exits 0 and prints the new non-zero check count;
- each figure prints compact min ≥12px and wide max ≤18px;
- 31 privacy tests pass and 10/10 privacy mutants are killed;
- full tracked-tree privacy scan reports 0 findings;
- SDLC gate reports all changed source files named in this plan;
- page bytes ≤75,000;
- normalized non-style/non-script text equals `origin/main:index.html` exactly;
- `index.html` diff contains only accepted CSS, table wrappers and SVG font-size attributes.

### Static responsive cases

- required root tokens and exact values;
- only 48rem and 64rem responsive enhancement breakpoints;
- compact 16px and medium 20px page gutter;
- 70ch prose measure and `clamp()` hero/section spacing;
- compact two-column nav plus medium flex restoration;
- compact no-wrap/scroll tabs plus medium wrap restoration;
- 44px compact nav/tab target contract;
- exactly two labeled/focusable table regions and local overflow;
- pre/code local overflow and safe long-token handling;
- figure/card 420px/360px caps and centering;
- compact formula includes both padding layers and border;
- wide formula includes figure and diagram caps;
- every figure 14→15 and 15→16 type change;
- reduced-motion override and print all-panel rule;
- no UA/platform/touch device sniffing.

### Rendered evidence

For each accepted viewport: engine, width, `scrollWidth`, `clientWidth`, screenshot path and observed
component state. Keyboard/no-JS/reduced-motion/print checks carry actual observations, not checkboxes
without evidence.

## Risks

- **The verifier could repeat the wrong box-model assumption.** Parse accepted tokens and subtract
  gutter, figure padding and border explicitly; print intermediate widths.
- **A 15-unit label could clip.** Static size passes do not prove geometry; Browser evidence blocks
  ready status.
- **A capped figure may still feel too small or too isolated.** Bound the whole card and judge at all
  viewports rather than enlarging SVG text independently.
- **Horizontal scrolling can hide information.** Limit it to labeled table/tab components; verify
  page-level width remains equal to viewport.
- **Keyboard focus on a scroll region can be unclear.** Add explicit focus-visible styling and
  operate both regions in evidence.
- **Print CSS can accidentally retain selected-tab hiding.** Force `.panel[hidden]` visible with
  sufficient specificity and inspect real print rendering.
- **Text could change during wrapper edits.** Compare normalized extracted text byte-for-byte after
  excluding style/script.
- **Browser remains unavailable.** Keep PR Draft and ask the owner to complete Settings → Browser;
  do not silently downgrade evidence.
- **Responsive CSS could exceed the page budget.** Measure after every implementation pass; do not
  raise 75,000 bytes without a spec amendment.
- **Privacy hook may block screenshot metadata/path content.** Store screenshots outside the Repo
  and reference only sanitized evidence; full tree must remain 0 findings.

## Rejected alternatives

UA/device sniffing, JavaScript layout switching, container-query dependency, duplicate mobile SVGs,
wider redrawn canvases, lowering the type floor, raising the ceiling, removing figure padding,
card-transformed table duplication, content edits and inferred visual evidence are rejected by the
signed-off spec.

---
Gate: the owner accepts BEFORE `verify.py` or `index.html` is edited. Any departure requires a plan
amendment and renewed acceptance.
