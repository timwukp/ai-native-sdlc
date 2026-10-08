# Spec: give the six Stage plays links distinct names and correct the README layout

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Status:** draft

## Measured baseline

Measured at `e929979` (current `main`).

- `index.html` is 84,989 bytes against its 85,000-byte cap. Each of the six stage tabpanels
  (`role="tabpanel"`, `data-stage` = `plan`, `design`, `build`, `test`, `deploy`, `maintain`) ends
  with exactly one `<a href="plays.html#<stage>">Stage plays</a>`. The six links share one
  accessible name and differ only in `href`.
- `verify.py` `index_play_link_checks()` asserts that each panel links its own `plays.html`
  section exactly once. It does not look at the link text, so six identical names pass.
- Replacing each name with `<Stage> plays` (capitalised stage name) measures 84,992 bytes, +3.
- The `README.md` Layout block lists four entries: `index.html` ("the entire site: markup, CSS and
  JS inline, no dependencies"), `verify.py`, `intent/` and `.sdlc/`. The tracked tree also holds
  `plays.html`, `evals/`, `scripts/`, `.githooks/`, `.privacy-allowlist.json`, `.github/` and
  `.kiro/`. No `verify.py` check reads the Layout block.
- Portal verifier: 384/384. Catalogue mutations: 11/11 killed.

## Requirements

### Link names

1. The six stage links read exactly `Plan plays`, `Design plays`, `Build plays`, `Test plays`,
   `Deploy plays` and `Maintain plays`, in that panel order, as the link's visible text. The
   `href` of each link is unchanged.
2. No `aria-label`, `aria-labelledby` or `title` is added to these links, so the visible text is
   the accessible name (intent decision 1).
3. No other byte of `index.html` changes. `index.html` stays at most 85,000 bytes; the expected
   size is 84,992. If it exceeds the cap, work stops and returns to the product owner; the cap is
   not raised.
4. `plays.html` is not changed.

### Verifier

5. `index_play_link_checks()` gains one check, `index plays: stage links have distinct names that
   name their stage`. For every stage panel it takes the visible text of the panel's
   `plays.html#<stage>` link, whitespace-collapsed. It fails if any two names are equal
   (case-insensitive), or if a name does not contain its stage name as a whole word
   (case-insensitive). The failure detail lists the offending stages and names.
6. `verify.py` gains one README check, `README layout: lists the published tree`. Inside the
   fenced block under `## Layout`, every top-level tracked entry (`index.html`, `plays.html`,
   `verify.py`, `intent/`, `.sdlc/`, `evals/`, `scripts/`, `.githooks/`,
   `.privacy-allowlist.json`, `.github/`, `.kiro/`) begins a line, and the block does not contain
   the phrase `entire site`. The list is a constant in `verify.py`, not derived from `git
   ls-files`, so the verifier stays standard-library and runs on an unpacked copy.
7. Both checks are written first and observed failing on the unchanged `index.html` and
   `README.md`, with every other check still green and no traceback. That red state is committed on
   its own.
8. One catalogue mutation is added to `MUTATIONS`: rename the `build` stage link back to `Stage
   plays`. It must turn requirement 5's check red, giving 12/12 killed. The README check has no
   mutation, because the mutation runner exercises only the catalogue inputs (`index.html`,
   `plays.html`, source and baseline); its red-first observation in requirement 7 is its evidence.

### README

9. The Layout block lists each entry from requirement 6 with a one-line purpose. `index.html` is
   described as the home page and course, not the entire site. `plays.html` is described as the
   Playbook play catalogue. Nothing else in `README.md` changes except what this requires.

## Verification

- Portal verifier all green, including the two new checks; catalogue mutations 12/12 killed.
- Privacy unit tests passing; privacy mutation proof 13/13 killed; tracked-tree scan 0 findings;
  pre-push hook over every unpushed commit 0 findings.
- The overlap ratchet still holds: `index.html` has 0 source matches outside the baseline, and the
  baseline is unchanged.
- Rendered verification against the immutable commit (intent criterion 4): at 360 and 1440px, the
  accessibility tree lists the six names from requirement 1, each link lands at the top of its
  `plays.html` section, and the console shows no errors or warnings. A screen reader itself is not
  run; the accessibility tree is the evidence.

## Allowed files

`index.html`, `README.md`, `verify.py`, `.sdlc/active` and this chain's artifacts. `plays.html`,
`evals/`, `scripts/`, `.githooks/`, `.privacy-allowlist.json`, `.github/` and `.kiro/` are not
changed.

## Flagged concerns

- **The README list goes beyond the intent's five named entries.** The intent names `plays.html`,
  `evals/`, `scripts/`, `.githooks/` and `.privacy-allowlist.json`. Measurement found `.github/`
  (workflows and the PR template) and `.kiro/` (the write-time privacy hook config) are tracked
  too. Leaving them out would keep the block incomplete, so they are included.
- **The README check uses a hard-coded list.** A new top-level path added later will not fail it
  until someone adds it to the constant. Deriving the list from Git would make the verifier depend
  on a repository checkout, which it does not today.
- **Headroom after this change is 8 bytes.** The next intent that touches `index.html` must
  settle the cap first.

---
Gate: product owner signs off. The sign-off commit is the record.
