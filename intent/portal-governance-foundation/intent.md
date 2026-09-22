# Intent: make every portal revision pass through a governed pull request

- **Slug:** portal-governance-foundation
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-22
- **Status:** accepted
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/4

## Problem

The portal owner requires every optimization and revision to update the repository through a pull
request before GitHub Pages changes. The repository does not currently enforce that path: `main`
has no branch protection and there is no pull-request workflow running `verify.py` or the
AI-Native SDLC merge gate. A direct change can therefore publish without either check.

Two changes that have already merged, `review-follow-ups` and `readme-front-door`, also remain
marked `accepted` / `signed-off` / `accepted` rather than `shipped`. Those spent chains still read
as live authorization, which is the exact approval-reuse failure the portal teaches readers to
avoid.

## Desired outcome

Every future portal change is proposed through a pull request and receives two deterministic
signals before merge: the portal's own verification target and the AI-Native SDLC merge gate.
The exact check-run names observed from a real pull request become required checks on `main`.
Previously merged chains are closed as `shipped`, and every later product change starts with a new
intent rather than reusing an old approval.

This is a repository-level safety rail, not an unbypassable enterprise control. The owner of a
personal repository can still change or remove branch protection, and the repository must state
that limit honestly.

## Affected users / systems

- The owner, who authors and teaches from the portal.
- Contributors proposing portal changes.
- Mentees reading the GitHub Pages site; availability must not regress while governance is added.
- GitHub pull requests, Actions, branch protection, and Pages publication from `main`.
- The committed SDLC artifact chains and their active pointer.

## Constraints

- PR 0 changes governance and contribution plumbing only. Responsive layout, diagram sizing,
  mentor mode, self-paced learning, and playbook-content expansion remain separate PRs.
- No direct push to `main`; the agent does not push any branch, approve its own artifacts, merge a
  pull request, or change branch-protection settings without the owner's explicit action.
- Required-check workflows must run on every pull request. They must not use a `paths:` or
  `branches:` filter that can leave a required check permanently unreported.
- Keep one stable portal-verification check name rather than requiring matrix-cell names.
- The AI-Native SDLC reusable workflow must use an immutable revision proven to pass the
  `Accepted-for` merge-base value; a released or moving ref is not assumed safe from its name.
- `verify.py` remains standard-library-only. Adding governance must not add a build system,
  runtime dependency, external asset, analytics request, or network request to the portal.
- GitHub Pages continues to publish the root `index.html` from `main`.
- Exact required-check names must be read from the real PR check runs before branch protection is
  configured; guessed names can block every later PR.
- A post-merge artifact-only closeout PR is required because marking this chain `shipped` before
  its implementation merges would be false.

## Success criteria

1. Issue #4 is the public tracking record for the governance foundation.
2. The two already-merged chains, `review-follow-ups` and `readme-front-door`, are marked
   `shipped` before they can authorize another product change.
3. An unfiltered pull-request workflow runs `python3 verify.py` and reports one stable aggregate
   check whose conclusion is literally `success` only when verification passes.
4. An unfiltered AI-Native SDLC workflow runs with `require-active: true`, verifies the accepted
   plan against the pull request's merge base, and fails closed on a missing, mismatched, or
   unverifiable `Accepted-for` value.
5. A pull-request template asks for the issue/intent, verification output, and—when the portal's
   appearance changes—viewport evidence at 360px, 768px, and 1440px plus keyboard and
   no-JavaScript checks.
6. PR 0 produces successful real check runs; their exact names are recorded before any required
   status-check configuration is written.
7. After the owner configures branch protection, a read-only API query confirms that `main`
   requires pull requests and the exact observed checks. No destructive merge or direct-push
   experiment is used as proof.
8. The repository documents that personal-repository protection remains owner-bypassable and is
   not an organization-level policy plane.
9. The live portal remains available and its existing verification target remains green throughout
   the governance change.
10. After PR 0 merges, an artifact-only closeout PR marks this chain `shipped` before PR 1 begins.

## Resolved questions

1. **Owner enforcement:** branch protection applies to the repository owner
   (`enforce_admins: true`). This prevents accidental bypass during ordinary work while remaining
   honest that the owner can still edit or remove the rule itself.
2. **Review policy:** require pull requests and required checks now, with no approving-review count
   until an independent collaborator exists. GitHub self-approval is not treated as independent
   review.
3. **Required-check names:** explicitly deferred until PR 0 runs. The names will be copied from the
   check-run API rather than guessed from workflow or job ids.

---
Gate: product owner accepts. The accepting commit is the record.
