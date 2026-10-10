# Intent: give the six Stage plays links distinct names and correct the README layout

- **Slug:** stage-plays-link-names
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-10-08
- **Status:** accepted
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/23

## Problem

`playbook-play-coverage` added one link at the end of each stage panel in `index.html`, pointing
to that stage's section of `plays.html`. All six links have the same accessible name, "Stage
plays". A screen-reader user who lists the page's links hears that name six times, with six
different destinations, and cannot tell them apart. The rendered verification for that chain
recorded this as an open defect.

The README's Layout block still describes `index.html` as "the entire site". The repository now
also publishes `plays.html` and carries `evals/`, `scripts/`, `.githooks/` and
`.privacy-allowlist.json`, none of which the block lists.

## Desired outcome

Each of the six links has a name that identifies its destination on its own, and the README
Layout block lists what the repository actually contains.

## Affected users / systems

- Screen-reader and voice-control users of the portal home page.
- Contributors reading the README to orient themselves.
- `index.html`, `README.md`, and `verify.py`, which checks the six links.

## Constraints

- No new content, no layout or style change, and no change to `plays.html`.
- `index.html` stays within its signed-off 85,000-byte cap. It is at 84,989 bytes now; the
  measured cost of the recommended names is +3 bytes (84,992).
- Link names reuse the canonical stage names already on the page (Plan, Design, Build, Test,
  Deploy, Maintain); no new vocabulary.
- `verify.py` gains a check, written and observed failing first, that the six names are distinct
  and each names its stage, so the defect cannot return.
- The agent does not push, self-approve artifacts, or merge.

## Success criteria

1. The six links read "Plan plays", "Design plays", "Build plays", "Test plays", "Deploy plays"
   and "Maintain plays", each linking to its own section, and `verify.py` fails if any two names
   repeat or a name omits its stage.
2. `index.html` is at most 85,000 bytes.
3. The README Layout block lists `plays.html`, `evals/`, `scripts/`, `.githooks/` and
   `.privacy-allowlist.json` with a one-line purpose each, and no longer calls `index.html` the
   entire site.
4. Rendered verification against the immutable commit shows the six names in the page's
   accessibility tree, with the links still landing on the right sections.
5. The chain closes as `shipped` through an artifact-only pull request.

## Decisions proposed for acceptance

1. **Visible text, not `aria-label`.** Changing the link text fixes the name for every user,
   including voice control ("click Build plays"), and costs 3 bytes. An `aria-label` would leave
   sighted users with a different label from the spoken one and cost about 150 bytes, which the
   cap cannot absorb.
2. **One chain for both defects.** Both are small corrections to `playbook-play-coverage`
   output; splitting them would double the review overhead for a README line.
3. **Issue #20 waits.** It starts only after this chain ships, because the SDLC gate allows one
   active intent at a time.

---
Gate: product owner accepts. The accepting commit is the record.
