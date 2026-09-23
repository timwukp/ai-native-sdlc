# Intent: make the portal comfortable on phones and consistent on laptops

- **Slug:** responsive-portal-layout
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-23
- **Status:** accepted
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/10

## Problem

The portal has a viewport meta tag and several isolated media queries, but it does not define one
coherent responsive system for compact, medium and wide displays. Navigation and stage tabs wrap
according to available space rather than an intentional mobile interaction, tables become dense,
and desktop spacing dominates smaller screens. The page is usable, but it does not yet feel designed
for a mentee reading on a phone or a mentor presenting from a laptop.

The three inline SVG diagrams have a more specific two-sided typography defect. Their viewBox width
is 360 units and the CSS gives each SVG `width: 100%`:

- on a wide laptop, the SVG expands toward the full content column, making 14–15 unit labels appear
  much larger than the surrounding 16px body text;
- on a 360px viewport, the current verifier says the diagram receives 320px after `.wrap` padding,
  but it ignores the figure's additional 14px padding on each side. The actual SVG width is about
  292px, so a 14-unit label renders near 11.4px—below the intended 12px floor.

The existing check therefore passes while measuring the wrong box. The portal needs an upper scale
bound for wide displays and a corrected lower-bound calculation for compact displays.

## Desired outcome

The same single-file portal adapts by viewport size—not device or user-agent detection—across phones,
tablets, laptops and wide displays. Content remains readable, controls remain easy to operate, and
page-level horizontal scrolling is absent. Tables and code blocks handle local overflow without
hiding content.

Each diagram remains legible at the narrowest supported viewport and visually consistent with body
text on larger screens. Verification measures the actual SVG content box after both page and figure
padding, and checks both minimum and maximum effective type size.

The change establishes a visual foundation for the later mentor and self-paced modes without adding
those modes now.

## Affected users / systems

- Mentees reading independently on phones, tablets or laptops.
- Mentors presenting the portal on laptop or projected wide displays.
- Keyboard-only and low-vision users who depend on visible focus and readable type.
- Printed or PDF handouts generated from the single page.
- The three inline SVG figures, navigation, tabs, tables, code blocks and page spacing.
- `verify.py`, whose current mobile diagram formula measures the wrong content box.
- Existing Portal, SDLC and privacy workflows; all must remain green.

## Constraints

- Use CSS viewport/container behavior and intrinsic sizing. Do not inspect user-agent strings,
  platform names, touch capability or device brands.
- Keep one `index.html` with inline CSS/JavaScript, no build system, external asset, webfont,
  framework, analytics or runtime network request.
- Preserve all source content and honest-limit claims. This PR changes presentation and responsive
  behavior, not the Playbook curriculum.
- Core content remains available with JavaScript disabled. No new content may depend on script.
- Keep the full page under the existing 75,000-byte budget.
- Maintain the semantic tab pattern, table headers, figure accessibility, skip link and visible
  focus behavior.
- Compact interactive targets are at least 44px in the dimension used for tapping.
- No page-level horizontal overflow at the accepted viewports. A table or code block may have a
  clearly bounded local scroll region when content cannot wrap safely.
- Diagram type must be at least 12px at the narrowest accepted content box and no more than 18px on
  wide displays. The verifier must include figure padding and the CSS maximum rendered SVG width.
- Do not create separate mobile and desktop SVGs. One canonical figure per concept avoids duplicated
  truth and accessibility descriptions.
- Existing privacy scanning remains active. Screenshots and test artifacts must not contain local
  machine paths or personal data.
- Every rendered change goes through a pull request with 360px, 768px and 1440px evidence plus
  keyboard-only, JavaScript-disabled and print checks.
- The current native Browser panel is not configured on this host. Final visual evidence must come
  from an enabled Browser surface or an explicitly identified human capture; source inspection is
  not a substitute for rendered evidence.
- The agent does not push, self-approve artifacts, approve the PR or merge.

## Success criteria

1. CSS defines a small set of named layout/touch/measure/diagram tokens and intentional compact,
   medium and wide behavior rather than scattered one-off fixes.
2. At 360px, 768px, 1024px and 1440px viewport widths there is no page-level horizontal overflow;
   navigation, tabs, tables, code blocks and every control remain reachable.
3. Compact navigation and stage tabs use intentional layouts with at least 44px tap targets, visible
   focus and no clipped selected state.
4. Body copy keeps a readable measure on wide displays and compact sections reduce excessive
   vertical whitespace without crowding headings or controls.
5. All three SVGs use one bounded rendering rule that prevents desktop upscaling beyond the accepted
   maximum while preserving mobile width.
6. The actual minimum effective SVG font size is at least 12px after page and figure padding at
   360px; the maximum is at most 18px at 1440px. Each figure's computed values are printed by
   verification.
7. Figure captions remain readable, distinct from titles and associated with their figures; SVG
   accessibility labels and ids remain valid.
8. Tables expose a keyboard-reachable local overflow region on compact screens rather than forcing
   the entire page wider. Code blocks wrap or scroll within their own boundary.
9. `prefers-reduced-motion` disables smooth scrolling, and print CSS renders all stage panels and
   essential text without dark backgrounds, clipped overflow or interactive-only hiding.
10. `verify.py` is updated first and observed failing because it detects the current wrong formula,
    missing upper bound and missing responsive contracts—not because of a traceback.
11. Existing privacy tests, privacy scan, Portal checks and SDLC gate all remain green after the
    responsive implementation.
12. Actual rendered evidence is recorded at 360px, 768px and 1440px. Keyboard-only operation,
    JavaScript-disabled content, reduced-motion behavior and print output are checked and reported.
13. No existing portal claim, stage content, quiz answer, source attribution or honest limitation is
    removed or changed by presentation work.
14. After merge, an artifact-only pull request marks this chain shipped before mentor/self-paced PR 2
    begins.

## Resolved questions

1. **Diagram strategy:** cap each canonical SVG at 360 CSS pixels and raise the current 14-unit
   labels to at least 15 units where required by the corrected mobile formula. Do not create a
   second asset or redraw onto a wider canvas.
2. **Figure-card width:** bound and center the whole figure card so diagram, caption and border form
   one intentional component on wide displays.
3. **Compact tables:** preserve semantic tables inside labeled, keyboard-focusable local overflow
   regions. Do not transform rows into duplicate card markup.
4. **Visual evidence:** use the dashboard Browser panel for 360px, 768px and 1440px rendered evidence.
   Availability must be tested before relying on it; selecting this route is not itself evidence that
   the Browser is configured.

---
Gate: product owner accepts. The accepting commit is the record.
