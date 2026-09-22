# Spec: PR-only governance with two required signals

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Requirements

1. **Close spent approvals.** Change the status of every artifact in the already-merged
   `review-follow-ups` and `readme-front-door` chains to `shipped`. Do not alter their authors,
   approvers, accepted base, requirements, plans, or historical wording.
2. **Portal verification on every pull request.** Add a GitHub Actions workflow with an unfiltered
   `pull_request` trigger and one stable job that checks out the repository, selects Python 3.12,
   and runs `python3 verify.py`. A non-zero verifier result must fail the job.
3. **Post-merge visibility.** The portal-verification workflow also runs on pushes to `main` and by
   `workflow_dispatch`, so the published branch has a recorded verification result. A branch
   filter is permitted on the `push` trigger only; the `pull_request` trigger remains unfiltered.
4. **AI-Native SDLC gate on every pull request.** Add an unfiltered caller workflow for
   `timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml` pinned to
   `582c818fbb6699ed8813df2d5a722a2c4da32f5c`, with `require-active: true`.
5. **Approval binding is real.** The pinned reusable workflow must be verified from its content to
   compute the caller PR's merge base and pass it to the gate as `--base-sha`. A tag name, release
   number, or green upstream badge is not evidence of this property.
6. **Least privilege.** Both workflows declare `contents: read` and require no repository secret,
   write token, model credential, deployment credential, or `pull_request_target` event.
7. **Stable required-check identities.** The portal-verification job has one explicit stable name.
   The SDLC caller job id remains stable. Exact branch-protection contexts are copied from the real
   check-run API after PR 0 runs; expected names in documentation are not treated as authoritative.
8. **Pull-request evidence template.** Add a repository pull-request template requiring:
   - the tracking issue and active intent slug;
   - the verification command and actual result;
   - confirmation that the eventual diff matches the accepted plan;
   - for visual changes only, evidence at 360px, 768px, and 1440px plus keyboard-only and
     JavaScript-disabled checks;
   - an honest statement for any check that could not be run.
9. **Document the contribution boundary.** Add a concise README section stating that portal changes
   go through pull requests, naming the local verification command, explaining that required checks
   become binding only through branch protection, and stating that a personal-repository owner can
   still edit or remove that protection.
10. **Configure `main` after observing checks.** After PR 0 is merged, the owner configures branch
    protection to require pull requests, require the exact observed check contexts, require branches
    to be up to date, apply checks to the owner (`enforce_admins: true`), disallow force pushes and
    deletion, and require zero approving reviews until an independent collaborator exists.
11. **Verify configuration read-only.** Read branch protection back through the GitHub API and
    compare every intended property. Do not test enforcement by attempting a direct push or by
    merging a deliberately failing pull request.
12. **Close PR 0 after merge.** A separate artifact-only closeout pull request changes this chain's
    three statuses to `shipped`. PR 1 does not begin before that closeout merges.

## Non-functional requirements

- **No portal regression.** `index.html` is unchanged in PR 0, the public page remains available,
  and `python3 verify.py` continues to report all checks passing.
- **No new runtime dependency.** The portal remains one static file with no external assets,
  analytics, build step, package manager, or network request. Workflow-only GitHub Actions do not
  become browser runtime dependencies.
- **No silent skip.** Neither required pull-request workflow may use `paths:`, `paths-ignore:`, or a
  pull-request `branches:` condition. A required check that never starts is a permanent block, not
  a useful failure.
- **Fail closed at merge time.** Portal verification and the SDLC gate are not advisory jobs and do
  not use `continue-on-error`. Their required check reports success only after the command succeeds.
- **Immutable policy dependency.** The SDLC reusable workflow is pinned to the full verified commit
  SHA, not `main` or a moving tag.
- **Availability during bootstrap.** Branch protection is configured only after a real successful
  run establishes the contexts, preventing a guessed context from blocking every future pull
  request.
- **Honest control claim.** Applying checks to the owner prevents ordinary accidental bypass; it
  does not make a personal repository equivalent to an organization-owned policy plane.
- **Local environment isolation.** Untracked `.kiro/settings/` content belongs to the local agent
  environment and is not included in the pull request. PR 0 does not add or install a local
  PreToolUse hook.

## Design

### 1. Portal verification workflow

Create `.github/workflows/portal-verify.yml` with three triggers:

- unfiltered `pull_request`;
- `push` limited to `main`;
- `workflow_dispatch`.

The workflow has `permissions: contents: read` and a single non-matrix job whose stable display
name is `portal verify`. The steps are checkout, Python 3.12 setup, and `python3 verify.py`. There is
no aggregation job because there is only one command and therefore no dependency whose skipped
state could be mistaken for green.

### 2. SDLC caller workflow

Create `.github/workflows/sdlc-gate.yml` with unfiltered `pull_request` and
`workflow_dispatch`, `permissions: contents: read`, and one caller job named `sdlc-gate`. It calls
the reusable workflow at the full SHA in requirement 4 and passes `require-active: true`.

The verified reusable workflow checks out both repositories, computes
`git merge-base origin/${{ github.base_ref }} HEAD`, passes it as `--base-sha`, and runs any
`evals/check_*.py`. The portal has no eval files today, so that loop reports there is nothing to run
without turning the absence into a false claim that eval quality was checked.

### 3. Pull-request template

Create `.github/pull_request_template.md` as an evidence checklist, not an approval form. It asks
for actual commands and results and never lets a checked box claim independent review. Visual
evidence is conditional so governance-only and documentation-only changes do not fabricate
screenshots.

### 4. README contribution section

Add a short `Contributing changes` section after local verification and before publishing. It
describes the PR path and the difference between a workflow check and a required gate. It links to
Issue #4 for the bootstrap record and does not describe the repository as unbypassable.

### 5. Existing-chain closeout

Only the six status values in the two merged chains change to `shipped`. Their plans remain bound to
the original merge bases. `.sdlc/active` already points at `portal-governance-foundation`, so no
spent chain remains active.

### 6. Branch-protection bootstrap

PR 0 necessarily runs before its checks can be required. The owner reviews and merges this one
bootstrap PR under the existing repository settings. After merge:

1. read the merge commit's check runs and record their exact names;
2. configure `main` with strict required status checks and the owner decisions from the intent;
3. read the resulting protection object back and compare it with requirement 10;
4. open the artifact-only closeout PR.

This one-time bootstrap gap is recorded rather than described as enforcement that already exists.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| A guessed check context can block every PR forever | Repository owner | Copy exact names from PR 0's check-run API before configuring protection. |
| A required workflow filter can leave a PR waiting for a check that can never run | Skill maintainer | Both required `pull_request` triggers are unfiltered; tests inspect the YAML shape. |
| PR 0 cannot be protected by a rule that does not exist yet | Repository owner | Treat PR 0 as an explicit bootstrap exception; configure and verify protection immediately after merge. |
| Owner enforcement could be described as unbypassable | Repository owner | State that `enforce_admins: true` prevents ordinary bypass but the personal-repository owner can still edit the rule. |
| Requiring one approval would deadlock a solo repository | Repository owner | Require zero approvals until an independent collaborator exists; checks and PRs remain required. |
| A released SDLC tag may not carry merge-base binding | Skill maintainer | Use and inspect immutable commit `582c818…`, which contains `--base-sha`; do not infer capability from a tag. |
| An advisory AI review could introduce secrets and prompt-injection risk | Repository owner | Do not add the optional model-based review job in PR 0; both checks are deterministic and secret-free. |
| Local Kiro settings could leak into the repository | Repository owner | Stage explicit files only; leave `.kiro/settings/` untracked and outside the plan. |

## Rejected alternatives

- **Rely on contributor discipline without branch protection — rejected.** It does not satisfy the
  owner's requirement that every revision go through a pull request.
- **Require guessed workflow/job names before PR 0 runs — rejected.** A wrong required context can
  never report and blocks all pull requests.
- **Add `paths:` to save one cheap verification run — rejected.** The resulting absent required
  status is a permanent merge block.
- **Vendor `sdlc_ci_gate.py` — rejected.** The reusable workflow fixes per-repository policy drift
  and the selected immutable revision has verified merge-base binding.
- **Pin the reusable workflow to `main` or a released tag — rejected.** `main` moves, and published
  evidence shows the existing tags omit the binding input required by gate v2.
- **Require one approving review immediately — rejected.** There is no independent collaborator;
  self-approval is not separation of duties.
- **Install the local PreToolUse hook in this PR — rejected as scope expansion.** PR 0 establishes
  PR and merge governance. A write-time hook is a separate, bypassable control and requires its own
  accepted intent.
- **Combine responsive UI or teaching-mode work with governance — rejected.** Those are PR 1 and
  later, with their own artifacts, red verification, and visual evidence.

## Out of scope

- Responsive CSS, diagram sizing, mentor mode, self-paced learning, expanded playbook content, or
  any other change to `index.html`.
- Installing Kiro or Claude Code local hook configuration.
- Model-driven PR review, API keys, analytics, telemetry, or deployment automation.
- Adding an independent reviewer who does not currently exist.
- Organization- or enterprise-level rulesets, external audit custody, or independent assurance.
- PR 1 through PR 4 implementation.

---
Gate: owner signs off; flagged concerns worked first. Applied org skill: `ai-native-sdlc`, published
from `timwukp/agent-skills-best-practice` main and used here with the reusable gate contract at
`582c818fbb6699ed8813df2d5a722a2c4da32f5c`.
