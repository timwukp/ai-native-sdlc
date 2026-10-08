# Plan: check commit identity metadata in the shared privacy scanner

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Accepted-for:** f6eef816cf89fe237af3ab59c3508ad3f0551f85
- **Status:** draft

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time, the value the CI gate
compares. It binds review to protected `main` after the playbook-play-coverage closeout.

## Files changed (in order of work)

1. `.sdlc/active`: already points at `commit-metadata-scan`.
2. `intent/commit-metadata-scan/intent.md`, `spec.md`, `plan.md`: this chain (Issue #12).
3. `scripts/test_privacy_scan.py`: red-first metadata unit tests (spec 12, 13).
4. `scripts/test_privacy_pre_push.py`: red-first real-hook test with a local bare remote (spec 14).
5. `scripts/privacy_mutation_proof.py`: three anchored metadata mutations (spec 15).
6. `verify.py`: red-first workflow and README checks in `privacy_checks()` (spec 16).
7. `scripts/privacy_scan.py`: identity reading, rules, output, `--pre-push` extension and
   `--commit-range` (spec 1-10).
8. `.privacy-allowlist.json`: one exact web-flow value (spec 6).
9. `.github/workflows/privacy-scan.yml`: one pull-request-only step (spec 11).
10. `README.md`: the two surfaces, per-layer coverage, uncovered surfaces, allowlist reason
    (spec 17).

Explicitly unchanged: `index.html`, `plays.html`, `.githooks/pre-push`,
`scripts/install_privacy_hooks.sh`, the Kiro write-time hook and its config, the SDLC gate,
branch protection and every shipped chain. No new script and no second allowlist.

## Work order

### A. Accept the plan and commit the red contract

1. Record acceptance in this file in its own commit. Nothing below is edited before it.
2. Add metadata unit tests to `scripts/test_privacy_scan.py`. They build throwaway repositories
   under the test's temporary directory, run every Git call with `GIT_CONFIG_GLOBAL` and
   `GIT_CONFIG_SYSTEM` pointed at an empty file so the host's identity and hooks cannot leak in,
   and set each commit's identity through `GIT_AUTHOR_*` / `GIT_COMMITTER_*`. Every synthetic
   address is assembled at runtime with `chr(64)`, following `private_email()`. Cases are the
   spec 13 list exactly.
3. Add the real-hook test to `scripts/test_privacy_pre_push.py`: a scratch repository with
   `core.hooksPath` set to a copy of `.githooks`, a local bare remote, one push with a bad committer
   email (refused, remote ref absent afterwards) and one with noreply identities (accepted).
4. Add three mutations to `scripts/privacy_mutation_proof.py`, each an exact-once anchored
   replacement in the scanner source, run against `scripts/test_privacy_scan.py`, which holds
   every metadata unit test:
   - identity checking disabled: the metadata check returns an empty tuple;
   - last commit only: the identity loop iterates over `commits[-1:]`;
   - value leak: the field label passed into the metadata finding has the value appended.

   An anchor that does not match exactly once reports `broken`, as the 10 category mutations do.
5. Add to `verify.py` `privacy_checks()`: the workflow runs `--commit-range`, the step is gated on
   `github.event_name == 'pull_request'`, both SHAs arrive through `env:`, no `${{` appears on that
   step's `run:` line, and the README names both surfaces and the uncovered list.
6. Run and record the red state, then commit: the existing 31 privacy tests still pass and only the
   new tests fail; the mutation proof reports the three new mutations `broken`; `verify.py` fails
   only the new named checks with no traceback, and the other 373 stay green.

### B. Implement the scanner

7. In `scripts/privacy_scan.py`, add a `MetadataFinding` (commit, field, category, remediation)
   and render it in the spec 7 format, keeping `Finding` and its rendering unchanged. Add the
   `commit_email` remediation.
8. Add `_commit_identity(repo, sha)`: `git cat-file commit`, header before the first blank line,
   strict UTF-8, exactly one `author ` and one `committer ` line parsed with one anchored regex.
   Any deviation raises `ScanError` naming the 12-character id only.
9. Add `scan_commit_identities(repo, commits, config)`: email fields through `_allowed()`, name
   fields through `scan_text`, deduplicated per (commit, field, category), returning findings and
   the count of commits checked.
10. `scan_pre_push` calls it on the same deduplicated commit list it already scans for trees.
11. Add `--commit-range BASE HEAD` (`nargs=2`), validating 40-hex ids, mutually exclusive with
    `--pre-push`, resolving `git merge-base` then `git rev-list --reverse <base>..HEAD`.
12. Print `privacy scan: <N> commit identities checked` after the existing summary only when
    identities were checked.
13. Add the web-flow address to `allowed_exact`. The new tests turn green and the 31 old ones stay
    green.

### C. Workflow and documentation

14. Add the spec 11 step after the tree scan:
    `if: github.event_name == 'pull_request'`, `env: BASE_SHA`, `HEAD_SHA`, and
    `run: python3 scripts/privacy_scan.py --repo . --commit-range "$BASE_SHA" "$HEAD_SHA"`.
15. Update the README privacy section per spec 17.

### D. Prove it locally and commit

16. Portal verifier all green; privacy tests all passing; mutation proof 13 killed, 0 survived,
    0 broken; tracked-tree scan 0 findings.
17. `--commit-range $(git merge-base origin/main HEAD) HEAD` reports 0 findings and the number of
    commits on the branch; the read-only `main` history check still reports 0 non-allowlisted
    identities; the pre-push hook over every unpushed commit reports 0 findings.
18. `git diff --check`, no host paths, and every changed file is on the spec's allowed list.

### E. Follow-up issue, Draft PR, CI

19. Open the follow-up issue for the uncovered surfaces (commit messages and trailers, tag tagger
    identity, merge commits created on `main`).
20. The owner pushes; I open a Draft PR for Issue #12 linking the follow-up issue, and wait for
    `portal verify`, `privacy scan` and `sdlc-gate`. The `privacy scan` log must show the new
    step ran and checked the branch's commits.
21. No portal page changes, so no rendered evidence. With all three checks green on the current
    head, the PR is marked Ready. The owner merges; a separate artifact-only PR marks the chain
    `shipped`.

## Tests that prove it

| Spec | Proof |
| --- | --- |
| 1-3 | Malformed object and unknown id exit 2; only the four fields are read |
| 4 | Non-allowlisted author, committer and internal-host-shaped emails are findings |
| 5 | Developer-home path in a name is a `developer_home` finding |
| 6 | Noreply and web-flow identities are allowed |
| 7 | Bad first commit of three is reported once per field |
| 8 | Output contains no value, local part or domain; value-leak mutation killed |
| 9 | Real hook refuses the bad push; last-commit-only mutation killed |
| 10, 11 | `--commit-range` scope and argument tests; `verify.py` workflow checks; CI log |
| 15 | Mutation proof 13/13 |
| 16, 17 | `verify.py` README checks |

## Risks

- **Host Git configuration leaking into tests.** Mitigated by step 2's empty global and system
  config; without it a developer's own identity or hooks could make a test pass or fail by accident.
- **`git hash-object --literally`** is needed to write a malformed commit. It exists in the local
  Git (2.50.1) and in the CI runner's Git; if a runner lacked it the test would fail red, not pass.
- **Mutation proof scope.** The proof runs only `scripts/test_privacy_scan.py`, so the hook
  integration test is not mutation-checked; the last-commit-only mutation is killed by the unit
  test of the same behaviour.
- **Event base SHA.** If the base object were missing, the CI step exits 2 and the check goes red.

## Rejected alternatives

- **Parsing `git log --format=%ae` output.** Formatting options and `.mailmap` sit between the
  object and the check; the raw object is what is published.
- **A separate identity script or allowlist.** Breaks the one-scanner, one-allowlist constraint.
- **Scanning all of `main` in CI on every run.** Existing history is clean and not rewritten;
  rescanning it adds time without protecting anything new.

---
Gate: the owner accepts BEFORE tests, `verify.py`, the scanner, the allowlist, the workflow or the
README is edited. Any departure requires a plan amendment and renewed acceptance.
