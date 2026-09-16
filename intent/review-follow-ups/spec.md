# Spec: dual-surface lab, declared scope, de-environmented artifacts

- **Intent:** ./intent.md
- **Author:** Claude (AI agent)
- **Signed-off-by:** Tim WU
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Requirements

1. **The lab installs the hook on both runtimes.** Lab step 1 shows the Kiro copy AND the
   Claude Code copy (`templates/claude-code-hooks/settings.json` → `.claude/settings.json`),
   states the two configs carry an identical command for one script, and carries the
   caveat: an existing `.claude/settings.json` gets the `hooks.PreToolUse` entry merged in,
   not copied over. Enforced by `verify.py` content checks on the extracted text:
   `.claude/settings.json`, `claude-code-hooks`, `.kiro/hooks`.

2. **Uncovered plays are declared in Honest limits.** A note names auto mode / staged
   autonomy, legacy-system onboarding, recurring security scans, and Claude on call as
   deliberately not covered, each with the reason in one clause; managed settings is
   stated as the enterprise-supplied tier. Enforced by `verify.py` content checks:
   `auto mode`, `recurring security scans`, `Claude on call`, `legacy-system onboarding`.
   The note must not trip the forbidden-phrase list.

3. **No `/home/<user>` path in any committed artifact.** The five occurrences in
   `intent/portal-diagrams/{intent,plan}.md` and `intent/sdlc-training-portal/spec.md`
   become repo-relative or `~/` paths, and the amended plan carries a dated post-ship note
   saying what changed and why. No other wording in those artifacts changes.

4. **Red first.** The `verify.py` checks for requirements 1–2 are committed and observed
   failing before `index.html` changes; the isolation checks (no new external links) and
   the page-weight budget must still pass afterwards.

## Out of scope

- README changes. The review's suggestion to soften "recorded in the commit that changes
  them" was withdrawn: the commit bodies do carry the manual-check records (measured
  contrast 6.79:1 lowest, keyboard traversal), so the claim is true as written.
- Any change to the skill repository (that is PR #68 there, a separate chain).
