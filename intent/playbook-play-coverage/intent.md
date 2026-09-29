# Intent: cover every Playbook play in the portal

- **Slug:** playbook-play-coverage
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Date:** 2026-09-29
- **Status:** draft
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/17

## Problem

The portal teaches the six stages of the source Playbook (Plan, Design, Build, Test, Deploy,
Maintain), but not the plays inside them. The source, dated 2026-08-21, has 16 named play
sections, plus a legacy-systems sidebar and a managed-settings worked example:

- **Plan:** Capture as `intent.md`.
- **Design:** Requirements and design.
- **Build:** Plan mode as the default starting point; auto mode; `CLAUDE.md`; skills as
  institutional knowledge; hooks as build-time guardrails; parallel sessions and subagents.
- **Test:** Give Claude a feedback loop; continuous evals in CI.
- **Deploy:** AI in the PR review loop; hooks as approval gates; CI/CD integration and deployment.
- **Maintain:** Closing the loop; recurring codebase scans; Claude on call with Claude Tag.

Most of these are absent from the page. Plan mode, `CLAUDE.md`, skills as institutional
knowledge, parallel sessions, the feedback loop, CI/CD and MCP deployment, recurring scans and
Claude Tag each get zero mentions. The Playbook gives every play prerequisites, a governance
consideration, and leading and lagging indicators. The portal shows none of this per play, and
it does not show the prerequisite dependency graph either.

The existing "What this deliberately does not cover" note lists four unmapped areas as prose. No
one can check it against the source, so it can drift silently from both the Playbook and the
repository. The page also has no glossary, and no map from Playbook terms (`CLAUDE.md`,
`.claude/skills`, `.claude/settings.json` hooks, `REVIEW.md`, `bands.yaml`) to the mechanisms
this repository actually uses.

`index.html` is at 84,555 of its signed-off 85,000 bytes. Play coverage cannot fit on the
current page without changing the page architecture or the budget.

## Desired outcome

A learner can see every play in the source and, for each one:

1. what it changes, in the portal's own words, attributed to the source stage;
2. its prerequisites, as links to other plays;
3. its governance consideration and its leading/lagging indicators;
4. where this repository stands on it: **implemented**, **partial**, or **declared out of
   scope**, with a concrete evidence pointer (a file, gate or section) or a stated reason.

The play dependency graph appears as an accessible figure with an equivalent text list. A glossary
defines the recurring terms once. A terminology map pairs each Playbook term with the mechanism
this repository uses, or says honestly that there isn't one.

The existing "does not cover" statement is generated from, or checked against, the
catalogue's out-of-scope entries, so the two cannot disagree.

## Affected users / systems

- Learners and mentors using the six-stage course, who need a route from each stage to its plays.
- Adopters deciding which plays to take on first, who need prerequisites and repo status.
- `index.html`, which must link to the catalogue within its existing budget.
- A new catalogue page, if accepted (see recommended decisions).
- `verify.py`, which must enforce closed-set play coverage, status/evidence completeness, graph
  consistency, glossary/terminology integrity, and the budgets.
- The `portal verify`, `privacy scan` and `sdlc-gate` workflows, which must stay green without
  changes.

## Constraints

- Paraphrase only. Do not reproduce Playbook prose, prompts or code samples verbatim beyond
  identifiers and file names. Every stage section attributes and links the source.
- Stay faithful to the source's own stage and play names. Do not invent a taxonomy.
- Stay dependency-free: static HTML with inline CSS, no build step, no runtime request, no
  external asset, no analytics.
- A status claim needs evidence. **Implemented** must point to a real artifact in this repository
  that the verifier can check exists. **Partial** must say what is missing. **Declared out of
  scope** must give a reason.
- Do not claim a control that the repository cannot grant itself. The existing honest-limits
  section still governs managed settings, audit sinks and independent assurance.
- Keep the PR #11 and PR #14 guarantees on every page touched: no overflow at 360/768/1024/1440px,
  44px compact targets, keyboard/focus/skip-link, reduced motion, print, readable without
  JavaScript, and the learning-mode/progress behavior unchanged.
- Every page keeps a hard byte budget. Any increase must be measured and signed off in the spec,
  not discovered during implementation.
- Rendered evidence and fixtures contain no personal data, local machine paths or credential-shaped
  values. The existing privacy scanning stays active.
- The agent does not push, accept its own artifacts, approve the PR or merge.

## Success criteria

1. The catalogue enumerates exactly the closed set of play sections fixed in the spec. The verifier
   fails on a missing, duplicated or invented play.
2. Every play entry has a stage, a paraphrased summary, prerequisites, a governance note, leading
   and lagging indicators, and exactly one repo status.
3. Every **implemented** evidence pointer resolves to a path or anchor that exists at the commit
   under test. Every **partial** entry names its gap. Every **declared out of scope** entry gives a
   reason.
4. The "does not cover" statement and the out-of-scope entries agree. The verifier fails on any
   disagreement.
5. Prerequisite links resolve to catalogue entries. The dependency figure and its text equivalent
   show the same edges, and those edges match the prerequisites.
6. Each of the six stage panels links to its plays. Mentor and Self-paced behavior, storage schema
   and the 314 existing Portal checks are unchanged.
7. The glossary defines each term once. Every terminology-map row names a Playbook term and either
   an existing repo mechanism (verified to exist) or an explicit "no counterpart".
8. No sentence of eight or more words is copied verbatim from the source. The verifier checks this
   against a committed list of source phrases.
9. Every touched page stays within its signed-off byte budget and meets the responsive,
   keyboard, no-JavaScript, reduced-motion and print contracts.
10. Verification is added red first. Portal, privacy tests, mutations, full-tree scan and the SDLC
    gate stay green.
11. Rendered evidence against an immutable commit URL covers the catalogue at 360/768/1440px,
    keyboard traversal, no-JavaScript, print and console.
12. After merge, an artifact-only PR marks this chain shipped before PR 4 begins.

## Recommended decisions awaiting owner acceptance

1. **Delivery surface:** add a separate static `plays.html` catalogue with its own byte budget
   (measured and fixed in the spec). `index.html` gains only per-stage links and a nav entry, and
   stays within 85,000 bytes. Raising `index.html` to about 115 KB would slow the mobile course
   page, and so would compressing 16 plays into it.
2. **Closed play set:** 16 play entries in the source's order. The legacy-systems sidebar and the
   managed-settings worked example are cross-cutting notes, not plays.
3. **Status vocabulary:** exactly three values (implemented / partial / declared out of scope).
   Status is judged against this repository's committed artifacts, never against intent.
4. **Out-of-scope statement:** the index note keeps its prose but must name exactly the entries
   marked declared out of scope. The verifier enforces equality.
5. **Dependency graph:** one inline SVG sized for the mobile-first canvas, plus an ordered text
   list. The text list is canonical and the figure must match it.
6. **Copyright discipline:** paraphrase with per-stage attribution. The verifier runs a
   verbatim-overlap check against a small committed file of source sentences used only for testing.
   No source code samples are reproduced.
7. **No new interactivity:** the catalogue is fully readable without JavaScript. Mentor and
   Self-paced modes and progress storage are not extended to it in this PR.

## Out of scope

- A full worked example or assessment redesign (PR 4).
- Commit-metadata privacy scanning (Issue #12).
- Changes to privacy rules, the SDLC gate, workflows, branch protection or deployment.
- Localization, search, filtering, accounts, analytics or any runtime request.
- Implementing plays in this repository (for example adding a `CLAUDE.md` or evals) just to turn a
  status green. Status reports reality; it does not drive scope.

---
Gate: product owner accepts. The accepting commit is the record.
