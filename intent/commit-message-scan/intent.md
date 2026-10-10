# Intent: scan outgoing commit messages and trailers before they are published

- **Slug:** commit-message-scan
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Date:** 2026-10-10
- **Status:** draft
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/20 (first of three surfaces)

## Problem

The privacy controls check two surfaces before publication: file content in every outgoing tree,
and the author and committer identity of every outgoing commit. The commit message is a third
published surface and no layer reads it. A message body or a trailer such as `Co-authored-by:` or
`Signed-off-by:` can carry a personal email address, a developer-home path or a pasted token, and
it passes every current check with zero findings.

A read-only measurement of `main` (131 commits, values not printed) found:

- 14 messages produce findings under the existing content rules. All 14 are category `email`, all
  sit in a `Co-Authored-By:` trailer, and all are one distinct value: a coding-agent vendor's
  public bot address whose local part is `noreply`. None is a personal mailbox.
- No other category (home path, phone, card, key or token) appears in any message.

So the exposure today is zero, but enabling message scanning as it stands would turn CI red on
the first run, because of an address that is public by design.

## Desired outcome

Before a commit is published, its full message (subject, body and trailers) passes through the same
scanner, the same reviewed allowlist and the same redacted output as file content. A finding names
the commit, the field `message` and the line within the message, never the value. Public bot
addresses that are meant to appear in trailers are allowed by an exact, reviewed allowlist entry,
not by a looser rule.

## Affected users / systems

- Anyone pushing with the opt-in pre-push hook, and every pull request through the `privacy scan`
  CI check.
- `scripts/privacy_scan.py`, its tests and the mutation proof.
- `.privacy-allowlist.json`, the single reviewed allowlist.
- `README.md`, which lists covered and uncovered surfaces.

## Constraints

- Scope is commit messages only. Annotated-tag tagger identity and the merge commits GitHub creates
  on `main` remain open under Issue #20 as their own chains; this pull request does not close #20.
- Messages use the existing content rules unchanged. No message-specific relaxation and no
  per-commit exclusion.
- Never print, log or hash a matched value. Output exposes category, abbreviated commit id, field
  `message` and line number only.
- The pre-push hook and CI keep their fail-closed exit 2 when a message cannot be read or decoded.
- The required `privacy scan` CI context keeps its exact name and unfiltered `pull_request` trigger.
- One allowlist file; reasons for an entry live in the README and spec, because the schema rejects
  unknown fields.
- Tests are written and observed failing first, using reserved synthetic values only.
- Published history is not rewritten. A read-only check over `main` must show 0 message findings
  once the allowlist decision is applied.
- The agent does not push, self-approve artifacts or merge.

## Success criteria

1. A synthetic outgoing commit whose message body or trailer carries a non-allowlisted email or a
   developer-home path makes `--pre-push` and `--commit-range` exit non-zero, and the output does
   not contain the value.
2. A message with only allowlisted addresses (GitHub noreply, and the reviewed bot address) passes.
3. A bad message in an earlier commit of a multi-commit push is still found.
4. An undecodable message keeps the fail-closed exit code and names only the commit.
5. The real `.githooks/pre-push` hook against a local bare remote blocks the bad push and allows the
   good one.
6. The mutation proof gains message mutations (message scanning disabled; message value leaked into
   output), and every mutation is killed.
7. The read-only scan of `main` history reports 0 message findings, and `privacy scan` stays green on
   this pull request with name and trigger unchanged.
8. `README.md` lists commit messages as covered and still lists tag identity and GitHub-created
   merge commits as not covered.
9. The chain closes as `shipped` through an artifact-only pull request.

## Decisions to confirm

1. **Allow the vendor bot address as one exact value (recommended).** It goes into `allowed_exact`,
   the same way the GitHub web-flow address did. Rejected alternatives: allowing every `noreply@`
   local part (any domain could then pass, including a company's internal relay), and rewriting
   history to drop the trailers (published history, and the trailers are accurate attribution).
2. **Scan the whole message, trailers included, with the same rules.** Trailer emails get the same
   allowlist as identity emails, so a `Co-authored-by:` naming a personal mailbox is a finding.
   Treating trailers separately would add a second classification path for no measured benefit.
3. **Strict UTF-8 for messages, fail closed.** This matches the identity fields. A commit that sets a
   legacy `encoding` header blocks and is reported by commit id only; the author re-commits.
4. **No new script and no new CI step.** Message scanning runs inside the existing `--pre-push` and
   `--commit-range` paths, so the CI step added for identities covers messages too.

---
Gate: product owner accepts. The accepting commit is the record.
