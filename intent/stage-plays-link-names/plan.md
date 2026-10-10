# Plan: give the six Stage plays links distinct names and correct the README layout

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** e929979bff8b161314e83fc6b1db5fb756e88810
- **Status:** shipped

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time, the value the CI gate
compares. It is also the current `origin/main`.

## Files changed (in order of work)

1. `.sdlc/active`: already points at `stage-plays-link-names`.
2. `intent/stage-plays-link-names/intent.md`, `spec.md`, `plan.md`: this chain (Issue #23).
3. `verify.py`: red-first link-name check (spec 5), README layout check (spec 6), and one
   catalogue mutation (spec 8).
4. `index.html`: six link texts (spec 1-3).
5. `README.md`: the Layout block (spec 9).

Explicitly unchanged: `plays.html`, `evals/`, `scripts/`, `.githooks/`,
`.privacy-allowlist.json`, `.github/`, `.kiro/`, the SDLC gate and every shipped chain.

## Work order

### A. Accept the plan and commit the red contract

1. The product owner accepts this plan; the acceptance commit is the record.
2. Add `index plays: stage links have distinct names that name their stage` to
   `index_play_link_checks()`. Names are the visible text of each panel's `plays.html#<stage>`
   link, whitespace-collapsed; equality and the whole-word stage match are case-insensitive.
3. Add `README layout: lists the published tree` beside the existing README checks. It reads the
   first fenced block after `## Layout`, requires each entry of a `LAYOUT_ENTRIES` constant to
   begin a line, and requires the block not to contain `entire site`. A missing heading or block
   is a named failure, not a traceback.
4. Add the mutation `rename the build stage link to "Stage plays"` to `MUTATIONS`, anchored on
   the `plays.html#build` link, expecting the link-name check.
5. Run `python3 verify.py`. Expected: exactly the two new checks fail, with every other check
   green and no traceback. `python3 verify.py --mutations` cannot show the new mutation killed
   yet, because its target check is already red; that is expected and recorded.
6. Commit `verify.py` alone as the red contract.

### B. Fix the page and the README

7. Replace the six link texts with `Plan plays` through `Maintain plays`. Nothing else in
   `index.html` changes. Measure: expected 84,992 bytes. Over 85,000 stops the work and returns
   to the product owner.
8. Rewrite the README Layout block with one line per entry, describing `index.html` as the home
   page and course and `plays.html` as the Playbook play catalogue. No other README line changes.
9. Run `python3 verify.py`: all green. Run `python3 verify.py --mutations`: 12/12 killed.

### C. Prove it locally and commit

10. Privacy unit tests passing, privacy mutation proof 13/13 killed, tracked-tree scan 0 findings.
11. Confirm the overlap ratchet: 0 `index.html` source matches outside the baseline, baseline
    unchanged.
12. `git diff --check`, no host paths, and every changed file on the spec's allowed list.
13. Commit `index.html` and `README.md`, then run the pre-push hook over every unpushed commit:
    0 findings.

### D. Draft PR, CI, rendered checks

14. The product owner pushes the branch. The agent opens a Draft PR for Issue #23 and waits for
    `portal verify`, `privacy scan` and `sdlc-gate`.
15. Rendered checks against the files at the PR head commit, confirmed byte-identical to GitHub's
    copies by blob SHA: at 360 and 1440px the accessibility tree lists the six names in panel
    order, each link lands at the top of its `plays.html` section once scrolling settles, and the
    console has no errors or warnings.
16. Only when all of that passes is the PR marked Ready. The product owner merges. An
    artifact-only closeout PR then marks intent, spec and plan `shipped`.

## Tests that prove it

- The two new checks, seen red on the unchanged files (step 5) and green after the fix (step 9).
- The new mutation: restoring one `Stage plays` name turns the link-name check red (12/12).
- The full existing verifier (384 checks) and privacy suite stay green.
- The rendered accessibility-tree read for the user-visible effect.

## Risks

- **The stage-name match could pass a bad name.** "Test plays" contains `test` as a whole word,
  but so would an unrelated "Test this". The check pairs the whole-word match with distinctness
  and the exact names are fixed by spec 1; the risk is accepted.
- **The README check list can go stale** when a top-level path is added later (spec flagged
  concern).
- **8 bytes of headroom remain** on `index.html` after this change.

## Rejected alternatives

- **`aria-label` on the existing text:** different spoken and visible names, about 150 bytes,
  over the cap (intent decision 1).
- **Deriving the README list from `git ls-files`:** makes the verifier depend on a Git checkout.
- **A README mutation:** the mutation runner exercises only catalogue inputs; extending it to
  README is outside the allowed scope (spec 8).
