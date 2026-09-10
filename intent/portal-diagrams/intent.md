# Intent: teach the lifecycle in pictures, not only in prose

- **Slug:** portal-diagrams
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** shipped

## Problem

The portal at `https://timwukp.github.io/ai-native-sdlc/` teaches the AI-native SDLC entirely in
prose and tables. Several of its central ideas are **structural**, and structure is what prose is
worst at:

- **The loop closes.** The page says Stage 6 writes a new `intent.md` that re-enters Stage 1, and a
  reader has to assemble that cycle in their head from a list rendered top to bottom. The one thing
  that distinguishes this lifecycle from a linear one is the hardest thing to see on the page.
- **The merge-base trap** is a claim about three different commits on a branching graph — the fork
  point, the branch tip, and the base tip after it moves. Describing a graph in sentences is why
  this trap keeps being re-explained.
- **The enforcement ladder** is three layers each with one escape route. The table conveys the
  ordering but not that strength means *fewer* bypasses rather than none.
- **The adoption ceiling** is a boundary: three controls sit outside what any repository can grant
  itself. A four-row table reads like a feature checklist with two rows unticked, which is exactly
  the wrong impression.
- **Control bands** are a chart — a metric crossing thresholds, with escalating permissions — and
  the page currently renders that as a YAML block plus a bullet list.

The request that prompted this was straightforward: readers remember pictures, and a diagram makes
a mechanism land faster than a paragraph does.

## Prior art, and its measured state

Six diagram drafts already exist, produced by six parallel sub-agents and kept **outside this
repository** at `/home/ec2-user/.kiro/crew/workspace/diagram-drafts/`. They were not produced by
this process and carry no review, so they are candidate material, not work product.

Each has been independently verified — not accepted on its author's report, several of which proved
inaccurate. Measured state:

| Draft | Bytes | Well-formed | viewBox width | Effective font at 360px |
|---|---|---|---|---|
| `01-loop-mobile.svg` | 5.3 KB | yes | 360 | **12.0px — passes** |
| `01-loop.svg` | 5.7 KB | yes | 900 | 4.8px |
| `02-artifact-chain.svg` | 6.8 KB | yes | 1000 | 3.6px |
| `03-enforcement.svg` | 4.9 KB | yes | 720 | 5.5px |
| `04-merge-base.svg` | 4.7 KB | yes | 960 | 4.5px |
| `05-adoption-ceiling.svg` | 6.5 KB | yes | 1000 | 4.3px |
| `06-control-bands.svg` | 6.3 KB | yes | 720 | 5.0px |

All seven are inline SVG with `role="img"`, a wired `<title>`/`<desc>`, per-diagram id prefixes, no
external reference, no script, and palette-only colours.

**The load-bearing finding:** six of the seven are unreadable on a phone. A wide viewBox scaled to a
360px screen shrinks its text by the same factor, landing at 3.6–5.5px against a 12px floor. Only
the 360-wide variant passes, and it does so at exactly 12.0px. This is not a font-size bug that can
be edited away; it follows from the canvas width.

## Desired outcome

A reader who scans the portal without reading it closely comes away with the loop, the artifact
handoff, the enforcement ladder and the adoption boundary correctly in mind, because each is shown
as well as stated. Every diagram is legible on the devices the portal claims to support, and the
portal's existing promises — zero dependencies, offline from `file://`, no console errors, keyboard
operable, usable without JavaScript — remain true afterwards.

No diagram may make the honest limits *look* better than the prose says they are.

## Affected users / systems

- **Readers of the portal**, particularly the ones skimming rather than studying.
- `index.html` — gains inline SVG figures. It is the only shipped file.
- `verify.py` — must gain checks for whatever the diagrams promise, or the promises are unenforced.
- The portal's existing spec commitment that content is legible from 360px wide — this change either
  honours it or amends it deliberately.
- No change to the `ai-native-sdlc` skill or to `agent-skills-best-practice`.

## Constraints

- **Zero dependencies, still.** Inline SVG only. No `<image>`, no external asset, no webfont, no
  script inside a diagram, no `@import`. The page must keep rendering from `file://`.
- **No console errors.** The page currently reports 0 errors and 0 warnings from the live URL; that
  must still hold. Note `height="auto"` is invalid on `<svg>` and threw an error in every draft — an
  instance of the class of mistake this constraint exists to catch.
- **Accessibility is not optional.** Every figure needs `role="img"` with a wired `<title>` and a
  `<desc>` that conveys the same information as the picture, so a screen-reader user is not sent to
  a dead end. A diagram is an alternative to prose, never a replacement for it.
- **No JavaScript dependency.** Diagrams must render with scripting disabled, like the rest of the
  page apart from the self-check.
- **Weight.** The page is 45 KB today. Diagrams must not turn it into a slow download; a total
  budget belongs in the spec.
- **Truthfulness.** A picture simplifies, and simplification is where overclaiming hides. Any
  caveat a diagram drops must still be present in the prose beside it. One draft already dropped the
  `enforce_admins` nuance to keep its ladder tidy — the nuance that makes the gate bypassable in a
  personal repository.
- **The drafts are unreviewed.** Anything adopted must satisfy a spec requirement on its own merit,
  not because it already exists.
- Follow this skill's own lifecycle: no edit to `index.html` before an accepted plan, and no
  artifact self-approved by its author.

## Success criteria

1. Every diagram shipped is legible on a 360px-wide screen by whatever rule the spec adopts, and
   that rule is stated rather than assumed.
2. Every diagram carries `role="img"`, a `<title>`, and a `<desc>` that conveys the mechanism, and
   the prose it accompanies still stands alone.
3. The page renders with **0 console errors and 0 warnings**, verified from the published URL.
4. No external reference, no script inside a diagram, no `@import`; the page still works offline.
5. Every diagram renders with JavaScript disabled.
6. `verify.py` asserts each of the above per figure, and the page's total weight against the spec's
   budget. Committed and observed failing before the diagrams land.
7. No diagram contradicts or softens the honest-limits section; any caveat a diagram omits appears
   in adjacent prose.
8. The published URL serves the new page, byte-identical to the committed file.
9. The chain for this slug is committed, with acceptance and sign-off in separate human commits.

## Open questions

1. **How is mobile legibility achieved?** This is the decision the measurements force, and the three
   candidates trade off differently:
   - **narrow mobile-first canvases** (~360–420 wide) — proven to pass, but each figure carries less,
     so the set probably grows from six to eight or ten;
   - **horizontal scroll on small screens** — keeps the rich wide diagrams, at the cost of panning;
   - **amend the portal's 360px promise** and declare diagrams desktop-oriented, with prose carrying
     mobile readers.
   Proposed: narrow mobile-first, because it is the only option already demonstrated and it keeps the
   existing promise intact. The owner decides.
2. **Which of the six concepts ship in the first release?** All six earn their place on the argument
   above, but each one added is more page weight and more to keep true. Proposed: the loop, the
   merge-base trap and the enforcement ladder first, since those three teach mechanisms readers
   most often get wrong.
3. **Are the existing drafts adopted, redrawn, or used only as references?** If mobile-first wins,
   five of six need redrawing anyway, in which case the drafts serve mainly as settled composition
   decisions. To be resolved in design.
4. **Does a figure caption belong in the SVG, in the HTML, or both?** A `<desc>` serves assistive
   technology; a visible `<figcaption>` serves everyone. Proposed both, with the caption not merely
   repeating the title.
