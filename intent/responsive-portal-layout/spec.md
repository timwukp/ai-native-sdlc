# Spec: mobile-first layout with bounded diagram type

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** shipped

## Measured baseline

The page uses global `box-sizing: border-box`, `.wrap` with 20px horizontal padding, and figures
with a 1px border plus 14px padding. At a 360px viewport the actual SVG width is therefore:

```text
360 viewport - 40 wrap padding - 28 figure padding - 2 figure border = 290px
```

For a 360-unit viewBox, current 14-unit text renders at `14 × 290 / 360 = 11.28px`. The existing
verifier uses 320px and reports 12.44px because it subtracts only `.wrap` padding. This is a wrong-box
false green.

At a wide viewport, the 1020px border-box `.wrap` leaves 980px content; the full-width figure leaves
950px after border and padding. The SVG scales to roughly 2.64 times its viewBox, making 14-unit text
about 36.9px beside 16px body text. The same rule therefore undersizes mobile text and oversizes
laptop text.

Current responsive inventory:

- two semantic tables, neither in a bounded overflow region;
- four code blocks with local `overflow: auto`;
- six stage tabs using wrap rather than an intentional compact interaction;
- eight section-navigation links using wrap;
- three SVGs with 360-unit viewBox widths, internal type at 14–15 units;
- no reduced-motion or print media query.

## Requirements

### Responsive foundation

1. Define named CSS custom properties for compact/wide page gutter, content measure, touch target,
   figure padding, figure maximum width and diagram maximum width. Layout formulas and verification
   read those tokens rather than duplicating unrelated literals.
2. Use a mobile-first base and at most two intentional enhancement breakpoints: medium at 48rem and
   wide at 64rem. Existing 700px/760px one-off media queries are consolidated into the named medium
   behavior.
3. The page responds only to viewport/media conditions and intrinsic layout. Neither HTML nor
   JavaScript reads user-agent, platform, device brand, touch-point count or screen class to choose
   layout.
4. `.wrap` remains centered with a 1020px maximum border-box width. Compact horizontal gutter is
   16px and medium/wide gutter is 20px.
5. Top-level explanatory prose has a maximum readable measure of 70 characters while cards, tables,
   code and diagrams keep their component-specific width. This must not center every paragraph or
   narrow tab-panel comparison grids.
6. Section and hero block spacing use `clamp()` so compact layouts reduce unused vertical space and
   wide layouts retain hierarchy.

### Navigation, tabs and touch

7. On compact screens the top section navigation uses an intentional two-column grid with each link
   at least 44px high. At medium width it becomes the existing horizontal flex navigation.
8. Stage tabs remain one semantic ARIA tablist. On compact screens they are a single horizontal,
   locally scrollable row with non-shrinking buttons, scroll snapping and at least 44px height; at
   medium width they may wrap normally.
9. Keyboard focus remains visible on navigation links, tabs, table overflow regions, buttons,
   summaries and other controls. A selected tab is never clipped from its own local scroll region.
10. No page-level horizontal scrolling is introduced. Long links and inline code may break safely;
    code blocks retain their own bounded horizontal scrolling.

### Tables

11. Each of the two real tables is wrapped once in a `.table-scroll` region with `role="region"`,
    a specific `aria-label`, and `tabindex="0"`. Table markup, captions, `th` scope and source order
    remain unchanged.
12. Compact tables retain a meaningful minimum table width and scroll only inside their region. The
    region has a visible focus style and a subtle overflow affordance; it does not hide columns,
    transform rows into cards or duplicate header labels.
13. At widths where a table fits, the wrapper introduces no unnecessary scrollbar or width change.

### Diagram sizing and typography

14. All three figure cards share one rule: 420px maximum border-box width, centered in the content
    column, with the existing border, background and 14px padding.
15. Each SVG keeps `width: 100%` for compact shrinking and gains a 360px maximum rendered width,
    centered inside the card. It never scales above its 360-unit viewBox width.
16. Every current 14-unit SVG text node becomes at least 15 units, and current 15-unit figure titles
    become 16 units. Text content, coordinates, viewBox, accessibility markup and diagram meaning
    remain unchanged unless rendered evidence proves one coordinate must move to prevent clipping.
17. At the 360px compact layout the verifier computes available SVG width as:

```text
viewport - 2 × compact gutter - 2 × figure padding - 2 × figure border
```

    then caps it at the SVG maximum width. For the specified values that is 298px, so 15-unit text
    renders at 12.42px and passes the 12px floor.
18. At a 1440px viewport the verifier computes the figure content box from its 420px maximum border
    box and caps the SVG at 360px. The largest 16-unit text therefore renders at 16px, below the 18px
    ceiling and consistent with body text.
19. `verify.py` prints minimum and maximum effective type per figure and independently requires
    minimum ≥12px and maximum ≤18px. It fails if the gutter, figure padding/border, figure cap,
    viewBox or font sizes become unreadable from the CSS/markup.
20. Figure title, description, caption, id namespacing, palette, no-script/no-image rules and
    administrator-bypass honesty check remain unchanged and green.

### Motion and print

21. Add `@media (prefers-reduced-motion: reduce)` that disables smooth scrolling. No animation or
    transition is added by this PR.
22. Add print CSS using light background/dark text, removing decorative borders/backgrounds where
    needed, allowing URLs/code to remain legible, and forcing all six tab panels to display. Print
    output must not depend on the currently selected JavaScript tab.
23. Print layout hides interaction-only navigation/controls only when their destination content is
    present in the print. It does not hide honest limits, sources, stage content or figure captions.

### Verification and evidence

24. Extend `verify.py` before modifying `index.html`. The red run must fail for the corrected 290px
    baseline formula, missing diagram upper bound, missing responsive tokens, missing table regions,
    missing 44px touch contract, and absent reduced-motion/print rules—not from a traceback.
25. Static checks require the exact number of table wrappers and their accessibility attributes,
    confirm no user-agent/device detection, confirm local overflow boundaries, and preserve all
    existing structure/content/honesty/privacy/governance checks.
26. `index.html` remains under 75,000 bytes and performs zero external runtime requests.
27. Rendered evidence is required at 360px, 768px and 1440px. For each viewport record page-level
    overflow, navigation, selected tab visibility, both tables, four code blocks and all three
    figures. A screenshot alone is insufficient if overflow dimensions were not checked.
28. Keyboard-only evidence covers navigation, tab arrow/Home/End behavior, table scroll regions,
    details, quiz controls and visible focus. JavaScript-disabled evidence confirms all six panels,
    tables and figures remain readable.
29. Reduced-motion and print evidence are recorded from a real rendering engine. Print evidence
    confirms all tab panels display and text is readable on a light background.
30. Existing commands remain green: privacy unit tests, privacy mutation proof, full tracked-tree
    privacy scan, Portal verifier and SDLC CI gate.
31. `index.html` text content is reviewed as unchanged except markup wrappers required around tables;
    SVG `font-size` attributes and CSS are the only intended visual changes.
32. The pull request remains blocked from ready/merge until Browser evidence exists. Source reading,
    verifier formulas and inferred layout do not substitute for rendering.

## Non-functional requirements

- **Accessibility:** preserve WCAG-oriented semantic structure, 44px compact targets, visible focus,
  12px minimum diagram type, reduced motion, keyboard scroll regions and complete no-JS content.
- **Performance:** no dependency, image, font, network request or JavaScript behavior is added.
- **Weight:** total `index.html` stays at or below 75,000 bytes.
- **Compatibility:** use broadly supported CSS grid/flex/overflow/media/print features; no container
  query or new JavaScript API is required.
- **Maintainability:** one mobile-first rule per component, two shared breakpoints, one canonical
  figure rule, and verifier tokens tied to CSS declarations.
- **Truthfulness:** do not claim device detection; describe responsive behavior as viewport-based.
- **Privacy:** screenshots and logs must pass the repository scanner and contain no host-local data.
- **Evidence:** rendered checks name viewport and engine; unavailable Browser evidence remains a
  blocker, not a passed checkbox.

## Design

### 1. CSS tokens

Add tokens equivalent to:

```css
--page-gutter:16px;
--measure:70ch;
--touch-target:44px;
--figure-padding:14px;
--figure-max:420px;
--diagram-max:360px;
```

At `min-width:48rem`, only `--page-gutter` changes to 20px. `.wrap`, prose measure, figure and touch
rules consume these tokens.

### 2. Compact navigation and tablist

Navigation defaults to a two-column grid and links use flex alignment with `min-height` from the
touch token. Medium layout returns to horizontal flex.

The tablist defaults to `flex-wrap: nowrap`, local horizontal overflow, scroll padding/snap and
non-shrinking buttons. Medium layout restores wrapping and removes forced local scrolling where all
tabs fit. The existing JavaScript selection and keyboard algorithm remains unchanged.

### 3. Table regions

Wrap the enforcement and adoption-position tables in separate labeled `.table-scroll` divs. CSS
applies `overflow-x:auto`, a component-local maximum width and focus outline. Each table receives a
minimum width only inside this wrapper; semantic table elements are untouched.

### 4. Figures

Center and cap `figure.dg` at 420px. Center and cap its SVG at 360px. Increase only figure text size
attributes: 14→15 and 15→16. The brand icon is outside `figure.dg` and is not changed.

The corrected verifier derives compact width from gutter, figure padding and border; derives wide
width from figure/diagram caps; and calculates both extrema for each figure.

### 5. Motion and print

Reduced motion overrides only `html { scroll-behavior:auto; }`. Print CSS forces panels visible and
uses printable colors without altering screen theme. Figures remain inline SVG and scale to the
print content box without exceeding their cap.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| Current mobile verifier measures `.wrap` content but ignores figure padding/border | Portal maintainer | Replace it with the full box-model formula and red-first failure against current markup. |
| Capping diagrams may make wide cards look like unused space | Design owner | Bound and center the whole figure card, not only the SVG. |
| Increasing text may clip long SVG labels | Design owner | Preserve coordinates initially; rendered 360/768/1440 evidence blocks ready status if clipping appears. |
| Horizontal table regions can be invisible to keyboard users | Accessibility owner | Labeled `role=region`, `tabindex=0`, visible focus and overflow affordance on exactly two wrappers. |
| Tabs may hide the selected item off-screen | Accessibility owner | Scroll-snap/non-shrinking buttons plus rendered keyboard evidence; adjust selection scrolling only if evidence shows a defect. |
| Print could include only the selected panel | Accessibility owner | Print CSS forces every tabpanel visible with `display:block !important`. |
| Device detection request could be implemented as UA sniffing | Portal maintainer | Explicitly prohibit UA/platform/touch detection; responsive CSS is the implementation. |
| Browser evidence route is currently unavailable | Repository owner | Owner selected dashboard Browser, but the tool still reports “not set up.” Enable it in Settings → Browser before the PR can become ready; otherwise obtain a new explicit human-evidence decision. |
| Static verification could be mistaken for visual proof | Repository owner | Keep rendered viewport, overflow, keyboard and print evidence as a separate blocking gate. |
| Visual artifacts could expose local data | Privacy owner | Use the public URL or clean local page only; run privacy scan before commit and do not include host paths in captions/logs. |

## Rejected alternatives

- User-agent/device detection; separate mobile/desktop SVG assets; wider redrawn canvases; full-width
  cards around narrow diagrams; row-to-card table duplication; JavaScript layout switching; external
  responsive libraries; lowering the 12px floor; raising the 18px ceiling; removing figure padding;
  or treating source inspection as rendered evidence.

## Out of scope

- Mentor mode, self-paced progress, section timing, teaching prompts, glossary or Playbook expansion.
- New diagrams, changed diagram meaning, animations, theme switcher or content rewrite.
- Browser installation itself; it is an owner/runtime setup action and a Deploy evidence precondition.
- Changes to privacy scanner, SDLC gate, workflows, branch protection or local hook configuration.

---
Gate: owner signs off; flagged concerns worked first. Applied org skill: `ai-native-sdlc`. Browser
availability was tested after Intent acceptance and remains unavailable until configured by the
owner; the spec does not count that route as evidence yet.
