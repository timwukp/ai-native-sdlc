# Plan: prove the privacy guardrails red, then make all three surfaces green

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Accepted-for:** d9906f86d0460a758490ed3bebddc28acf6365e7
- **Status:** draft

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time. It binds approval to the
protected `main` state after the PR 0 closeout, not to this branch's moving tip.

## Files changed (in order of work)

Files already changed to establish this chain are included so the complete pull-request diff is
accounted for.

1. `.sdlc/active` — point at `automatic-pii-scanning` instead of the shipped governance chain.
2. `intent/automatic-pii-scanning/intent.md` — accepted Stage 1 artifact linked to Issue #6.
3. `intent/automatic-pii-scanning/spec.md` — signed-off requirements, boundaries, and design.
4. `intent/automatic-pii-scanning/plan.md` — this merge-base-bound implementation plan.
5. `verify.py` — add privacy-governance checks first; require every scanner, config, hook, test,
   workflow and documentation surface, and reject the three current real-host literals.
6. `scripts/test_privacy_scan.py` — red-first unit/integration tests for rules, configuration,
   tracked-tree enumeration, redaction, binary handling, ordering, limits, and CLI exits.
7. `scripts/test_privacy_pretooluse_hook.py` — red-first event-contract tests for both event
   spellings, every new-content key, multi-operation payloads, old-value removal, relative paths,
   redacted blocks, and fail-open infrastructure paths.
8. `scripts/test_privacy_hook_config.py` — red-first structural and hermetic execution tests for the
   shipped Kiro hook JSON and its command wrapper.
9. `scripts/test_privacy_pre_push.py` — red-first temporary-Git-repository tests for new, existing,
   deleted and multi-commit pushes, including add-then-remove history and installer conflicts.
10. `scripts/privacy_mutation_proof.py` — mutation runner that disables each detection category and
    proves the tests kill every mutant without printing fixture values.
11. `.github/workflows/privacy-scan.yml` — committed with the red tests so a draft PR exposes the
    stable `privacy scan` context and proves it fails before implementation.
12. `.privacy-allowlist.json` — schema-1 narrow allowlist and configured marker data.
13. `scripts/privacy_scan.py` — shared deterministic scanner, CLI, tracked-tree reader and outgoing
    commit-tree reader.
14. `scripts/privacy_pretooluse_hook.py` — Kiro event adapter scanning only proposed new content.
15. `.kiro/hooks/privacy-scan.json` — repository-local official Kiro v1 PreToolUse configuration.
16. `.githooks/pre-push` — executable POSIX adapter passing Git ref-update input to the scanner.
17. `scripts/install_privacy_hooks.sh` — executable conflict-refusing repository-local installer.
18. `intent/review-follow-ups/intent.md` — replace its one real developer-home literal with a
    generic placeholder; preserve all artifact fields and meaning.
19. `intent/review-follow-ups/plan.md` — replace its two real developer-home literals with generic
    placeholders; preserve all artifact fields and meaning.
20. `README.md` — document scan command, categories, allowlist, Kiro surface, POSIX hook
    installation/verification, `--no-verify`, CI, redaction, and permanent limits.

Explicitly unchanged: `index.html`, `.github/workflows/portal-verify.yml`,
`.github/workflows/sdlc-gate.yml`, `.github/pull_request_template.md`, `.gitignore`, local
`.kiro/settings/`, and every shipped artifact field other than the three genericized prose
occurrences in files 18–19.

## Work order

### A. Accept the plan and build the red verification system

1. **Reconfirm gates and binding.** Verify committed intent accepted, spec signed-off, Build gate
   open, merge base equals `Accepted-for`, protected `main` still requires the existing two checks,
   and the only unrelated worktree content is local `.kiro/settings/`.
2. **Accept this plan.** The owner replaces `pending` and `draft`, commits the acceptance, and the
   Test gate must open before any file below is edited.
3. **Write `verify.py` privacy checks first.** Add a `privacy` group using existing checked-file,
   YAML-block, unfiltered-trigger, and read-only-permission helpers. Each absent surface is a named
   finding rather than a traceback. Assert:
   - files 6–17 exist;
   - the workflow has unfiltered `pull_request`, `push` limited to `main`, manual dispatch,
     `contents: read`, no secret, job id/name `privacy-scan` / `privacy scan`, full-history checkout,
     and fail-closed test, mutation, and tree-scan commands;
   - Kiro JSON has v1/PreToolUse/write/command/timeout/enabled shape;
   - allowlist has schema 1 and no broad path/category exclusion;
   - README carries every limitation and install statement;
   - no tracked file contains the real developer-home or host markers measured in the baseline.
4. **Write the four red test suites.** They invoke not-yet-present implementation through controlled
   subprocess/import helpers and report named test failures—not an uncaught import traceback. Build
   synthetic values from fragments at runtime so the full tracked-tree scanner will not flag its
   own test source.
5. **Write the privacy workflow as verification infrastructure.** It runs on unfiltered PRs, `main`
   push and manual dispatch; uses read-only permissions; checks out full history; runs the four test
   suites, mutation proof, then `privacy_scan.py --repo .`; and has stable display name
   `privacy scan`. Before implementation, missing scripts must fail the job.
6. **Observe local red.** Run the four test commands and `python3 verify.py`. Failures must name
   missing behavior/files only. Existing portal/governance checks remain green. Commit files 5–11
   as one red verification commit.
7. **Publish the red state as a Draft PR.** The owner pushes the named branch. Create a Draft PR
   linked to Issue #6. Record that `portal verify` and `privacy scan` are red while
   `sdlc-gate / sdlc-gate` passes process authorization. The protected PR must remain blocked. Do
   not merge or mark ready.

### B. Implement the shared scanner

8. **Create and validate allowlist schema.** Add `.privacy-allowlist.json` with schema 1, exact
   public values/anchored patterns and explicit marker lists. Reject unknown keys, bad types,
   duplicates, unsupported versions, unanchored regex and malformed regex before scanning.
9. **Implement the pure rule engine.** Add finding/category structures, line-preserving text scan,
   Luhn validation and narrow allowlist matching. Convert raw regex matches immediately into
   redacted metadata. Renderer functions receive no source text or matched value.
10. **Implement tracked-tree mode.** Resolve repo root with Git, enumerate `git ls-files -z`, reject
    external symlink resolution, classify NUL-bearing content as binary, fail on invalid non-binary
    UTF-8 or oversized text, and sort findings deterministically.
11. **Implement outgoing-commit mode.** Parse pre-push lines without logging them; derive commit sets
    for new/existing refs; scan every outgoing commit tree through Git object reads; skip deletion
    refs; deduplicate metadata-only findings; fail closed on malformed or unavailable objects.
12. **Run scanner tests until green.** Fix implementation, not test expectations, unless a test is
    proven to contradict the signed-off spec; any such correction requires an explained test commit.

### C. Implement and functionally verify both local hooks

13. **Implement the Kiro adapter.** Parse both event-name spellings and write-tool payloads; extract
    only new-content fields; retain target path; ignore old-content fields; call the shared engine in
    memory; exit 2 on finding and 0 on non-applicable/infrastructure paths. Never write payloads to
    disk.
14. **Add the Kiro config.** Mirror the official shipped v1 format and guarded POSIX command style.
    The command self-disables when Python or the checked-in adapter is absent and has a bounded
    timeout. Do not touch local `.kiro/settings/`.
15. **Implement pre-push adapter and installer.** The adapter passes stdin once, unchanged, to the
    scanner with the remote name. The installer checks prerequisites, refuses hook-path conflicts,
    sets repository-local—not global—`core.hooksPath`, reads it back, and runs a safe smoke scan.
16. **Exercise installed behavior.** Tests create temporary repositories under the process temp
    root, run the actual Kiro command from the checked-in JSON, run the actual installer, then invoke
    the installed pre-push hook. File presence, executable mode and config parsing alone do not pass.

### D. Prove coverage and integrate the repository

17. **Implement mutation proof.** Define one mutation per supported detection category and any
    load-bearing redaction/allowlist branch. Each mutant runs against the relevant test subset in an
    isolated copy; all must be killed. The final mutation count is derived from the manifest and
    printed, never copied into docs as a hand-maintained constant.
18. **Genericize the baseline.** Replace exactly three real host-prefix occurrences in files 18–19
    with `/home/<user>/` or machine-neutral wording. Inspect zero-context diff to prove no status,
    author, approval, binding, requirement or historical conclusion changed.
19. **Write README documentation.** State supported categories, commands, POSIX-only terminal hook,
    installer conflict behavior, Kiro hook fail-open versus CI fail-closed, `--no-verify` bypass,
    narrow allowlist review and permanent false-negative/false-positive limits. A clean result is
    never called proof, certification or compliance.
20. **Green locally.** Run all four suites, mutation proof, full tracked-tree scan, Portal verifier,
    SDLC CI gate, Python syntax checks, shell syntax checks and `git diff --check`. Measure scanner
    durations against the one/five-second budgets.
21. **Inspect the complete diff.** Prove `index.html` and the two existing required workflows are
    unchanged; all paths appear in this plan; local `.kiro/settings/` is untracked/unstaged; test
    source has no complete sensitive fixture; output captures contain no synthetic fixture value.
22. **Commit implementation.** Stage only named files. Preserve red and green commits separately.

### E. Turn the Draft PR green and make the CI check binding

23. **Owner pushes green commits.** The agent does not push. Re-read GitHub auth workflow scope
    before handing over the command.
24. **Observe all checks.** Require `portal verify`, `sdlc-gate / sdlc-gate`, and `privacy scan` to
    conclude `SUCCESS`. Read logs for failures; do not infer from local tests. Record exact context
    from the check-run API.
25. **Mark the PR ready.** Only after all checks are green. The owner performs human review and
    merge; the agent does not approve or merge its work.
26. **Add the privacy context to branch protection.** Show the complete payload and obtain immediate
    owner confirmation. Preserve strict mode, Owner enforcement, zero approvals, force-push/deletion
    denial and the two existing exact contexts; append only the observed privacy context.
27. **Read protection back.** Verify all three contexts and every existing setting. Never test by
    merging a failing PR or direct-pushing to protected `main`.
28. **Offer local terminal activation.** Show that committing hook files did not install them. With
    owner authorization, run the checked-in installer in this repository and read back local
    `core.hooksPath`; do not alter global Git config.
29. **Close the chain.** Open an artifact-only PR marking this intent/spec/plan shipped. Begin
    responsive PR 1 only after closeout merges.

## Tests that prove it

### Red targets

```sh
python3 scripts/test_privacy_scan.py
python3 scripts/test_privacy_pretooluse_hook.py
python3 scripts/test_privacy_hook_config.py
python3 scripts/test_privacy_pre_push.py
python3 verify.py
```

Before implementation: each command exits non-zero with named missing-behavior/file findings and no
uncaught import traceback. The Draft PR shows `privacy scan` and `portal verify` red and blocked.

### Green local suite

```sh
python3 -m unittest discover -s scripts -p 'test_privacy*.py'
python3 scripts/privacy_mutation_proof.py
python3 scripts/privacy_scan.py --repo .
python3 verify.py
python3 -m py_compile scripts/privacy_scan.py scripts/privacy_pretooluse_hook.py
sh -n .githooks/pre-push scripts/install_privacy_hooks.sh
git diff --check
```

Pass conditions:

- every unittest passes with no skipped integration surface;
- all declared mutants are killed, with no broken mutation;
- full tracked-tree scan exits 0, prints scanned/skipped/finding counts, and no source text;
- Portal verifier exits 0 with a non-zero increased check count;
- hook scripts parse, POSIX scripts pass syntax, and executable bits are recorded;
- `index.html`, portal workflow and SDLC workflow have no diff;
- only the three planned historical host literals change in shipped artifacts;
- complete diff paths equal the plan's list;
- local `.kiro/settings/` remains untracked and unstaged.

### Required rule cases

- Unix/macOS/Windows home path positive and generic-placeholder negative.
- Configured host/user marker positive.
- Ordinary, GitHub noreply and reserved-example email cases.
- Labeled phone positive and unlabeled-number negative.
- Luhn-valid positive and same-length invalid negative.
- PEM header, bearer, AWS, GitHub and Slack credential prefixes.
- URLs, commit SHA, workflow expression and ordinary `token` prose negative.
- Narrow exact/anchored allowlist positive; unknown/broad/malformed config negative.
- NUL binary explicit skip; invalid UTF-8 and oversized text fail closed.
- Tracked file positive; untracked, ignored, `.git` and external symlink negative.
- Hook event names, every new-content key, nested operations, old-value removal, no-content and bad
  JSON behavior.
- Existing branch, new branch, deletion ref, multiple outgoing commits and add-then-remove history.
- Installer success, pre-existing hook-path conflict and active legacy-hook conflict.
- Every output path asserts raw synthetic values absent.

### Real GitHub evidence

- Draft red run records `privacy scan` as a real context and the PR as blocked.
- Green revision records all three checks `SUCCESS`.
- Check-run API supplies the exact privacy context.
- Post-merge branch-protection API contains all three contexts with previous settings unchanged.

## Risks

- **Tests can leak the fixture they detect.** Build values from fragments; capture every output; make
  raw-value absence an assertion on success, finding, malformed input and exception paths.
- **Full-tree scanning can inspect local private metadata.** Use `git ls-files`, not filesystem walk;
  tests plant private-looking `.git` and untracked content and prove absence from findings.
- **A pre-push tree-only scan misses add-then-remove history.** Scan every outgoing commit tree.
- **New-branch range calculation can accidentally include all history or miss commits.** Derive
  commits excluding remote refs and test a temporary remote with known published/unpublished
  commits.
- **Symlinks can escape the repository.** Refuse external targets; never open them through a
  resolved path.
- **Allowlist regex can suppress too much.** Require full anchoring and forbid path/category skips.
- **Hook integration can break editing.** Infrastructure errors fail open locally; positive matches
  alone exit 2; CI fails closed.
- **Installer can displace an existing hook.** Refuse conflicts and leave config untouched.
- **POSIX-only can be mistaken for cross-platform.** Repeat the limit in code, tests, README and PR.
- **CI arrives after a public branch push.** Pre-push is the preventive layer; CI cannot unpublish a
  leaked remote commit and does not claim to.
- **Mutation output can reveal fixtures.** Capture mutant test output and print only mutant id and
  killed/survived/broken state.
- **Required-context mutation can lock all PRs.** Append only the exact observed context after owner
  confirmation and immediate read-back.
- **The Kiro hook may not reload in the current session.** Hermetic command execution proves its
  contract; actual session activation is not claimed until a subsequent session observes it.

## Rejected alternatives

Gitleaks in this change, recursive working-tree scan, match/hash output, scanning old replacement
text, tree-only pre-push, silent hook composition, real-host allowlist, Windows claims, filtered CI,
and any Portal UI change are rejected by the signed-off spec.

---
Gate: the owner accepts BEFORE `verify.py`, tests, workflow, scanner, hooks, baseline prose or README
is edited. Any implementation departure requires a plan amendment and renewed acceptance.
