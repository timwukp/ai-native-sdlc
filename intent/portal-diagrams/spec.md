# Spec: three diagrams, legible on the narrowest screen the portal claims

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Signed-off-by:** pending — owner sign-off
- **Status:** draft

## The measurement that drives every requirement below

The portal's container is `.wrap{max-width:1020px;margin:0 auto;padding:0 20px}`. At a 360px
viewport the **content box is 320px**, not 360. An inline SVG with `width:100%` is therefore scaled
by `320 / viewBox_width`, and its text with it:

```
effective_px = font_size × 320 / viewBox_width
```

This corrects the figure reported during investigation. The 360-wide draft was called "passing at
12.0px" by measuring against the viewport instead of the content box; inside this container it
renders at `12 × 320/360 =` **10.7px**. It fails the portal's own promise, like the other six. No
draft currently satisfies the requirement.

Permissible widths, at `effective_px ≥ 12`:

| Minimum font in the SVG | Maximum viewBox width |
|---|---|
| 12 | 320 |
| 14 | 373 |
| 16 | 426 |

## Resolved open questions

**Q1 — how mobile legibility is achieved: narrow mobile-first.** One canvas, sized so it never needs
scaling down on the narrowest supported screen. Horizontal scroll is rejected because the portal
teaches a lifecycle in sequence and a panned diagram hides half the sequence at the moment the
reader is building the mental model. Amending the 360px promise is rejected because the promise is
the accessible behaviour, not a nicety. **The constraint is a formula, not a fixed width**: a wider
canvas is permitted when its fonts scale with it, per the table above.

**Q2 — which concepts ship first: three.** The loop (§`loop`, "The loop, and the artifact that
carries it"), the enforcement ladder (§`enforce`, "Advisory, deterministic, or actually binding"),
and the merge-base trap, also in §`enforce`, since it is about what the gate verifies. The artifact
handoff, adoption ceiling and control bands are deferred — not rejected.

**Q3 — the drafts are references, not assets.** All three are redrawn to the formula. The drafts
settle composition — which elements, what order, what to leave out — and their `.md` notes carry
that reasoning. None is adopted as-is, including the mobile variant, which misses by 1.3px.

**Q4 — captions in both places.** A `<desc>` for assistive technology and a visible `<figcaption>`
for everyone, and the `<figcaption>` must not restate the `<title>`: the title names the diagram,
the caption says what to take from it.

## Requirements

1. **Three inline SVG figures**, in `index.html`, at the sections named in Q2. No external file, no
   `<image>`, no `<script>`, no `@import`, no webfont, no remote `url()`. The page must still render
   from `file://`.
2. **Legibility by formula.** For every figure, `min_font_size × 320 / viewBox_width ≥ 12`. Asserted
   per figure by parsing the SVG, not by eyeballing a screenshot.
3. **No `height` attribute on any `<svg>` root.** `height="auto"` is invalid — it expects a length —
   and threw a console error in all six drafts. The container controls height via CSS.
4. **Accessibility per figure:** `role="img"`, `aria-labelledby` naming a `<title>` and a `<desc>`
   whose ids exist, and a `<desc>` of at least 80 characters conveying the mechanism rather than
   repeating the title. Each figure wrapped in `<figure>` with a `<figcaption>` whose text differs
   from the `<title>`.
5. **Id namespacing.** Every `id` in a figure is prefixed `dgN-`. The page already has ids and a
   duplicate id is an accessibility defect, not a cosmetic one.
6. **Palette only.** Colours restricted to those already defined in the page. Verified: every colour
   used by the drafts is already present, `#8ee8ca` included as `--acc2`, so no palette extension is
   needed. Hard-coded hex is permitted inside SVG (CSS variables do not apply to presentation
   attributes in all engines) but must be a value the page already uses.
7. **Weight budget.** The page is 44,972 bytes today. After the three figures it must not exceed
   **75,000 bytes**, asserted by `verify.py`. Each figure therefore has roughly 10 KB, against
   drafts of 4.7–6.8 KB.
8. **No JavaScript dependency.** Every figure renders with scripting disabled. Since the figures are
   static markup this holds by construction, and the assertion is that no figure contains a
   `<script>` or an event-handler attribute.
9. **Zero console errors and zero warnings**, verified from the published URL after deploy, not only
   locally.
10. **Truthfulness.** No figure may contradict §`limits`. Specifically the enforcement-ladder figure
    **must** show that the strongest tier is still bypassable by a repository administrator — the
    draft dropped that nuance for tidiness, and it is the difference between "binding" and
    "binding unless you own the repo". Asserted by requiring the administrator-bypass wording in the
    figure's `<desc>` or `<figcaption>`.
11. **`verify.py` asserts 1–8 and 10** per figure, committed and observed failing before the figures
    exist. Requirement 9 is verified by the browser against the live URL.
12. **Serve-integrity unchanged.** After publish, the bytes served must be byte-identical to the
    committed `index.html`, by sha256, as with the current build.

## Non-requirements

- The other three concepts. Deferred to a later chain.
- A desktop-optimised variant of any figure. One canvas serves both; a second canvas per concept
  doubles what must be kept true, and the whole point of the formula is that one canvas suffices.
- Dark/light theming. The page is dark-only today.
- Animation or interactivity of any kind.

## Acceptance evidence

- `python3 verify.py` — all checks pass, including the three new per-figure groups; the count rises
  from 69 and the new total is reported rather than assumed.
- The formula computed and printed per figure, showing the effective pixel size at 320px content.
- A headless render at 360px and at 1000px, with the console message count reported at both.
- `sha256` of the served bytes equal to `sha256` of the committed file.
- Page size in bytes, against the 75,000 budget.

## Rejected alternatives

- **Horizontal scroll on small screens** — hides part of a sequence the reader is assembling.
- **Amending the 360px promise** — trades an accessibility commitment for author convenience.
- **Adopting the drafts as-is** — the closest one misses the requirement by 1.3px, and adopting
  unreviewed work because it already exists is the mistake this process is meant to prevent.
- **SVG files referenced with `<img>`** — breaks `file://` rendering and the single-file property,
  and `<img>`-loaded SVG cannot inherit the page's palette.
- **A `<style>` block inside each SVG** — duplicates the page's tokens in a second place that can
  drift; presentation attributes are verbose but singular.

## Open questions for the plan

1. Does the merge-base figure sit before or after the prose that explains the trap? A figure ahead of
   the explanation can orient a reader or can confuse them; the plan should pick one and say why.
2. Does `verify.py` grow a reusable per-figure helper, or three explicit blocks? Favour the helper
   only if it stays readable when a check fails — a failure must name which figure.
