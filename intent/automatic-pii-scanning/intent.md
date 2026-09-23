# Intent: detect sensitive data before it reaches the public repository

- **Slug:** automatic-pii-scanning
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending
- **Date:** 2026-09-23
- **Status:** draft
- **Issue:** https://github.com/timwukp/ai-native-sdlc/issues/6

## Problem

This is a public repository, but it has no active Git hook, Kiro hook, KiroCrew hook, or CI check
that detects PII or credential-shaped data before publication. The repository's new PR protection
requires portal verification and the SDLC gate, but neither check is a privacy scanner.

A manual scan before PR #5 found no developer-home paths, host usernames, private keys, access
tokens, passwords, or new private identity data. That result covered one branch once. It does not
protect the next agent edit, terminal push, or pull request, and it cannot be cited as an automatic
control.

A privacy scanner also creates its own disclosure risk: a naive finding that prints the matching
email, token, phone number, or card-shaped value copies the sensitive data into public Actions logs.
A useful control must detect a high-confidence category without reproducing the value it protects.

## Desired outcome

One deterministic scanner supplies three layers:

1. fast feedback when an agent writes a high-confidence sensitive value;
2. an opt-in pre-push check for a human terminal;
3. a fail-closed, unfiltered pull-request check required by branch protection.

Every layer uses the same rules and reviewed allowlist. A finding reports category and repository
path, but never the matched value. The documentation states what is detected, what is deliberately
not inferred, which platforms are supported, and why a clean result is not proof that a repository
contains no PII.

## Affected users / systems

- The owner and any future contributor preparing a public change.
- Agents writing files through Kiro-compatible write tools.
- Human terminal users pushing Git commits.
- GitHub Actions, pull requests, required status checks, and public workflow logs.
- Existing public artifacts that contain approved identities and documentation examples.
- Future PR 1–4 portal optimization work, which should inherit the scanner once this chain ships.

## Constraints

- This is a separate PR 0.5. It must not modify responsive UI, diagrams, teaching modes, Playbook
  content, or the rendered portal.
- Never print, upload, hash into a diagnostic, or otherwise reproduce the matched sensitive value.
  Findings expose only category, repository-relative path, line number, and remediation.
- The CI workflow uses an unfiltered `pull_request` trigger. It must not use `paths:` or
  `branches:` conditions after becoming a required check.
- The CI scanner fails closed on findings, malformed configuration, or an unreadable tracked text
  file. A local write-time hook fails open on infrastructure errors so a broken hook cannot disable
  editing; CI remains the backstop.
- Repository-local Git hook files are not active merely because they are committed. Installation,
  `core.hooksPath`, and a real invocation must be verified before claiming terminal protection.
- Binary files are identified and skipped explicitly, with a count; decoding failures must not be
  silently treated as clean text.
- An allowlist is narrow, reviewable, reasoned, and limited to exact values or anchored patterns.
  A broad path exclusion is not an acceptable way to make findings disappear.
- Public GitHub noreply identities and reserved documentation domains such as `example.com` may be
  allowlisted. Live personal contact details must not be added merely to test the scanner.
- Names and ordinary prose are not automatically classified as PII. That judgement is contextual
  and remains a human review responsibility.
- A clean scan means only that the declared high-confidence rules found nothing. It must not be
  described as privacy certification, compliance, or proof that no PII exists.
- The scanner and its tests remain lightweight and runnable without a portal build step.
- The agent does not push, self-approve artifacts, merge, or weaken branch protection.

## Success criteria

1. A checked-in deterministic scanner has one documented command and exits non-zero on a finding
   or invalid configuration.
2. Tests are committed and observed failing before implementation, then cover every supported
   detection category, allowlist behavior, text/binary handling, and exit-code contract.
3. High-confidence coverage includes developer-home/host markers, email addresses, labeled phone
   numbers, Luhn-valid payment-card-shaped values, private-key headers, bearer tokens, and selected
   provider credential formats.
4. Public GitHub noreply addresses, reserved example domains, and explicitly reviewed repository
   identities do not create false positives.
5. Test fixtures use unmistakably synthetic values. No real-looking secret is printed in test or
   Actions output, including on failure.
6. Every finding redacts the matched value while preserving enough location and category data to
   remediate it.
7. A repository-local Kiro write-time hook invokes the shared scanner for supported write/edit
   payloads, blocks a positive finding with exit 2, and allows on infrastructure failure with an
   explicit warning.
8. A checked-in terminal pre-push hook or installer invokes the same scanner, documents platform
   support, and is exercised from its installed location before being described as functional.
9. An unfiltered GitHub Actions workflow exposes one stable `privacy scan` check, uses read-only
   permissions and no secret, and fails closed on scanner findings.
10. The portal verifier checks the scanner, hook configuration, CI workflow shape, stable context,
    redaction guarantee, and documentation claims so the control cannot silently disappear.
11. A real pull request first demonstrates a blocked synthetic finding in a safe test fixture or
    negative-control path, then passes after the intended implementation is present without
    publishing the sensitive fixture value.
12. After merge, branch protection requires the exact `privacy scan` context observed from the
    check-run API, and a read-only API query confirms it alongside the existing two checks.
13. The README explains local installation/use, CI behavior, supported categories, allowlist review,
    and permanent false-negative/false-positive limits.
14. The chain is closed as `shipped` through an artifact-only pull request before responsive PR 1
    begins.

## Open questions

1. **Secret detection dependency.** Use only the standard-library scanner in PR 0.5, or add a pinned
   third-party scanner such as Gitleaks for broader credential coverage? Recommendation: keep the
   shared PII rules standard-library-only and evaluate a pinned specialist secret scanner as a
   separately owned dependency rather than pretending a few regexes equal mature secret scanning.
2. **Terminal platforms.** Must the pre-push hook support Windows immediately, or may it be honestly
   POSIX-only while CI remains cross-platform? Recommendation: POSIX-only first, explicitly labeled;
   do not claim Windows support without a native exercised path.
3. **Initial allowlist.** Which identities may be public? Recommendation: reserved example domains,
   GitHub noreply addresses, and the existing public owner name only; no phone number or personal
   mailbox.
4. **CI scan scope.** Scan only the PR diff or the complete tracked tree? Recommendation: scan the
   complete small tracked tree in CI so moving an existing value does not hide it; use changed data
   locally for speed. History scanning and removal from already-published commits remain a separate
   remediation problem.

---
Gate: product owner accepts. The accepting commit is the record.
