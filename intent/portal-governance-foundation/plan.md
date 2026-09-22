# Plan: bootstrap PR-only governance without claiming it already binds

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 2544ab776ccc1b1b6ba00b447783fc1f31e0de1f
- **Status:** accepted

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time. It records the fork point
whose repository state this plan was reviewed against, not the branch tip containing the artifact
commits.

## Files changed (in order of work)

Files already changed while establishing the accepted artifact chain are listed so the plan
accounts for the complete eventual pull-request diff.

1. `.sdlc/active` — point at `portal-governance-foundation` instead of the merged
   `readme-front-door` chain.
2. `intent/portal-governance-foundation/intent.md` — accepted Stage 1 artifact linked to Issue #4.
3. `intent/portal-governance-foundation/spec.md` — signed-off Stage 2 requirements and design.
4. `intent/portal-governance-foundation/plan.md` — this implementation plan and its acceptance
   binding.
5. `verify.py` — add deterministic governance checks FIRST and observe them fail before the files
   they require exist.
6. `intent/review-follow-ups/intent.md` — change only `Status: accepted` to `Status: shipped`.
7. `intent/review-follow-ups/spec.md` — change only `Status: signed-off` to `Status: shipped`.
8. `intent/review-follow-ups/plan.md` — change only `Status: accepted` to `Status: shipped`.
9. `intent/readme-front-door/intent.md` — change only `Status: accepted` to `Status: shipped`.
10. `intent/readme-front-door/spec.md` — change only `Status: signed-off` to `Status: shipped`.
11. `intent/readme-front-door/plan.md` — change only `Status: accepted` to `Status: shipped`.
12. `.github/workflows/portal-verify.yml` — unfiltered pull-request verification, `main` push
    verification, manual dispatch, read-only permissions, and one stable `portal verify` job.
13. `.github/workflows/sdlc-gate.yml` — unfiltered immutable-pinned reusable gate caller with
    `require-active: true`.
14. `.github/pull_request_template.md` — evidence checklist for intent, plan compliance,
    verification, and conditional viewport/accessibility proof.
15. `README.md` — add the contribution path, required-check distinction, verification command,
    bootstrap issue, and personal-repository owner-bypass limit; update the stale statement that
    the repository has no workflow.

Explicitly unchanged: `index.html`, `.gitignore`, local `.kiro/settings/`, and every prior artifact
field other than the six status values named above.

## Work order

1. **Reconfirm the accepted design.** Check that `intent.md` is accepted and `spec.md` is signed
   off in committed history, the Build gate is open, the merge base still equals the recorded
   `Accepted-for`, and the only unrelated working-tree item is local `.kiro/settings/`.
2. **Accept and commit this plan.** The owner replaces `pending` with their identity and changes
   the status to `accepted`. Run the Test gate; it must open before `verify.py` is edited.
3. **Write the red verification target.** Extend `verify.py` with a `governance` group that checks:
   - all three expected `.github` files exist;
   - both workflow files use unfiltered `pull_request` triggers;
   - neither workflow contains `pull_request_target`, a pull-request path filter, or a
     pull-request branch filter;
   - both workflows grant only `contents: read` at workflow level;
   - the portal job has the stable name `portal verify` and runs `python3 verify.py` without
     `continue-on-error`;
   - the SDLC caller uses the full `582c818…` SHA and `require-active: true`;
   - the PR template asks for issue/intent, actual verification evidence, plan compliance, and
     conditional 360/768/1440px plus keyboard/no-JavaScript evidence;
   - the README states the PR path, required-check distinction, local command, and owner-bypass
     limit;
   - the six prior artifact statuses are `shipped`.
4. **Prove red for the intended reasons.** Run `python3 verify.py`. It must exit non-zero with named
   governance findings for missing `.github` files, absent README content, and live old chains—not
   a traceback and not a failure in an existing portal check. Commit this red target separately.
5. **Close the two spent chains.** Change only the six status values listed in files 6–11. Inspect
   a zero-context diff to prove no author, approver, binding, or historical prose changed.
6. **Create portal verification workflow.** Add unfiltered `pull_request`, `push` limited to
   `main`, and `workflow_dispatch`; set `contents: read`; add checkout, Python 3.12, and the one
   `python3 verify.py` command in the stable `portal verify` job.
7. **Create SDLC caller.** Add unfiltered `pull_request` and `workflow_dispatch`, `contents: read`,
   the immutable reusable-workflow reference from the spec, and `require-active: true`. Do not add
   the optional model review job or any secret.
8. **Create the pull-request template.** Make visual evidence conditional so governance/docs-only
   pull requests do not claim screenshots they did not need. Ask for unavailable checks to be
   stated honestly rather than silently checked.
9. **Update the README.** Add `Contributing changes` after local verification and before publishing.
   Replace the now-false “no workflow” statement while preserving “no build step” and direct Pages
   publication from root `main`.
10. **Green the target.** Run `python3 verify.py` until all old and new checks pass. Do not weaken a
    check merely to match the implementation; correct the implementation when the requirement is
    right.
11. **Inspect the complete diff.** Run `git diff --check`; prove `index.html` has no diff; prove the
    two old chains have status-only diffs; confirm local `.kiro/settings/` is not staged; confirm
    the branch contains only files named in this plan.
12. **Commit the implementation.** Stage only the explicit files. Keep the red-verifier commit and
    implementation commit distinct so history shows the check existed and failed first.
13. **Verify authentication preconditions without pushing.** Confirm the user's GitHub credential
    can update workflow files; a token lacking the `workflow` scope is rejected server-side even
    when ordinary repository writes work. Do not treat `git push --dry-run` as proof of that scope.
14. **Owner pushes the named feature branch.** The agent does not run `git push`. After the remote
    branch exists, create the pull request referencing Issue #4 and include actual verifier output.
15. **Observe the real GitHub checks.** Wait for both workflows. If either fails, read the job log,
    fix only within this accepted plan, have the owner push the named branch again, and repeat.
    Record the exact check-run names from the check-run API; tool output or guessed job ids do not
    count.
16. **Human review and merge.** The owner reviews and merges PR 0. There is intentionally no
    self-approval claim and no required independent approval count during bootstrap.
17. **Configure branch protection.** After the checks exist on the default branch, apply the signed
    off policy: require pull requests, exact observed checks, strict up-to-date branches,
    `enforce_admins: true`, zero required approvals, no force pushes, and no branch deletion. This
    is a high-impact repository setting; show the final payload and obtain immediate owner
    confirmation before applying it.
18. **Verify protection and publication.** Read branch protection back via API, compare every
    property, and fetch the live portal to confirm it still matches committed `index.html`. Do not
    test by attempting a forbidden push or merging a failing pull request.
19. **Close the chain.** Create a separate artifact-only closeout branch and pull request that marks
    `portal-governance-foundation` intent/spec/plan as `shipped`. Do not begin responsive PR 1 until
    that closeout merges.

## Tests that prove it

### Red-first local target

```sh
python3 verify.py
```

Before files 6–15 are implemented: exit non-zero with governance findings while all existing portal
structure, isolation, content, honesty, and figure checks remain green. The exact new count is
recorded from the run rather than predicted.

### Green local target

```sh
python3 verify.py
git diff --check
git diff origin/main...HEAD -- index.html
```

Pass conditions:

- `verify.py` exits 0, prints a non-zero total, and every governance finding is green;
- `git diff --check` reports no whitespace error;
- `index.html` diff is empty;
- the old-chain diff contains exactly six status substitutions;
- no unplanned path appears in `git diff --name-only origin/main...HEAD`;
- `.kiro/settings/` is untracked and unstaged.

### Workflow-shape assertions inside `verify.py`

The governance group reports each property independently so one missing file cannot collapse the
rest into a traceback. It distinguishes the unfiltered `pull_request` block from the permitted
`push: branches: [main]` block; a broad search for the word `branches` would reject the correct
workflow and therefore is not an acceptable check.

### Real GitHub evidence

- PR 0 has successful portal and SDLC check runs.
- The check-run API supplies the exact required contexts.
- The SDLC job log records gate commit `582c818fbb6699ed8813df2d5a722a2c4da32f5c`
  and validates the plan against base `2544ab776ccc1b1b6ba00b447783fc1f31e0de1f`.
- After merge, the branch-protection API reports strict required checks, required pull requests,
  owner enforcement, zero approvals, force-push disabled, and deletion disabled.
- The public portal returns successfully and its bytes equal committed `index.html`.

## Risks

- **The verifier could confuse push and PR filters.** Parse the indentation-bounded
  `pull_request` trigger rather than banning `branches` globally; `push` is deliberately limited
  to `main`.
- **The static YAML check could pass malformed YAML.** Local stdlib checks establish required
  semantics but are not a YAML parser. GitHub accepting and running both workflows is the final
  syntax/integration evidence.
- **The required context could be guessed wrong.** Do not configure protection until the check-run
  API returns real names from PR 0.
- **PR 0 is a bootstrap exception.** It cannot be governed by checks or protection that do not yet
  exist. Record that limitation and close it immediately after merge rather than claiming this PR
  was already protected.
- **The reusable workflow is immutable but calls version-tagged GitHub Actions internally.** This
  PR pins the policy repository revision; it does not claim end-to-end supply-chain immutability.
- **Workflow-file push permissions can fail late.** Verify the credential's `workflow` scope before
  asking the owner to push; ordinary repo access and a dry-run are insufficient.
- **Branch protection can lock a solo owner out if configured incorrectly.** Use zero approving
  reviews, exact observed contexts, and read the settings back immediately. The owner explicitly
  chose `enforce_admins: true`.
- **Closing prior chains could rewrite history accidentally.** Restrict those six files to one-line
  status changes and inspect the diff before commit.
- **Local `.kiro/settings/` could be staged accidentally.** Stage named files only; never use
  `git add .`.
- **A personal-repository owner remains ultimate authority.** The owner can remove protection. The
  README must not call this control unbypassable or enterprise-owned.

## Rejected alternatives

- Installing a local PreToolUse hook, adding model review, modifying the portal UI, requiring an
  independent approval, guessing check names, filtering required workflows, vendoring the CI gate,
  or combining PR 1 work into this branch. Each is rejected in the signed-off spec.

---
Gate: the owner accepts BEFORE `verify.py`, workflow, template, README, or old-chain statuses are
edited. If implementation departs from this plan, update it and obtain renewed acceptance.
