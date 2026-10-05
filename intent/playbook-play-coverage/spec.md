# Spec: a play catalogue for every Playbook play

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Status:** draft
- **Revision:** 3 — requirement 19 exempts the 16 play headings that requirement 5 fixes verbatim,
  after implementation measured that the nine-word name of play 3 itself contains a source
  window. Revision 2 revised requirements 19, 23 and 24 to a ratchet after measurement showed
  the merged `index.html` already shares eight-word windows with the source. Re-sign-off
  required.

## Measured baseline

- `index.html` is 84,555 bytes against its signed-off 85,000-byte cap, leaving 445 bytes.
- The six stage panels (`p1`–`p6`, `data-stage` plan…maintain) teach stages only. No play has an
  entry, prerequisites, governance note, indicators or repo status.
- The "What this deliberately does not cover" note names four things as prose: auto mode,
  legacy-system onboarding, recurring security scans and Claude on call. Nothing checks it.
- `verify.py` runs 314 checks over `index.html` only. There is no second page.
- Source: [The AI-native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook),
  dated 2026-08-21, read in full for this spec.

### What the source actually provides per play

The intent asks for prerequisites, a governance note and indicators on every play. The source
does not give all of them for every play:

| Play | Prerequisites section | Governance section | Indicators |
| --- | --- | --- | --- |
| Claude Code on auto mode | none | none | none |
| Hooks as build-time guardrails | none | none | none |
| Claude on call with Claude Tag | none | audit sentence only | none |
| The other 13 plays | yes | yes | leading + lagging |

This spec therefore requires every field to be present, but lets a field hold the fixed marker
**"Not stated in the source"** where the source has no such section. Inventing prerequisites or
indicators to fill the grid would break the intent's faithfulness constraint.

## Requirements

### Page architecture

1. Add one new static page, `plays.html`. It is self-contained: inline CSS, no JavaScript, no
   external asset, font, script or runtime request. Its hard budget is **55,000 bytes**
   (estimate 42–48KB: 16 entries at about 1.4KB, glossary, terminology map, one figure and a
   reduced copy of the portal's CSS tokens). If the implementation cannot fit, work stops and the
   budget returns to the owner. It is not raised during implementation.
2. `index.html` keeps its **85,000-byte** cap unchanged. It gains only: one header-nav link to
   `plays.html`; one link per stage panel to that stage's section of `plays.html`; and the revised
   "does not cover" note (requirement 12). The note is rewritten shorter, which is how the new
   links fit in the remaining 445 bytes. If they still do not fit, work stops and returns to the
   owner.
3. `plays.html` reuses the portal's colour tokens, type scale, skip link, focus style and header
   pattern so the two pages read as one site. It links back to `index.html` and to each stage
   panel on it.
4. Mentor and Self-paced modes, the storage key and schema, the six questions and every existing
   Portal check stay unchanged. `plays.html` does not read or write storage.

### Closed play set

5. `plays.html` contains exactly these 16 play entries, in this order, each an `<article>` with
   `id`, `data-play` equal to the id, `data-stage`, and the source play name as its heading:

   | # | Stage | Source play name | `id` |
   | --- | --- | --- | --- |
   | 1 | plan | Capture as `intent.md` | `capture-intent` |
   | 2 | design | Requirements and design | `requirements-design` |
   | 3 | build | Claude Code plan mode as the default starting point | `plan-mode` |
   | 4 | build | Claude Code on auto mode | `auto-mode` |
   | 5 | build | The `CLAUDE.md` | `claude-md` |
   | 6 | build | Skills as institutional knowledge | `skills` |
   | 7 | build | Hooks as build-time guardrails | `build-hooks` |
   | 8 | build | Parallel sessions and subagents | `parallel-sessions` |
   | 9 | test | Give Claude a feedback loop | `feedback-loop` |
   | 10 | test | Continuous evals in CI | `continuous-evals` |
   | 11 | deploy | AI in the PR review loop | `pr-review` |
   | 12 | deploy | Hooks as approval gates | `approval-hooks` |
   | 13 | deploy | CI/CD integration and deployment | `cicd` |
   | 14 | maintain | Closing the loop | `closing-loop` |
   | 15 | maintain | Recurring codebase scans | `recurring-scans` |
   | 16 | maintain | Claude on call with Claude Tag | `claude-tag` |

   "Maintenance and closing the loop" is the Maintain stage introduction, not a play. The
   legacy-systems sidebar and the managed-settings worked example appear once each in a separate
   "Cross-cutting notes" section, with `data-crosscut="legacy-systems"` and
   `data-crosscut="managed-settings"`. They are not play entries.
6. Entries are grouped under six stage sections with ids `plan`, `design`, `build`, `test`,
   `deploy`, `maintain`. Each section ends with an attribution line linking the source.

### Fields in every entry

7. Every entry has, in this order, each marked with `data-field`:
   - `summary`: what changes, one or two sentences in the portal's own words;
   - `prerequisites`: links to other entries, or "None", or "Not stated in the source";
   - `governance`: one or two sentences, or "Not stated in the source";
   - `leading` and `lagging`: one sentence each, or "Not stated in the source";
   - `status`: exactly one of `implemented`, `partial`, `declared out of scope`, carried both as
     visible text and as `data-status`;
   - `evidence`: see requirement 9.
8. Colour is never the only status signal: the status word is always visible text, and it prints.

### Repository status

9. Status is judged only against files committed in this repository.
   - **implemented** needs one or more evidence paths in `data-evidence` (space-separated,
     repository-relative). The verifier fails if any path does not exist at the commit under test.
   - **partial** needs evidence paths for what exists and a `data-field="gap"` sentence naming what
     is missing.
   - **declared out of scope** needs a `data-field="reason"` sentence.
10. The statuses are fixed here so the owner signs off the claims, not just the format:

    | Play | Status | Evidence / gap / reason |
    | --- | --- | --- |
    | capture-intent | implemented | `intent/`, `.sdlc/active` |
    | requirements-design | partial | `intent/*/spec.md` chains exist. Gap: no brand, security or UX policy skills are committed here, so specs are not skill-constrained. |
    | plan-mode | implemented | `intent/*/plan.md`, `.github/workflows/sdlc-gate.yml`. The runtime plan mode itself is not observable from the repository; the page says so. |
    | auto-mode | declared out of scope | An agent-runtime permission setting, not a repository artifact. |
    | claude-md | declared out of scope | This repository commits no agent-context file. Adopting one is its own intent, not a status fix. |
    | skills | partial | The lifecycle skill lives in a separate linked repository. Gap: no skill is committed in this repository. |
    | build-hooks | implemented | `.kiro/hooks/privacy-scan.json`, `scripts/privacy_pretooluse_hook.py` |
    | parallel-sessions | declared out of scope | Session orchestration is a runtime practice; no subagent definition is committed. |
    | feedback-loop | implemented | `verify.py`, `.github/workflows/portal-verify.yml` |
    | continuous-evals | partial | `scripts/privacy_mutation_proof.py`, `.github/workflows/portal-verify.yml`. Gap: these test the portal and scanner, not the agent's configuration; there is no eval suite over agent tasks. |
    | pr-review | partial | `.github/pull_request_template.md`, `.github/workflows/sdlc-gate.yml`. Gap: no `REVIEW.md` and no AI review pass. |
    | approval-hooks | partial | `.githooks/pre-push`. Gap: no hook asks a named person to approve; human approval comes from branch protection, which is repository configuration, not a committed file. |
    | cicd | partial | `.github/workflows/`. Gap: CI is deterministic only; no agent step, MCP deployment or rehearsed rollback. |
    | closing-loop | declared out of scope | A static page has no production metric to band; no `bands.yaml` is committed. |
    | recurring-scans | declared out of scope | The privacy scan runs on changes, not on a schedule, and is not a model-driven scan. |
    | claude-tag | declared out of scope | No channel integration exists or is planned for this repository. |

    Totals: 4 implemented, 6 partial, 6 declared out of scope. Nothing is added to the repository
    to change a status in this PR.

### Out-of-scope statement

11. `plays.html` has a section `id="out-of-scope"` listing every declared-out-of-scope entry.
12. The `index.html` note keeps its heading "What this deliberately does not cover". It names
    each declared-out-of-scope play once, each wrapped as `<a data-oos="<id>"
    href="plays.html#<id>">`, and names the two cross-cutting notes with `data-crosscut`. The
    verifier fails unless the set of `data-oos` ids on `index.html` equals the set of
    `data-status="declared out of scope"` entries on `plays.html`, in both directions.

### Dependency graph

13. Edges come from each play's **Prerequisites** paragraph only. The source's own graph image is
    not machine-readable and is not used. Each edge is `required` or `helps`, following the
    source's wording ("helps", "also helps", "if one exists" read as `helps`):

    | Play | Required | Helps |
    | --- | --- | --- |
    | requirements-design | capture-intent, skills | — |
    | plan-mode | — | capture-intent, requirements-design, claude-md |
    | skills | — | claude-md |
    | parallel-sessions | claude-md | feedback-loop |
    | continuous-evals | claude-md, feedback-loop | — |
    | pr-review | claude-md | skills, parallel-sessions |
    | cicd | pr-review, approval-hooks | — |
    | closing-loop | capture-intent, pr-review, approval-hooks, cicd | — |
    | recurring-scans | pr-review, approval-hooks, capture-intent | — |

    Plays with "None": capture-intent, claude-md, feedback-loop, approval-hooks. Plays with no
    Prerequisites section: auto-mode, build-hooks, claude-tag. Two readings are interpretive and
    the page says so: pr-review's "defined subagents" maps to parallel-sessions, and
    closing-loop's "hooks as an action boundary" maps to approval-hooks.
14. The canonical form is an ordered text list, `id="dependency-list"`, one `<li data-edge="<from>
    <to> <kind>">` per edge. Each entry's prerequisite links equal its incoming edges.
15. One inline SVG figure draws the same edges, each edge a group with the same `data-edge` value.
    The verifier fails if the figure's edge set and the list's edge set differ. The figure is
    sized mobile-first, has `role="img"`, a `<title>`, a `<desc>`, a visible caption, and
    distinguishes `required` from `helps` by line style, not colour alone.

### Glossary and terminology map

16. A glossary `id="glossary"` defines each term once as `<dt id="term-<slug>">`. The verifier
    fails on a duplicate term. It covers at least: intent, spec, plan, play, gate, control band,
    hook, skill, subagent, worktree, eval, MCP, managed settings, merge base.
17. A terminology map `id="terminology"` has one row per Playbook term: `CLAUDE.md`,
    `.claude/skills/`, `.claude/settings.json` hooks, `.claude/agents/`, `REVIEW.md`,
    `bands.yaml`, `evals/`, managed settings. Each row names either a repository path, verified
    to exist, or the exact text "No counterpart".

### Paraphrase discipline

18. No source code sample, prompt or configuration block is reproduced. File and identifier names
    are allowed.
19. The verifier normalises visible text (lower case, collapse whitespace and punctuation) into
    eight-word windows and compares them with the source's windows. The committed fixture
    `evals/source-shingles.txt` holds only **SHA-256 hashes** of the source's eight-word windows,
    not the source text, so the repository does not redistribute the prose it is checking
    against. It records the source URL and date and the command that produced it. The rule is a
    ratchet:
    - **`plays.html`: zero matching windows.** The one exemption is the heading of each of the
      16 entries, whose text requirement 5 fixes as the source play name: before windowing, the
      verifier removes the text of an entry's first heading only when it equals that entry's
      name in the requirement 5 table exactly. Like file and identifier names under
      requirement 18, a play name is a name, not a reproduced sentence. Any other element,
      including a heading elsewhere that repeats a play name inside longer text, is checked in
      full. No hash exception list applies to `plays.html`.
    - **`index.html`, new text: zero matching windows.** Every matching window must appear in the
      committed baseline `evals/index-source-overlap-baseline.txt`; a match not in the baseline
      fails, so text this PR adds or rewrites cannot copy the source.
    - **`index.html`, existing text: baseline only moves down.** The baseline lists the hashes of
      the windows that already match in `index.html` at `514366c`, generated by the verifier's
      own normaliser (measurement during this spec found roughly 190–212 depending on the
      normaliser; the committed file is the figure, not either estimate). The verifier fails if
      the baseline lists a hash that no longer matches `index.html` (a stale entry must be
      removed, so the count cannot silently hold) and fails if the baseline grows beyond the
      count recorded in its own header at `514366c`.
    - **Visible, not hidden.** Every verifier run prints the baseline count and, for each
      baseline hit, the eight `index.html` words that match, so the overlap stays on the record.
      Rewriting the merged lesson text to clear the baseline is a separate intent, not this PR.

### Accessibility, layout and budgets

20. `plays.html` meets the same contracts as `index.html`: no horizontal page overflow at
    360/768/1024/1440px, 44px compact touch targets, a skip link as first focusable element,
    visible focus, one `h1`, no skipped heading levels, `prefers-reduced-motion` respected, a
    readable print layout, `lang="en"`, a viewport meta tag and no console messages.
21. Wide tables sit in a focusable, labelled scroll region rather than overflowing the page.

## Verification

22. `verify.py` gains a `plays` section, added red first: the commit adding it fails on the
    current tree with named `plays:` findings only, with no traceback and all 314 existing checks
    green.
23. After implementation: all Portal checks green, 31 privacy tests, 11/11 catalogue mutations, full-tree
    privacy scan with 0 findings, SDLC gate passing, `git diff --check` clean. The source-overlap
    check reports `plays.html` 0 hits, `index.html` 0 hits outside the baseline, and a baseline
    count no higher than the one recorded at `514366c`.
24. Mutation evidence for the new checks, at least: delete one entry; invent one entry; point one
    implemented evidence path at a missing file; drop one `data-oos` link; add one edge to the
    figure only; duplicate one glossary term; paste one eight-word source sentence into
    `plays.html`; paste one eight-word source sentence not in the baseline into `index.html`; add
    one extra hash to the baseline; leave one stale hash in the baseline after its text is
    removed; append an eight-word source sentence to one entry's heading, so the heading no
    longer equals its play name and loses the requirement 19 exemption. Each must go red.
25. Rendered evidence against an immutable commit URL: `plays.html` at 360/768/1440px screenshots;
    overflow at 360/768/1024/1440px; keyboard traversal from skip link through every entry;
    no-JavaScript render; print; console; and the `index.html` stage links landing on the right
    `plays.html` sections.

## Allowed files

`plays.html` (new), `index.html`, `verify.py`, `evals/source-shingles.txt` (new),
`evals/index-source-overlap-baseline.txt` (new), `README.md` (one
link to the catalogue only), and this chain's artifacts. Workflows, privacy rules and allowlist,
the SDLC gate, hooks and branch protection are not changed.

## Flagged concerns

- **Faithfulness vs completeness.** Three plays have no prerequisites, governance or indicator
  sections in the source. The spec shows "Not stated in the source" rather than inventing them,
  which narrows intent success criterion 2 for those three plays.
- **Interpretive edges.** Two prerequisite mappings (requirement 13) are readings of loose source
  wording and are labelled as such on the page.
- **CLAUDE.md marked out of scope.** It is the one out-of-scope play that is a plain repository
  artifact rather than a runtime or operations concern. The owner may prefer to open a separate
  intent to adopt it later; this PR does not.
- **Shingle fixture as hashes.** Intent decision 6 says "a committed file of source sentences".
  Hashes meet the same check without redistributing source text; the owner should confirm this
  reading.
- **Existing overlap in `index.html`.** The merged lesson text already shares eight-word windows
  with the source (roughly 190–212 by the two normalisers tried). A zero-hit rule on
  `index.html` would require rewriting merged lessons, which requirement 2 forbids and the
  85,000-byte cap cannot absorb. Requirement 19 therefore ratchets: new text must be clean,
  the existing overlap is listed on every run and may only shrink, and clearing it is left to a
  separate intent. The intent's paraphrase constraint is met in full for `plays.html` and for
  all new `index.html` text, not yet for the pre-existing lessons.
- **Play-name exemption.** "Claude Code plan mode as the default starting point" is nine words,
  so the verbatim heading requirement 5 demands shares an eight-word window with the source.
  Requirement 19 exempts exactly the 16 required headings rather than shortening the name
  (which would misname the play) or allowing a hit count (which would admit copied prose).
- **Budgets.** `plays.html` gets a new 55,000-byte cap. `index.html` stays at 85,000 and must
  absorb the new links by shortening the note. Overrunning either one stops work.
