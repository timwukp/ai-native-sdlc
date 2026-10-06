# Plan: add a verified play catalogue beside the portal

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 514366c8b9d99e38b7fa17e4547ce61e9c713581
- **Status:** accepted
- **Revision:** 3 — steps 6, 8, 24 and the success criteria follow spec revision 3: the overlap
  check exempts the 16 required play headings, and an eleventh mutation proves the exemption
  does not widen. Re-acceptance required.
- **Revision 2:** steps 15 and 25 revised after step 16 measured `index.html` over the cap.
  Plays links carry no learning marker; the cap stays 85,000. Steps 3 and 12 revised after the
  privacy scan found 49 payment-card false positives in the hex fixtures; hashes are stored as
  base32. Re-acceptance required.

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time. It binds review to protected
`main` after the mentor/self-paced closeout, not to this branch's artifact commits.

## Files changed (in order of work)

1. `.sdlc/active`: already points at `playbook-play-coverage`.
2. `intent/playbook-play-coverage/intent.md`, `spec.md`, `plan.md`: this chain (Issue #17).
3. `verify.py`: red-first `plays` group, `index.html` link and out-of-scope parity checks, the
   source-overlap ratchet, two fixture-builder modes and an in-memory mutation mode.
4. `evals/source-shingles.txt` (new): SHA-256 hashes of the source's eight-word windows only.
5. `evals/index-source-overlap-baseline.txt` (new): hashes of windows already shared by
   `index.html` at `514366c`.
6. `index.html`: one header-nav link, six stage links, the rewritten "does not cover" note.
7. `plays.html` (new): the 16-play catalogue.
8. `README.md`: one link to the catalogue.

Explicitly unchanged: workflows, privacy scanner/rules/allowlist/hooks, the SDLC gate, PR
template, branch protection, the Mentor/Self-paced UI, storage schema, the six questions, figures,
tables and every shipped chain. No generator script, Playwright script or screenshot is committed;
fixtures are built by `verify.py` itself so the builder and the checker share one normaliser.

## Work order

### A. Accept the plan and commit the red contract

1. **Reconfirm state.** Intent accepted, spec signed off (revision 2, `ceecc1a`), Build gate open,
   merge base equals `Accepted-for`, privacy scan clean, Portal 314/314, Git identity is the GitHub
   noreply identity, `.kiro/settings/` the only untracked path.
2. **Accept this plan.** The owner replaces `pending`/`draft`; the acceptance commit must open the
   Test gate before `verify.py` changes.
3. **One normaliser.** Add `shingles(text)`: lower-case, replace every non-alphanumeric run with a
   space, collapse whitespace, emit every eight-word window, SHA-256 each window and encode the
   digest as lowercase unpadded base32 (52 characters). Text comes from
   the existing stdlib `Page` extractor (markup text, excluding `<script>` and `<style>`).
4. **`plays` checks (spec 1, 3, 5-17, 20-21).** Load `plays.html` if present; when absent, emit named
   `plays:` findings, never a traceback. Assert: byte cap 55,000; no `<script>`, no external
   `src`/`href` asset or runtime request; skip link first, one `h1`, no skipped heading level,
   `lang="en"`, viewport meta, reduced-motion rule, print rule; exactly the 16 ids in spec order
   with `data-play`, `data-stage`, source heading and stage section; the seven `data-field`
   fields in order; status is one of three values, matches the spec table, appears as visible text
   and as `data-status`; every `implemented`/`partial` evidence path exists (glob patterns such as
   `intent/*/plan.md` must match at least one file); `partial` carries `gap`, out of scope carries
   `reason`; the two `data-crosscut` notes appear once each and not as plays; `#out-of-scope`
   lists exactly the out-of-scope ids; `#dependency-list` equals the spec edge table (kind
   included); each entry's prerequisite links equal its incoming edges; the SVG has `role="img"`,
   `<title>`, `<desc>`, caption and an edge set equal to the list; `required`/`helps` differ by
   dash pattern; glossary has the 14 required terms with no duplicate `term-` id; the terminology
   map has the eight rows, each naming an existing path or exactly "No counterpart"; wide tables sit
   in a labelled `tabindex="0"` scroll region; no `<pre>` reproduces a source code sample.
5. **`index.html` checks (spec 2, 12).** Assert the 85,000-byte cap still holds, one header link to
   `plays.html`, one link per stage panel to `plays.html#<stage>`, the note heading kept, and the
   `data-oos` id set equal to `plays.html`'s out-of-scope set in both directions, plus both
   `data-crosscut` names.
6. **Overlap ratchet (spec 19).** Read both fixtures; missing fixtures are named findings. Require
   `plays.html` windows ∩ source = ∅, after removing the text of each entry's first heading only
   where it equals that entry's spec play name exactly (spec 19). Require every `index.html` hit to be in the baseline, every
   baseline hash to still hit, and the baseline line count ≤ the count in its header. Print the
   baseline count and each baseline hit's eight words (from `index.html`, not the source).
7. **Fixture builders.** `--build-source-shingles FILE` reads the fetched source page, extracts
   text with the same `Page` extractor and writes sorted unique hashes with a header (source URL,
   source date 2026-08-21, fetch date, command, count). `--build-overlap-baseline` reads
   `git show 514366c:index.html` and writes the sorted intersection with the same header shape.
   Both are deterministic: rerunning on the same input yields identical bytes.
8. **Mutation mode (spec 24).** `--mutations` applies each of the eleven spec mutations to in-memory
   copies of pages/fixtures and requires each to produce its named finding; it exits 0 only if 11/11
   are killed. Every mutation anchors on a string the verifier first asserts is present, so a moved
   anchor fails loudly instead of silently disabling the mutant. It never writes to the tree.
9. **Observe red.** `python3 verify.py` fails with named `plays:`/`overlap:`/`index plays:` findings
   only; all 314 existing checks stay green. Record counts.
10. **Commit the red verifier alone.**

### B. Commit the fixtures

11. **Fetch and build in one shell invocation.** Download the source page into scratch, pipe it to
    `--build-source-shingles`, then delete it in the same invocation. The source text is never
    staged. Build the baseline from `514366c`.
12. **Inspect.** Fixtures contain only header comments and 52-character base32 lines; `git grep`
    finds no source sentence in `evals/`; `scripts/privacy_scan.py --repo .` over the tracked tree
    and the pre-push hook over every unpushed commit both report 0 findings. Hex encoding is
    rejected: digit runs inside hex digests match the payment-card rule. Record both counts.
13. **Observe partial green.** Overlap checks for `index.html` now pass on the baseline;
    `plays:` findings remain. Commit the two fixtures alone.

### C. Change `index.html` first, because its 445-byte headroom is the tightest constraint

14. **Rewrite the note shorter.** Keep the heading; name the six out-of-scope plays as `data-oos`
    anchors and the two cross-cutting notes with `data-crosscut`. New prose must add no hash
    outside the baseline.
15. **Add links.** One header-nav link to `plays.html`, one short "Stage plays" link at the end of
    each panel. The links carry no `data-learning-addition` marker: that marker means learning-mode
    content, no stylesheet, script, workflow or check reads it on a link, and the `index plays:`
    checks find the links by `href`. The note opens "Out of scope:" and keeps the phrases
    "recurring security scans" and "legacy-system onboarding" that existing checks require.
16. **Measure.** If `index.html` exceeds 85,000 bytes, stop and return to the owner. Do not trim
    other lessons, minify, or raise the cap. All prior 314 checks stay green.

### D. Build `plays.html`

17. **Shell.** Reduced copy of the portal's tokens, type scale, skip link, focus style, header,
    touch-target rule, reduced-motion and print rules; links back to `index.html` and its panels.
18. **Sixteen entries.** Written in the portal's own words from the source read for the spec; the
    three plays without source sections use "Not stated in the source". Statuses, evidence, gaps
    and reasons exactly as spec requirement 10. The two interpretive edges are labelled on the page.
19. **Out of scope, cross-cutting notes, dependency list, figure, glossary, terminology map.** The
    figure is a narrow mobile-first `viewBox`; measure effective minimum text size at 360px before
    committing it. Status words are visible text and print.
20. **Overlap loop.** Run the verifier after each stage section; rewrite any window that hits.
    Never add a hash to a fixture to clear a hit.
21. **Measure.** If `plays.html` exceeds 55,000 bytes, stop and return to the owner.
22. **README.** One link line to `plays.html`.

### E. Prove it locally and commit

23. `python3 verify.py` exits 0; output shows 16 plays, 4/6/6 statuses, edge count, figure edge
    count, glossary size, `plays.html` 0 hits, `index.html` 0 hits outside baseline, baseline count,
    both page sizes.
24. `python3 verify.py --mutations` reports 11/11 killed.
25. Mentor/Self-paced contracts remain green; the canonical-text comparison against
    `origin/main:index.html` (additions removed) differs only in the rewritten note and the seven
    plays links (one header-nav, six stage).
26. Privacy tests (31), privacy mutation proof (10/10), staged full-tree privacy scan (0 findings),
    `py_compile`, `git diff --check`, SDLC CI gate with `--require-active`, the real changed-file
    list and base `514366c…`.
27. Diff scope equals the file list above; commit implementation separately from the red and
    fixture commits.

### F. Draft PR and rendered evidence

28. Run the checked-in pre-push hook with a correct stdin line; inspect author/committer metadata
    manually until Issue #12 ships.
29. **Owner pushes** `feat/playbook-play-coverage`; the agent does not run `git push`. After the
    remote SHA matches, the agent opens a Draft PR linked to Issue #17.
30. Against the immutable commit URL: `plays.html` screenshots at 360/768/1440 and inspected;
    overflow metrics at 360/768/1024/1440; keyboard from skip link through all 16 entries and the
    scroll regions; JavaScript disabled; print with PDF generation; console zero; each `index.html`
    stage link lands on the matching `plays.html` section and the back links return.
31. `portal verify`, `privacy scan`, `sdlc-gate / sdlc-gate` all `SUCCESS`. Only then mark Ready.
    The owner reviews and merges; the agent neither approves nor merges.
32. After merge: confirm Pages serves `plays.html`, then an artifact-only closeout PR marks this
    chain `shipped`.

## Tests that prove it

```sh
python3 verify.py
python3 verify.py --mutations
python3 -m unittest discover -s scripts -p 'test_privacy*.py'
python3 scripts/privacy_mutation_proof.py
python3 scripts/privacy_scan.py --repo .
python3 -m py_compile verify.py scripts/privacy_scan.py scripts/privacy_pretooluse_hook.py
git diff --check
```

Pass conditions: red commit fails with named findings only and 314 prior checks green; final run
exits 0; 16 plays with statuses 4/6/6; `plays.html` ≤ 55,000 and `index.html` ≤ 85,000 bytes;
`plays.html` 0 overlap hits; `index.html` 0 hits outside a baseline no larger than at `514366c`;
11/11 new mutants and 10/10 privacy mutants killed; 0 privacy findings; SDLC gate passes naming
every changed file; noreply identity; `.kiro/settings/` unstaged.

## Risks

- **`index.html` headroom.** 445 bytes for eight links and a note naming six plays is tight; C is
  ordered first so a stop costs no catalogue work.
- **Source page drift.** The fixture is a snapshot; its header records the fetch date. CI uses only
  the committed hashes and makes no network request.
- **Extractor scope.** Text rendered by JavaScript (the six questions in `index.html`) is not in the
  `Page` text, so the overlap check does not cover it. The baseline uses the same extractor, so the
  ratchet is consistent; the gap is reported in the PR, not hidden. `plays.html` has no script.
- **Status claims.** A wrong status is a false public claim; spec table values are asserted exactly
  and evidence paths must exist.
- **Figure legibility.** A wide `viewBox` cannot be fixed with font size; measure at 360px first.
- **Mutant disabled by a moved anchor.** Each mutation asserts its anchor exists before mutating.
- **Commit metadata.** Outside the tree scanner until Issue #12; inspected manually.

## Rejected alternatives

Committing source sentences, a separate generator script, a network fetch in CI, adding
`CLAUDE.md` or other files to turn a status green, adding hashes to clear a hit, minifying
`index.html`, raising either cap during implementation, JavaScript on `plays.html`, and
mutable-preview evidence.

---
Gate: the owner accepts BEFORE `verify.py`, fixtures, `index.html` or `plays.html` is edited. Any
departure requires a plan amendment and renewed acceptance.
