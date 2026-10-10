# Spec: scan commit messages and trailers with the shared privacy scanner

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Measured baseline

Measured at `2e22706` (current `main`) without printing any value.

- `scripts/privacy_scan.py` (517 lines) checks the tree of every outgoing commit and, through
  `_commit_identity`, the author and committer header lines. It splits the raw commit object at the
  first blank line and reads only the header; the message after that blank line is never read.
- `--pre-push` and `--commit-range BASE HEAD` both call `scan_commit_identities`. The `privacy
  scan` CI job runs `--commit-range` on `pull_request` only, with both SHAs passed through `env:`.
- `MetadataFinding` has four fields (`commit`, `field`, `category`, `remediation`) and renders as
  `category=<c> commit=<12 hex> field=<f>`.
- `.privacy-allowlist.json` (schema 1, unknown keys rejected) has 2 `allowed_exact` values and 2
  `allowed_patterns`.
- Privacy tests: 47 passing. Mutation proof: 13 killed (10 category, 3 identity). Portal verifier:
  386/386. `verify.py` asserts the README lists "commit messages and their trailers" as **not**
  covered.
- `main` holds 131 commits. Passing each message through `scan_text`: 14 messages give one
  `email` finding each, all in a `Co-Authored-By:` trailer, all the same single value (local part
  `noreply`, a coding-agent vendor's public domain). No other category appears. No commit on
  `main` has an `encoding` header.

## Requirements

### Reading the message

1. The message is the bytes after the first blank line of the raw commit object
   (`git cat-file commit <sha>`), the same object `_commit_identity` already reads, so `.mailmap`,
   `git log` formatting and `notes` cannot change what is checked. Subject, body and trailers are
   all part of it; trailers get no separate parser.
2. The message must decode as strict UTF-8. A header `encoding` line whose value is not `UTF-8`
   (case-insensitive, with or without the hyphen) or message bytes that do not decode raise
   `ScanError`, so every enforcing layer exits 2. The error names the abbreviated commit id only.
3. An empty message is valid and has no findings.

### Rules

4. The message is passed through the existing `scan_text` rules unchanged, with the same
   `_allowed()` allowlist. Each resulting finding keeps that rule's category (for example `email`
   or `developer_home`). No message-only rule and no message-only relaxation is added.
5. **One added allowlist value.** The vendor bot address found in the baseline is added to
   `allowed_exact` as one exact string. No new pattern is added, and no `noreply@` local-part rule.
   The reason is recorded in the README allowlist paragraph and in this spec, because the schema
   rejects extra keys. The README names the vendor's product but does not write the address out.

### Output

6. A message finding renders as
   `PRIVACY FINDING: category=<category> commit=<first 12 hex> field=message line=<n>; <remediation>; matched value redacted`,
   where `<n>` is the 1-based line within the message. `MetadataFinding` gains an optional `line`
   (default none); identity findings render byte-for-byte as today.
7. Findings are deduplicated per (commit, field, line, category) and sorted. Output never contains
   the matched value, its local part, its domain, the matched line's text, or a hash of any of them.
8. The summary line `privacy scan: <N> commit identities checked` becomes
   `privacy scan: <N> commits checked (identity and message)`. The tree-content summary line is
   unchanged.

### Enforcement layers

9. `--pre-push` and `--commit-range` check the message of exactly the commit set they already check
   for identity: every outgoing commit, not only the tip. `.githooks/pre-push`, the CLI flags and
   `.github/workflows/privacy-scan.yml` are unchanged (intent decision 4).
10. The tracked-tree default mode and the Kiro write-time hook do not read messages.

### Tests and mutation proof

11. Tests are committed and observed failing before scanner code changes. Synthetic values are
    assembled at runtime (as `private_email()` does with `chr(64)`) under reserved names
    (`example.invalid`, a `/home/<user>/`-style path). The vendor address is not written as a
    literal in any test; the allowlisted-trailer test reads it from `.privacy-allowlist.json`.
12. Unit tests in `scripts/test_privacy_scan.py` cover:
    - a non-allowlisted email in the message body, a finding at the right line;
    - a non-allowlisted email in a `Co-authored-by:` trailer and in a `Signed-off-by:` trailer;
    - a developer-home path in the subject line, a finding under `developer_home`;
    - GitHub noreply and the allowlisted vendor address in trailers, allowed;
    - a bad message in the first of three outgoing commits, found by both `--pre-push` and
      `--commit-range`;
    - an `encoding: ISO-8859-1` commit and a message with invalid UTF-8 bytes (written with
      `git hash-object -t commit --literally`), both exit 2;
    - an empty message, allowed;
    - stdout and stderr containing none of the synthetic value, its local part, its domain or the
      offending line's text.
13. `scripts/test_privacy_pre_push.py` adds a real-hook case: a push whose only problem is in a
    trailer is refused and nothing reaches the local bare remote; the same commit with a noreply
    trailer is accepted.
14. `scripts/privacy_mutation_proof.py` keeps its 13 mutations and adds three anchored message
    mutations, each of which must fail the tests:
    - message checking disabled (no message findings are produced);
    - trailers dropped (only text before the trailer block is scanned);
    - the offending line's text written into the rendered finding.

    Required result: **16 killed, 0 survived, 0 broken**, with the existing unmutated control run
    passing first.
15. `verify.py` `privacy_checks()` replaces the "uncovered commit messages" check with checks, red
    before implementation, that the README lists commit messages and trailers as a **covered**
    surface, still lists tag identity and GitHub-created merge commits as not covered, and gives the
    vendor-address reason. The other 385 checks stay green.

### Documentation

16. The README "Two published surfaces" section becomes three: tree content, commit identity
    metadata, and **commit messages** (subject, body and trailers; checked by the pre-push hook and
    by CI with `--commit-range`; findings name the commit, field and line, never the value). The
    "Not covered" line keeps annotated-tag tagger identity, merge commits GitHub creates on `main`,
    and already-published history, and drops commit messages.
17. The pull request links Issue #20 and does not close it.

## Verification

- Portal verifier all green; privacy unit tests all passing; mutation proof 16/16 killed.
- Tracked-tree scan 0 findings; pre-push hook over every unpushed commit 0 findings;
  `--commit-range $(git merge-base origin/main HEAD) HEAD` 0 findings.
- A read-only check of all `main` messages with the new allowlist reports 0 findings
  (intent criterion 7).
- `privacy scan` stays green on the pull request, and its log shows the new summary line.
- No portal page changes, so no rendered-browser evidence is required.

## Allowed files

`scripts/privacy_scan.py`, `scripts/test_privacy_scan.py`, `scripts/test_privacy_pre_push.py`,
`scripts/privacy_mutation_proof.py`, `.privacy-allowlist.json`, `verify.py`, `README.md`,
`.sdlc/active` and this chain's artifacts. `index.html`, `plays.html`, `.githooks/pre-push`, the
CI workflows, the installer, the Kiro write-time hook and its config, the SDLC gate and branch
protection are not changed.

## Flagged concerns

- **The summary line changes wording.** Requirement 8 rewrites the identity summary line so it
  does not undercount what was checked. Nothing in CI or `verify.py` parses it today; the tests
  are updated with it.
- **Prose false positives are possible.** The phone and card rules were tuned on files, not on
  messages. Measured on `main` they produce 0 message hits. If a future message trips one, the
  author rewords before pushing (a message is still local then); the rule is not relaxed for
  messages.
- **Squash-merge messages are written by GitHub at merge time** and fall outside the pull request's
  range, like merge commits. They stay with the merge-commit chain of Issue #20.
- **A legacy-encoded message blocks the push.** That is deliberate (intent decision 3); the error
  names only the commit.
- **The allowlist grows to 3 exact values.** Each one is a public bot or GitHub-owned address; the
  README explains each.

---
Gate: product owner signs off. The sign-off commit is the record.
