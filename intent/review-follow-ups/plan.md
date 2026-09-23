# Plan: seven checks, two notes, five paths

- **Spec:** ./spec.md
- **Author:** Claude (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** b5c89603f1b05e2ed02015a8c25a0f73859952c6
- **Status:** shipped

`Accepted-for` is `git merge-base origin/main HEAD` at draft time: `b5c8960`.

## Files changed (in work order)

1. `verify.py` — seven new `REQUIRED_TEXT` entries (three for the dual-surface lab, four
   for the scope declaration). Committed and observed failing FIRST: 128 checks, 6 failed
   (`.kiro/hooks` already present, the other six needles absent).
2. `index.html` — lab step 1 gains the Claude Code lines inside the existing `<pre>` block
   plus the merge-don't-overwrite sentence; Honest limits gains one `note` div declaring
   the uncovered plays. No new external link, so the isolation checks hold.
3. `intent/portal-diagrams/plan.md` — two absolute workspace paths become repo-relative,
   one `cd` path becomes `~/`; a dated post-ship note above "Files changed" records the
   edit.
4. `intent/portal-diagrams/intent.md`, `intent/sdlc-training-portal/spec.md` — one
   `/home/<user>/` prefix each becomes `~/`.
5. `.sdlc/active` — points at this slug.
6. `intent/review-follow-ups/` — this chain.

## Sequencing constraint

The lab's new `cp` line references `templates/claude-code-hooks/settings.json`, which
exists on the skill repository's `claude-code-surface` branch (PR #68) and not yet on its
`main`. Merge PR #68 before or together with this one, or the lab teaches a copy that
fails.

## Verification

`python3 verify.py` — red at step 1 (6 failures), then 128 checks / 0 failed after step 2,
page weight 60,687 of 75,000 bytes. A tracked-tree grep for the machine-specific home
prefix returns
nothing after step 4.
