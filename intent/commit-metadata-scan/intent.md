# Intent: scan outgoing commit identity metadata before it is published

- **Slug:** commit-metadata-scan
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-10-06
- **Status:** accepted
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/12

## Problem

The privacy controls shipped by `automatic-pii-scanning` read file content only. The pre-push hook
scans the tree of every outgoing commit, and the `privacy scan` CI check scans the tracked tree. No
layer reads the author or committer fields of a commit.

Those fields are published with every push. When a repository-local identity is unset, Git builds
an email address from the local user and host name, and on a cloud host that address names an
internal machine. A commit carrying it passes every current check with zero findings, because the
leak is in the commit object rather than in any file. The tree scan's clean result is therefore
true but answers a different question from "is it safe to push this commit".

Today the exposure is zero: every author and committer email on `main` is either a GitHub noreply
address or the GitHub web-flow address. The gap is that nothing would notice the first exception.

## Desired outcome

Before a commit is published, its identity metadata is checked by the same scanner, the same
reviewed allowlist and the same redacted output as file content. An identity that is not an
approved public identity blocks the push and names which field of which commit failed, without
printing the value. The documentation states plainly that tree content and commit metadata are
separate surfaces with separate checks.

## Affected users / systems

- The owner and any contributor pushing from a terminal with the opt-in pre-push hook installed.
- `scripts/privacy_scan.py`, its tests, and the mutation proof.
- `.privacy-allowlist.json`, the single reviewed allowlist.
- The `privacy scan` required CI check, if the CI layer is extended (decision 1 below).
- `README.md`, which documents what the privacy controls cover.

## Constraints

- Scope is Issue #12 only. No portal content, layout, learning-mode or Playbook change.
- Never print, log, hash into a diagnostic or otherwise reproduce a matched identity value. A
  finding exposes only category, an abbreviated commit id, and the field name (for example
  `author-email`).
- Reuse the existing `Finding` output format and exit-code contract. Infrastructure errors keep the
  documented behaviour: the pre-push hook and CI fail closed (exit 2).
- One allowlist. Identity rules read `.privacy-allowlist.json`; no second allowlist file, and no
  broad path or commit exclusion.
- Emails are judged by allowlist, not by "looks internal": any author or committer email that does
  not match a reviewed public pattern is a finding. Host-name heuristics alone would miss a personal
  mailbox and would invite a growing list of cloud host suffixes.
- Names are not classified as PII by themselves (the shipped intent's rule). Name fields are passed
  through the existing high-confidence content rules only, so a developer-home path or email typed
  into a name field is still caught.
- The required `privacy scan` CI context keeps its exact name and its unfiltered `pull_request`
  trigger.
- Tests are written and observed failing before implementation, using unmistakably synthetic
  identities (reserved domains such as `example.invalid`), never a real mailbox or host.
- Already-published history is not rewritten. Existing `main` history is clean, which a read-only
  check confirms before the change is described as safe.
- The agent does not push, self-approve artifacts, or merge.

## Success criteria

1. A synthetic outgoing commit whose author or committer email is not allowlisted (including an
   internal-host-shaped address) makes `privacy_scan.py --pre-push` exit non-zero, and its output
   does not contain the email, its local part, or its domain.
2. A commit with a GitHub noreply author and committer is allowed.
3. A sensitive identity in an earlier commit of a multi-commit push is still detected, and each
   offending commit is reported once per field.
4. A malformed or unreadable commit object, or a Git failure while reading metadata, keeps the
   existing fail-closed exit code.
5. The real `.githooks/pre-push` hook, invoked as Git invokes it against a scratch repository with a
   local bare remote, blocks the bad push and allows the good one.
6. The mutation proof gains metadata mutations (identity scanning disabled; earlier commits
   skipped; value leaked into output), and every one is killed.
7. The `privacy scan` CI check stays green on this pull request with its name and trigger unchanged.
8. `README.md` names the two surfaces separately and states what metadata scanning does not cover.
9. The chain closes as `shipped` through an artifact-only pull request.

## Decisions accepted

All four decisions below were accepted as proposed, including decision 1 (CI scans the pull
request's commits).

1. **CI also scans the pull request's commits (recommended).** The pre-push hook is opt-in and
   POSIX-only, so it cannot be the only control; the shipped design made CI the backstop for
   content, and metadata needs the same backstop. CI would scan only the commits in
   `merge-base..head` of the pull request, not all history, inside the existing `privacy scan` job.
   The alternative is pre-push only, exactly as Issue #12 is worded, accepting that a contributor
   without the hook is unprotected.
2. **Allow the GitHub web-flow identity exactly.** Commits GitHub creates (merges and "Update
   branch" in the web UI) carry GitHub's own web-flow committer address (local part `noreply`,
   domain `github.com`), which the current `users.noreply.github.com` pattern does not match. Add
   that single exact value to the allowlist with a reason; no wider GitHub pattern.
3. **Fields covered: author name, author email, committer name, committer email.** Commit messages
   (including `Co-authored-by:` and `Signed-off-by:` trailers) and annotated-tag tagger identities
   are also published but are out of scope here; the README records them as an uncovered surface,
   and a follow-up issue tracks them.
4. **No new script.** Identity scanning lives in `scripts/privacy_scan.py` behind the existing
   `--pre-push` path and one new CI flag, so all layers keep sharing one scanner.

---
Gate: product owner accepts. The accepting commit is the record.
