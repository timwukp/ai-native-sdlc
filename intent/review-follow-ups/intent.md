# Intent: close what the external review found

- **Slug:** review-follow-ups
- **Author:** Claude (AI agent)
- **Date:** 2026-09-16
- **Accepted-by:** Tim WU
- **Status:** shipped

## Problem

An external review of the skill and this portal (2026-09-10, re-run 2026-09-16) surfaced
three findings against this repository:

1. **The lab teaches one runtime.** The hands-on lab installs the write-time hook into
   `.kiro/hooks/` only. The skill now ships a Claude Code config for the same hook
   (`templates/claude-code-hooks/settings.json`, PR #68 on the skill repository), so
   training material that shows only the Kiro path bakes yesterday's gap into the lesson.
2. **The uncovered plays are implied, not declared.** The playbook contains plays with no
   counterpart here or in the skill — auto mode, legacy-system onboarding, recurring
   security scans, Claude on call — and the page never says so. On a page whose whole
   honest-limits section exists to prevent overclaiming, silence reads as coverage.
3. **Committed artifacts leak the build environment.** Five absolute
   `/home/ec2-user/...` workspace paths sit in the shipped intent chains of a public
   repository. Harmless to the reader, but it is environment detail the artifacts never
   needed to carry.

## Desired outcome

The lab shows both hook surfaces with the merge-don't-overwrite caveat; the honest-limits
section declares the uncovered plays as decisions on record; the artifact chains carry
repo-relative or `~` paths with the edit itself noted in the amended file. `verify.py`
gains content checks for 1 and 2 **before** the page changes, so the requirements are
enforced rather than remembered.

## Acceptance

Accepted on the owner's explicit authorization of the review recommendations
(review session, 2026-09-15). Merging the pull request is the recorded confirmation.
