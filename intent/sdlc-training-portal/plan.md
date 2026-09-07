# Plan: a training portal that teaches the AI-native SDLC by enforcing it

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 55b979fdb5a34b6738fdede2a23b04e868d0d5f3
- **Status:** accepted

This repository has no remote yet and no merge base, because the owner creates the repository
(spec Q2). `Accepted-for` therefore binds to the commit that is `HEAD` when the plan is
accepted — the base this plan's approval covers. Once a remote exists, later changes bind to
`git merge-base origin/main HEAD` as normal.

## Files changed (in order of work)

1. `verify.py` — the verification target: structure, isolation, required content markers, and the
   forbidden-overclaim list. Written and observed failing first.
2. `index.html` — the portal itself, single file, inline CSS and JS, at the repository root.
3. `README.md` — what the repository is, how to verify it locally, how it is published, and the
   disambiguation that it is a training site rather than the skill's source.
4. `.gitignore` — exclude `__pycache__/` so a local `verify.py` run leaves no residue.

No `.github/workflows/` in this change: GitHub Pages publishes from the branch root directly, and
a CI job would need the repository to exist first. Adding CI is a separate follow-up once the
remote is live.

## Work order

1. **Reconfirm the gate.** Build gate open on a *committed* signed-off spec, tree clean.
2. **Red first.** Write `verify.py` against the spec's requirements. Run it with no
   `index.html` present; it must exit non-zero reporting the missing file and the unmet markers
   as findings, not as a traceback. Commit this red target alone.
3. **Build the page skeleton** — landmarks, one `h1`, skip link, the nine sections in the order
   fixed by spec design 1, with the disambiguation line in the hero.
4. **Write the six stage panels** as full markup inside the tablist, all present in the document
   so nothing is script-gated. Each panel states the shift, the artifact, the gate and its
   holder, and the measures.
5. **Write the enforcement section** — the three strengths, the "not required is not a gate"
   statement, and the three failure modes.
6. **Write the lab and its exercises** — install, mark the check required, intent, watch the gate
   refuse, plan with the merge-base binding, red-then-green, PR, close as `shipped`; plus one
   observable exercise per trap.
7. **Write the honest-limits section** — four positions with two marked not achieved, 36/80
   (45%), the ~48% ceiling, the three enterprise-owned controls, and what documentation does not
   buy.
8. **Add the tab script and the quiz** — roving `tabindex` with Left/Right/Home/End, ARIA state
   only; the quiz built into an empty container with a `<noscript>` explanation.
9. **Green the target.** Run `verify.py` until it passes without weakening any check. Where a
   check is wrong rather than the page, fix the check and say so in the commit.
10. **Manual accessibility pass** that `verify.py` cannot do: tab through every control with the
    keyboard only, confirm visible focus throughout, disable JavaScript and confirm all six
    panels' content is readable, and check contrast of the actual colour pairs used.
11. **Write `README.md` and `.gitignore`.** Commit the implementation.
12. **Hand off.** The owner creates the repository named `ai-native-sdlc`, pushes `main`, and
    enables Pages from branch `main`, path `/`. The agent supplies the exact commands and does
    not run them.
13. **Owner confirms the live URL** renders, then closes the chain as `shipped`.

## Tests that prove it

### Red-first target

```sh
python3 verify.py     # before index.html exists: non-zero, findings not a traceback
```

### Green, with counted checks

```sh
python3 verify.py     # after implementation: exit 0
```

Pass condition: exit 0, and the run prints the number of checks performed so a silently empty
verification is visible. Minimum coverage, each an independent check:

- `index.html` exists, is valid enough to parse, sets `lang`, and has exactly one `h1`;
- a skip link targets an existing id; `main`, `nav`, `footer` landmarks present;
- **six** elements with `role="tab"`, **six** with `role="tabpanel"`, every `aria-controls`
  resolving to a real panel id, every panel labelled by its tab, exactly one tab with
  `aria-selected="true"`, and a roving `tabindex`;
- zero external references: no `src=`, no stylesheet `href=`, no `fetch(`, no
  `XMLHttpRequest`, no `@import` pointing outside the file;
- content markers present in the **text**, not the markup: the six stage names; the six artifact
  names (`intent.md`, `spec.md`, `plan.md`, `evals/`, `REVIEW.md`, `bands.yaml`); the four trap
  markers; the four adoption positions with `Not achieved` present twice; `36/80`, `45%`, `48%`;
  the three enterprise-owned controls; `Louis Claxton`; both source links; and the
  disambiguation sentence;
- forbidden phrases absent: `enterprise-ready`, `fully compliant`, `independently audited`,
  `certified`, `production-proven`, `SOC 2`, and `guarantees compliance`.

### Manual checks recorded in the implementation commit

Keyboard-only traversal, visible focus, no-JS panel readability, and the contrast pairs measured.
These are stated as done with what was checked, not implied.

### Isolation

```sh
grep -nE 'https?://' index.html | grep -vE '<a |href="https://(claude\.com|github\.com)' || true
```

Pass condition: no external URL appears anywhere except inside anchor hrefs to the two sources.

## Risks

- **`verify.py` could pass on an empty page.** It must print its check count, and the content
  markers must be asserted against extracted text so an HTML comment cannot satisfy one.
- **The tab script could hide content for no-JS readers.** Panels ship visible; only the script
  applies `hidden`. Verified by disabling JavaScript in step 10, not by reasoning about it.
- **Reusing the pre-process prototype could smuggle unreviewed claims.** Every reused block must
  map to a spec requirement; the prototype's own brand name and any claim not in the sources are
  dropped.
- **Over-claiming by omission.** The honest-limits section sits before the self-check so a reader
  who stops early still meets it, and the disambiguation is in the hero rather than the footer.
- **Binding with no remote.** `Accepted-for` binds to the accepted `HEAD`; recorded explicitly
  above so a later reader does not read it as a merge base.

Rejected alternatives: a generator or framework, multi-page, committing the prototype wholesale,
script-gated stage content, a CI check that fetches the live URL, and softening the limits. All
argued in `spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs from
this plan, update it and obtain renewed acceptance.
