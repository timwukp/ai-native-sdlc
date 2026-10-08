# Spec: scan commit identity metadata with the shared privacy scanner

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Measured baseline

Measured at `f6eef81` (current `main`) without printing any identity value.

- `scripts/privacy_scan.py` (412 lines) has two modes. The default scans the tracked tree. With
  `--pre-push` it computes the outgoing commit set (`_outgoing_commits`, deduplicated) and scans
  the **tree** of each commit through `_scan_treeish`. No code path reads a commit object's
  `author` or `committer` header.
- `.github/workflows/privacy-scan.yml` (job `privacy-scan`, name `privacy scan`) runs the privacy
  unit tests, the mutation proof and the tracked-tree scan. It checks out full history
  (`fetch-depth: 0`). Nothing reads commit metadata.
- `.privacy-allowlist.json` (schema 1, unknown keys rejected) allows the exact string `Tim WU`
  and two anchored patterns: GitHub noreply addresses (`users.noreply.github.com`) and
  `example.com|org|net`. It has no field for a per-entry reason.
- `scripts/privacy_mutation_proof.py` deletes each of the 10 `RULES` entries in turn and requires
  `scripts/test_privacy_scan.py` to fail: 10/10 killed. Privacy tests: 31 passing.
- `verify.py` `privacy_checks()` asserts the workflow's three commands, its trigger, permissions,
  job id and name, and several README claims. Portal verifier: 373/373.
- `main` holds 109 commits, i.e. 218 author/committer lines. 205 match the noreply pattern, 13 are
  GitHub's web-flow committer address, and **0** match neither. Existing history is clean, and
  intent constraint "already-published history is not rewritten" needs no remediation.

## Requirements

### Reading identity metadata

1. Identity is read from the raw commit object (`git cat-file commit <sha>`), not from formatted
   `git log` output, so `.mailmap` and display options cannot change what is checked. Only the
   header block before the first blank line is parsed.
2. The header must contain exactly one `author ` line and exactly one `committer ` line, each of
   the form `<name> <<email>> <unix-seconds> <+|-hhmm>`. A missing, duplicated or unparseable line,
   header bytes that are not strict UTF-8, or a failing Git call raises `ScanError`, so every
   enforcing layer exits 2 (intent success criterion 4). The error names the abbreviated commit
   id only, never a value.
3. Exactly four fields are checked: `author-name`, `author-email`, `committer-name`,
   `committer-email`. The message, its trailers (`Co-authored-by:`, `Signed-off-by:`), `gpgsig`,
   `encoding` and tag objects are not read.

### Rules

4. **Email fields are allowlist-judged.** A `*-email` field is a finding (category
   `commit_email`) unless the whole value is in `allowed_exact` or fully matches an
   `allowed_patterns` entry, through the same `_allowed()` used for content. An empty email is a
   finding. No host-name or "looks internal" heuristic is added.
5. **Name fields reuse the content rules.** A `*-name` field is passed through the existing
   `scan_text` rules unchanged; each resulting finding keeps that rule's category (for example
   `developer_home` or `email`). A name is never a finding merely for being a name.
6. **One added allowlist value.** GitHub's web-flow committer address (local part `noreply`,
   domain `github.com`) is added to `allowed_exact` as one exact string. No new pattern is added.
   Because the schema rejects unknown keys, the reason is recorded in the README allowlist text
   and in this spec, not in the JSON.

### Output

7. A metadata finding renders on one line as
   `PRIVACY FINDING: category=<category> commit=<first 12 hex> field=<field>; <remediation>; matched value redacted`.
   Findings are deduplicated per (commit, field, category) and sorted, so an offending commit is
   reported once per field (intent success criterion 3). Content findings keep their exact current
   format.
8. Output never contains the matched value, its local part, its domain, or any hash of them. When
   identity checks ran, the summary prints one extra line,
   `privacy scan: <N> commit identities checked`; the existing summary line is unchanged.

### Enforcement layers

9. **Pre-push.** `--pre-push` checks the identities of exactly the outgoing commit set it already
   computes for tree scanning, every commit and not only the tip. Branch deletions are skipped as
   today. `.githooks/pre-push` is unchanged, since it already forwards stdin to `--pre-push`.
10. **CI flag.** A new flag `--commit-range BASE HEAD` takes two full 40-hex ids, rejects anything
    else with exit 2, and checks identities only of `git rev-list <merge-base(BASE, HEAD)>..HEAD`.
    It does not rescan tree content and cannot be combined with `--pre-push`. An empty range is 0
    commits and passes. The argument parser keeps `allow_abbrev=False`.
11. **CI step.** `privacy-scan.yml` gains one step after the tree scan, run only when
    `github.event_name == 'pull_request'`. It passes `github.event.pull_request.base.sha` and
    `head.sha` through `env:` and references them as shell variables, never as inline `${{ }}`
    in `run:`. Job id, display name, triggers and permissions are unchanged, and no step uses
    `continue-on-error`. Push-to-`main` and manual runs do not run this step (see Flagged concerns).

### Tests and mutation proof

12. Tests are committed and observed failing before scanner code changes. Every synthetic identity
    is assembled at runtime (as `private_email()` already does with `chr(64)`) under reserved
    names: `example.invalid`, an internal-host-shaped domain built on the TEST-NET address
    `192.0.2.1` with an `.internal` suffix, and a `/home/<user>/`-style path in a name. No literal
    address appears in a committed file.
13. Unit tests in `scripts/test_privacy_scan.py` build throwaway repositories and cover:
    - a non-allowlisted author email, a non-allowlisted committer email, and the internal-host
      shape, each one a finding;
    - noreply author and committer, and the web-flow committer, allowed;
    - a developer-home path in a name, a finding under `developer_home`;
    - a bad identity in the first of three outgoing commits, reported once per field;
    - a malformed commit object (written with `git hash-object -t commit --literally`, missing its
      committer line) and an unknown object id, both exit 2;
    - `--commit-range` scanning only the range, rejecting short ids, and rejecting combination with
      `--pre-push`;
    - stdout and stderr containing none of the synthetic value, its local part or its domain.
14. `scripts/test_privacy_pre_push.py` runs the real `.githooks/pre-push` as Git invokes it, in a
    scratch repository with a local bare remote: the bad push is refused and nothing reaches the
    remote; the good push succeeds (intent success criterion 5).
15. `scripts/privacy_mutation_proof.py` keeps its 10 category mutations and adds three anchored
    metadata mutations, each of which must fail the tests:
    - identity checking disabled (the metadata check returns no findings);
    - only the last outgoing commit's identity checked;
    - the matched value written into the rendered finding.

    The proof copies every test file that holds metadata tests into its temporary tree. The
    required result is **13 killed, 0 survived, 0 broken**.
16. `verify.py` `privacy_checks()` adds checks, red before implementation, that the workflow has
    the `--commit-range` command, gates it on `pull_request`, and passes both SHAs through `env:`;
    and that the README states the surfaces in requirement 17. The existing 373 checks stay green.

### Documentation

17. The README privacy section names **tree content** and **commit identity metadata** as separate
    surfaces and states which layer covers which: the Kiro write-time hook covers content only; the
    pre-push hook covers content and outgoing-commit identity; CI covers the tracked tree and the
    pull request's commit identities. It lists what is **not** covered: commit messages and
    trailers, annotated-tag tagger identity, identity on push-to-`main` and manual runs, and
    already-published history. It records why the web-flow address is allowlisted.
18. A follow-up issue for the uncovered surfaces is opened and linked from the pull request
    description before the pull request is marked Ready.

## Verification

- Portal verifier all green; privacy unit tests all passing; mutation proof 13/13 killed.
- Tracked-tree scan 0 findings; pre-push hook over every unpushed commit 0 findings;
  `--commit-range $(git merge-base origin/main HEAD) HEAD` 0 findings.
- The read-only `main` history check is re-run and still reports 0 non-allowlisted identities.
- `privacy scan` stays green on the pull request with name and trigger unchanged (intent
  criterion 7).
- No portal page changes, so no rendered-browser evidence is required.

## Allowed files

`scripts/privacy_scan.py`, `scripts/test_privacy_scan.py`, `scripts/test_privacy_pre_push.py`,
`scripts/privacy_mutation_proof.py`, `.privacy-allowlist.json`,
`.github/workflows/privacy-scan.yml`, `verify.py`, `README.md`, `.sdlc/active` and this chain's
artifacts. `index.html`, `plays.html`, `.githooks/pre-push`, the installer, the Kiro write-time
hook and its config, the SDLC gate and branch protection are not changed.

## Flagged concerns

- **Merge commits on `main` are not checked before publication.** The merge commit GitHub creates
  when a pull request merges is outside the pull request's range, and its author is the merging
  account's configured email. If that account ever stops using a private address, nothing here
  catches it beforehand. The real control is the account's GitHub settings ("Keep my email
  addresses private" and "Block command line pushes that expose my email"), which only the owner
  can confirm; they cannot be verified from the repository. All 109 existing commits are clean.
- **Reason for the allowlisted address lives outside the JSON.** Intent decision 2 asked for a
  reason; the schema rejects extra keys, and changing the schema is out of scope.
- **CI depends on the event's base SHA being present.** Full-history checkout fetches it. If it is
  ever missing, the step exits 2 and the check goes red; it does not pass silently.
- **Strict UTF-8 can block a legitimate push** whose name uses a legacy encoding. That fails
  closed and names only the commit.
- **`example.com|org|net` identities are allowed** because they share the content allowlist. They
  are public placeholders, so this is accepted rather than adding a second allowlist.

---
Gate: product owner signs off. The sign-off commit is the record.
