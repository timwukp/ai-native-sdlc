# Spec: one redacting scanner behind three enforcement surfaces

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Baseline evidence

A tracked-file scan at design time found:

- three developer-home markers, all historical prose in the shipped `review-follow-ups` intent and
  plan that names a machine-specific home prefix (represented here as `/home/<user>/`) while
  describing its removal;
- zero email addresses;
- zero private-key, bearer-token, provider-token, password-assignment, secret-assignment, or
  token-assignment markers;
- zero labeled phone-number or long payment-card-shaped sequences.

The `.git/` reflog contains machine identity data, but it is not tracked and is outside both the
public tree and CI scan. The scanner must enumerate tracked files through Git rather than recursively
walking the working directory, or it will report private local metadata that is never being
published.

The three tracked home-path mentions are remediated to generic placeholders in this change. They
must not be allowlisted: allowing the real host prefix would disable the exact rule meant to catch a
future leak.

## Requirements

### Shared scanner

1. Add a standard-library Python module and CLI at `scripts/privacy_scan.py`. One rule engine is
   imported or invoked by every surface; hooks may adapt input shape but must not duplicate pattern
   definitions.
2. The scanner returns structured findings containing only category, repository-relative path,
   one-based line number, and remediation. It never returns, prints, hashes, serializes, or logs the
   matched value or surrounding source line.
3. The CLI supports a full tracked-tree mode for CI. It obtains paths from `git ls-files -z`, never
   follows untracked files, `.git/`, ignored files, symlink targets outside the repository, or a
   recursive filesystem walk.
4. The CLI supports a pre-push mode that reads Git's standard pre-push ref-update lines and scans
   every outgoing commit tree, not only the current worktree. A value added in one outgoing commit
   and deleted in a later one must still block before either commit is published.
5. New-branch pushes derive outgoing commits from the local object graph excluding refs already on
   the named remote. Existing-branch pushes use the supplied remote SHA to local SHA range. Deleting
   a remote ref scans no content. Invalid ref input fails closed without echoing the input line.
6. Files are read as bytes. A NUL byte classifies a file as binary and produces an explicit skipped
   count. Non-binary bytes that are not valid UTF-8 are an error in CLI/CI, not a clean result.
7. Findings are deterministic and stably ordered by path, line, then category. Exit 0 means no
   finding and valid configuration; exit 1 means one or more findings; exit 2 means invalid
   configuration/input or an infrastructure error.

### Detection rules

8. High-confidence rules cover:
   - Unix developer-home paths under `/home/<name>/` and `/Users/<name>/`;
   - Windows user-home paths under a drive's `Users` directory;
   - configured host/user markers;
   - syntactically valid email addresses;
   - phone-like values only on a line carrying an explicit phone/contact label;
   - 13–19 digit payment-card-shaped values only when the digits pass the Luhn checksum;
   - PEM private-key headers;
   - bearer credentials;
   - selected high-confidence AWS, GitHub, and Slack credential prefixes.
9. The scanner does not infer whether an ordinary person's name, prose sentence, city, IP address,
   or unlabeled number is PII. Documentation states those permanent false-negative boundaries.
10. Patterns operate on decoded text but do not treat repository URLs, immutable commit SHAs,
    ordinary `token` prose, or workflow expressions as findings unless they match a supported
    credential form.

### Configuration and allowlist

11. Add `.privacy-allowlist.json` with an integer schema version, exact allowed values, anchored
    allowed patterns, and configured host/user markers. Unknown fields, unsupported schema,
    malformed regex, unanchored allow patterns, duplicate entries, or non-string entries fail
    closed.
12. The initial allowlist permits only reserved example-domain addresses, GitHub noreply addresses,
    and any exact existing public owner identity value actually required by a detection rule. It
    contains no personal mailbox, phone number, live token, broad path exclusion, or generic
    catch-all regex.
13. An allowlist match suppresses only the matched finding value. It cannot skip a file, directory,
    category, line, hook surface, or CI mode.

### Agent write-time hook

14. Add `scripts/privacy_pretooluse_hook.py` plus `.kiro/hooks/privacy-scan.json`, using the official
    repository-local Kiro v1 hook format: `trigger: PreToolUse`, `matcher: write`, command action,
    bounded timeout, and enabled state.
15. The hook accepts both `preToolUse` and `PreToolUse` event spellings, case-insensitively, and is
    inert for other events or non-write tools.
16. The hook scans only content the tool proposes to add: complete write/insert content and
    replacement `newStr` / `new_str` / `text` values, recursively across multi-operation payloads.
    It must not scan `oldStr` / `old_str`; sensitive data must remain removable.
17. A positive finding blocks with exit 2 and a redacted category/path/line diagnostic. Invalid JSON,
    a missing content field, missing Python, missing scanner, or an internal exception fails open
    with exit 0; where possible it emits an infrastructure warning that contains no payload data.
18. The hook resolves the target path relative to event `cwd`, reports a repository-relative path,
    and does not scan writes outside the opted-in repository.

### Human terminal pre-push hook

19. Add executable `.githooks/pre-push` as a POSIX shell adapter that passes Git's stdin unchanged to
    `scripts/privacy_scan.py --pre-push --remote <remote-name>`. It never prints the ref-update input.
20. Add `scripts/install_privacy_hooks.sh`. It verifies POSIX, Python, Git, repository root, scanner,
    and hook executability before setting the repository-local `core.hooksPath` to `.githooks`.
21. The installer refuses rather than overwrites when `core.hooksPath` already names another path or
    an active `.git/hooks/pre-push` would be displaced. It reads the configured value back and runs
    a safe scanner smoke test before claiming installation succeeded.
22. Documentation states that the terminal hook is POSIX-only, opt-in, bypassable with
    `--no-verify`, and absent until the installer has completed. CI is the binding backstop.

### CI and repository integration

23. Add `.github/workflows/privacy-scan.yml` with unfiltered `pull_request`, `push` limited to
    `main`, and `workflow_dispatch`; workflow-level `contents: read`; no secret; and one stable
    non-matrix job with display name `privacy scan`.
24. The CI job checks out full history, sets up Python 3.12, runs all privacy scanner/hook tests, then
    runs the full tracked-tree scanner. Neither step uses `continue-on-error`.
25. Extend `verify.py` before implementation so it fails on missing scanner, tests, allowlist, hook,
    installer, workflow, README claims, or the three existing host-path literals. Its workflow
    checks reuse the existing indentation-bounded YAML helpers and prove the privacy PR trigger is
    unfiltered, read-only, secret-free, stably named, and fail-closed.
26. Update `README.md` with supported categories, one-command full scan, POSIX hook installation and
    verification, CI behavior, allowlist review rules, `--no-verify` bypass, and the statement that a
    clean scan is not proof of no PII or privacy compliance.
27. Replace only the three literal real-host markers identified in the baseline with generic
    `/home/<user>/` or equivalent wording. Preserve each shipped artifact's status, authorship,
    approval, binding, and historical meaning.
28. Do not modify `index.html`; this change has no rendered Portal delta and needs no viewport
    evidence.

### Verification and deployment

29. Tests are committed and observed red before scanner implementation. A missing scanner is
    reported as a test failure, not an uncaught import traceback.
30. Test fixtures use clearly synthetic markers held only in test input. Captured stdout/stderr is
    asserted not to contain the fixture value for every success, finding, and error path.
31. Tests cover every category, positive/negative Luhn cases, labeled/unlabeled phone cases,
    allowlist acceptance/refusal, stable ordering, binary skip counts, invalid UTF-8, tracked-only
    enumeration, symlink containment, all hook event spellings and content keys, old-value removal,
    hook fail-open paths, pre-push new/existing/deleted refs, and installer conflict refusal.
32. The checked-in Kiro command is exercised in a hermetic temporary repository. The terminal hook
    is installed and invoked in a temporary Git repository. File presence or JSON validity alone is
    not functional evidence.
33. A real PR must show `portal verify`, `sdlc-gate / sdlc-gate`, and `privacy scan` successful. The
    exact privacy context is copied from the check-run API before branch protection is updated.
34. Adding `privacy scan` to protected `main` requires an immediate owner confirmation of the final
    protection payload. Read-back must preserve strict mode, owner enforcement, zero approvals,
    force-push/deletion denial, and the two existing required checks.
35. After merge and protection verification, a separate artifact-only PR marks this chain shipped
    before responsive PR 1 begins.

## Non-functional requirements

- **No sensitive diagnostic data.** Redaction is a tested interface contract, not a best-effort log
  convention.
- **Standard library.** Scanner, adapters, tests, configuration parser, Git integration, and CI add
  no Python package dependency. Specialist secret scanning remains separate work.
- **Bounded work.** Reject a text file larger than a documented maximum rather than silently skip it;
  the repository is small enough that the chosen limit must cover every current tracked text file.
- **Deterministic output.** Identical tracked trees and configuration produce identical category,
  path, line, count, ordering, and exit status.
- **Least privilege.** CI has read-only contents permission. Hooks read proposed/tracked content and
  Git metadata only; they do not perform network requests or write repository files.
- **Fail posture is explicit.** Agent hook infrastructure errors fail open; scanner CLI, terminal
  pre-push input errors, and CI configuration errors fail closed.
- **Performance.** Full-tree scanning of the current repository completes within five seconds on the
  development host; a single agent event within one second, excluding host tool startup.
- **Portability honesty.** Scanner Python supports the repository's chosen CI version. The terminal
  adapter is POSIX-only. No Windows terminal-hook claim is made.
- **Public-log safety.** GitHub Actions annotations and summaries contain no source line, match,
  digest, encoded match, or fixture value.
- **No certification claim.** The feature is described as a high-confidence guardrail with declared
  blind spots, not a DLP product, privacy audit, compliance control, or complete secret scanner.

## Design

### 1. Rule engine and result model

`privacy_scan.py` defines immutable finding records and pure `scan_text` / Luhn / allowlist
functions. Match objects are converted immediately into redacted finding metadata; raw matches do
not cross the rule function boundary. Rendering receives no sensitive value, making accidental log
leakage structurally harder.

### 2. Tracked-tree scanner

The CLI asks Git for NUL-delimited tracked paths. For an ordinary full-tree scan it reads each path
without following an external symlink. For pre-push it enumerates outgoing commits from the ref
updates and reads each commit's tree through Git, so a value removed by a later outgoing commit is
still found before publication. Duplicate findings across identical commit trees are collapsed by
category/path/line while preserving the commit id prefix as non-sensitive location context only if
needed for remediation.

### 3. Rule configuration

`.privacy-allowlist.json` carries `schema_version: 1`, narrow allowed-value/pattern lists, and explicit
host/user markers. Configuration validation runs before content scanning. Allowed patterns must
begin with `^` and end with `$`; this prevents a partial regex from silently suppressing unrelated
findings.

### 4. Hook adapters

The Kiro adapter parses the event and extracts only new text fields. It calls the pure scanner in
memory, so proposed data is not written to a temporary file. Its top-level exception boundary
returns 0 after a generic warning. A finding returns 2.

The POSIX pre-push adapter is intentionally thin and contains no detection rule. The installer
refuses conflicts and configures only the current repository, never global Git settings.

### 5. CI

The `privacy scan` job runs tests before the full-tree command. Required-check protection is added
only after a real successful PR check establishes the exact context. There is no trigger filter on
pull requests and no model or external service in the detection path.

### 6. Existing baseline remediation

The three real host-prefix mentions in `review-follow-ups` are rewritten to generic placeholder
language in the implementation commit. The scanner test then asserts that no tracked developer-home
marker remains. No historical commit is rewritten; already-published history remains public and is
named as out of scope.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| A finding could republish the protected value in Actions logs | Security owner | Finding model never carries match text; tests assert fixture absence from every captured output. |
| Full filesystem walking exposes private `.git` reflog identity | Repository owner | Enumerate only `git ls-files`; hermetic test plants untracked and `.git` values and proves they are ignored. |
| Three shipped artifacts contain the real host prefix in historical prose | Repository owner | Replace with generic placeholders; do not allowlist the host. Preserve statuses and meaning. |
| A committed Git hook can be mistaken for an installed control | Repository owner | Installer verifies local `core.hooksPath`; README says absent until installed; integration test invokes installed hook. |
| Installing hooks could disable an existing hook chain | Repository owner | Refuse conflicting `core.hooksPath` or active legacy pre-push hook; never overwrite or compose silently. |
| `--no-verify` bypasses pre-push | Repository owner | State it openly; required unfiltered CI is the fail-closed backstop. |
| CI sees a public branch only after a secret may already be pushed | Repository owner | Local pre-push scans every outgoing commit tree; CI protects merge/main but cannot unpublish remote branch history. |
| Standard-library credential patterns could be called complete secret scanning | Security owner | Document selected prefixes and blind spots; Gitleaks or another specialist remains a separate dependency decision. |
| Name/prose detection would create unbounded false positives | Privacy owner | Do not infer names or free prose; retain human review responsibility. |
| An allowlist can become a bypass mechanism | Security owner | Exact or anchored value rules only; no path/category skip; malformed/broad entries fail closed and are reviewed in PR. |
| Invalid UTF-8 could be silently skipped as binary | Security owner | Only NUL identifies binary; invalid non-binary UTF-8 fails closed. |
| Windows users could believe the terminal hook protects them | Repository owner | Mark adapter POSIX-only in code, tests, README, and support statement; CI remains platform-independent. |
| Tests may prove their own assumptions rather than real hooks | Skill maintainer | Exercise shipped Kiro command and installed pre-push hook in temporary Git repositories. |
| Required context update can lock every PR | Repository owner | Read exact successful check-run name, confirm payload immediately before mutation, and read protection back. |

## Rejected alternatives

- **Add Gitleaks inside this change — rejected by the accepted intent.** Broader secret scanning is
  valuable but is a separately pinned dependency and does not replace PII rules.
- **Scan the recursive working directory — rejected.** It captures `.git`, ignored files, local
  settings, caches, and other data that is not being published.
- **Print or hash the match to help remediation — rejected.** Both republish derived sensitive data;
  category/path/line is sufficient.
- **Scan `oldStr` in replacement events — rejected.** It would block removing the sensitive value.
- **Full-tree-only pre-push — rejected.** A secret added then deleted in later outgoing history would
  still be published.
- **Automatically overwrite existing Git hook configuration — rejected.** Silent hook loss is worse
  than an explicit installation refusal.
- **Allowlist the current host path — rejected.** It defeats the exact leak this control must catch.
- **Require Windows terminal support without an exercised native hook — rejected.** CI provides the
  honest cross-platform backstop.
- **Use path filters on the privacy workflow — rejected.** A required check excluded by its trigger
  blocks a PR forever waiting for a status that cannot arrive.

## Out of scope

- Gitleaks or another third-party secret scanner.
- Rewriting or purging already-published Git history.
- Name/entity recognition, OCR, image metadata, natural-language classification, or remote DLP APIs.
- A Windows-native terminal hook.
- Organization-wide policy distribution, external audit custody, or privacy certification.
- Responsive UI, diagrams, mentor/self-paced modes, or any `index.html` change.

---
Gate: owner signs off; flagged concerns worked first. Applied org skill: `ai-native-sdlc`; Kiro hook
shape and fail-open contract were read from its shipped repository-local hook and
`sdlc_pretooluse_hook.py` implementation before this design was written.
