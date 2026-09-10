# Plan: three figures, certified by the formula rather than by eye

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 2858bab1f3c05393d7249f726a62f8e9c5962d32
- **Status:** shipped

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`2858bab` (full sha recorded at acceptance).

## Resolved: the spec's two open questions for the plan

**Figure placement relative to prose — figure first for the loop, prose first for the other two.**
The loop figure is an *orientation* device: §`loop` opens by telling the reader the lifecycle is a
cycle, and a picture of the cycle before the words makes the following prose confirmatory rather
than constructive. The enforcement ladder and the merge-base trap are *corrections* of an intuition
the reader arrives with — that a gate is binding, that a branch's base is its tip — and a correction
only lands once the wrong intuition has been stated. So those two follow their prose.

**`verify.py` gets a per-figure helper, not three blocks.** A helper is chosen only because the
failure message can name the figure: `figure_checks(fig_id="dg1", ...)` reports
`dg1: effective font 10.7px at 320px content, need >= 12`. Three copy-pasted blocks would drift as
the checks grow, which is how the mutation-count coupling in the other repository happened.

## Files changed (in order of work)

1. `/home/ec2-user/.kiro/crew/workspace/ai-native-sdlc-portal/verify.py` — the per-figure helper and
   its three invocations, plus the page-weight assertion. Written and observed failing FIRST.
2. `/home/ec2-user/.kiro/crew/workspace/ai-native-sdlc-portal/index.html` — three `<figure>` blocks
   containing the inline SVGs, at the placements resolved above.

`README.md` is deliberately **not** in this list: it references `verify.py` by name and describes how
to run it, but hard-codes no check count, so the count rising from 69 does not falsify it. Verified
by grep rather than assumed.

## Work order

1. **Reconfirm.** Spec `signed-off` in a committed state (not merely on disk), build gate open,
   merge base recorded, tree clean.
2. **Red first.** Add `figure_checks` and its three invocations to `verify.py`, plus the 75,000-byte
   page budget. Run it: it must report **3 figure groups failing because no figure exists**, as
   findings with figure ids named, not as a traceback. Commit this red target alone.
3. **Draw figure 1 — the loop.** Satisfy the formula by construction: pick the minimum font first,
   then derive the maximum viewBox width from it, rather than drawing and measuring afterwards.
4. **Run `verify.py`.** Figure 1's group passes; figures 2 and 3 still fail.
5. **Draw figure 2 — the enforcement ladder**, including the administrator-bypass fact required by
   spec requirement 10. This is the figure most likely to be quietly wrong, because the honest
   version is less tidy than the tidy version.
6. **Draw figure 3 — the merge-base trap.**
7. **Green.** `verify.py` reports 0 failed and the new total; page size under budget.
8. **Render and read.** Headless at 360px and 1000px; report console message counts at both, and the
   computed effective font size per figure. A screenshot is evidence for the human, not a check.
9. **Commit the implementation.** No approval field touched by the agent.
10. **Publish and verify the live bytes.** Owner pushes and merges; then confirm the served page is
    byte-identical to the committed file by sha256, and re-run the console check against the public
    URL, since spec requirement 9 is about the published page rather than the local one.

## Tests that prove it

### Red-first target

```sh
cd /home/ec2-user/.kiro/crew/workspace/ai-native-sdlc-portal
python3 verify.py      # must fail: three figure groups, no figures present
```

### The formula, per figure

`verify.py` parses each figure's `<svg>` and computes:

```
effective_px = min_font_size × 320 / viewBox_width
```

Pass condition: `effective_px >= 12` for all three, where 320 is the content width of
`.wrap{max-width:1020px;padding:0 20px}` at a 360px viewport. The check asserts the divisor against
the stylesheet rather than hard-coding it, so a future padding change fails the test instead of
silently invalidating every figure.

### Per-figure structural checks

For each of `dg1`, `dg2`, `dg3`:

- `role="img"` present; `aria-labelledby` names ids that exist in that figure;
- `<title>` non-empty; `<desc>` at least 80 characters;
- wrapped in `<figure>` with a `<figcaption>` whose text differs from the `<title>`;
- every `id` in the figure prefixed `dgN-`, and no id duplicated anywhere in the page;
- no `height` attribute on the `<svg>` root;
- no `<script>`, `<image>`, `@import`, `xlink:href` to a remote target, or `on*` handler attribute;
- every colour is one already present in the page.

### Whole-page checks

```sh
python3 verify.py                       # 0 failed; report the new total
wc -c index.html                        # < 75000
python3 -c "import html.parser,pathlib;..." # existing well-formedness check
```

Pass condition: 0 failed, total reported (currently 69, rising); page under 75,000 bytes;
requirement 10's administrator-bypass wording present in figure 2.

### Published-page checks (step 10, after merge)

```sh
curl -s https://timwukp.github.io/ai-native-sdlc/ -o live.html
sha256sum live.html index.html          # must match
```

Plus a headless load of the public URL reporting 0 console errors and 0 warnings.

## Risks

- **The formula is satisfiable but tight.** At 12px minimum the canvas is 320 wide, which is a small
  drawing surface. Mitigation: choose the font first and take a larger canvas with larger text
  (14px → 373, 16px → 426) where a concept needs room. If a concept cannot be drawn legibly at any
  permitted combination, that is a finding to report, not a reason to lower the floor.
- **Figure 2 is where truthfulness will be tempted.** A ladder with one clean arrow per tier is
  prettier than one admitting the top tier leaks. Requirement 10 exists because the draft already
  made that mistake once; the test asserts the wording so tidiness cannot quietly win.
- **The 320 divisor could rot.** Asserted against the stylesheet, not hard-coded.
- **Page weight.** Three figures at draft sizes (4.7–6.8 KB) land near 60 KB total, inside the
  75,000 budget, but a fourth figure would not fit — a real reason the spec ships three.
- **Existing ids could collide.** The page already carries ids; the duplicate-id check covers the
  whole document, not only the figures.
- **Previews drawn outside this repository are not evidence.** Any preview shown before this plan is
  accepted is illustration only; the figures that ship are the ones `verify.py` certifies here.

Rejected alternatives: adopting the existing drafts as-is (the closest misses the formula by 1.3px);
external SVG files; a `<style>` block per figure; a desktop variant per concept; and relaxing the
12px floor. All argued in `spec.md`.

---
Gate: engineer accepts BEFORE `index.html` is edited. If implementation departs from this plan,
update it and obtain renewed acceptance.
