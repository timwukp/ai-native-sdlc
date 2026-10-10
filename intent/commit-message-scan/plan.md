# Plan: check commit messages and trailers in the shared privacy scanner

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 2e22706b2fb6cdfeb098f9e3f6ac1132d0e920a3
- **Status:** accepted

`Accepted-for` is `git merge-base origin/main HEAD` at plan draft time, the value the CI gate
compares. It is also the current `origin/main`, after the stage-plays-link-names closeout.

## Files changed (in order of work)

1. `.sdlc/active`: already points at `commit-message-scan`.
2. `intent/commit-message-scan/intent.md`, `spec.md`, `plan.md`: this chain (Issue #20, messages).
3. `scripts/test_privacy_scan.py`: red-first message unit tests (spec 11, 12).
4. `scripts/test_privacy_pre_push.py`: red-first real-hook trailer case (spec 13).
5. `scripts/privacy_mutation_proof.py`: three anchored message mutations (spec 14).
6. `verify.py`: red-first README checks in `privacy_checks()` (spec 15).
7. `scripts/privacy_scan.py`: message reading, rules, output and summary line (spec 1-9).
8. `.privacy-allowlist.json`: one exact vendor bot value (spec 5).
9. `README.md`: three surfaces, the shorter not-covered line, the allowlist reason (spec 16).

Explicitly unchanged: `index.html`, `plays.html`, `.githooks/pre-push`, every workflow under
`.github/`, `scripts/install_privacy_hooks.sh`, the Kiro write-time hook and its config, the SDLC
gate, branch protection and every shipped chain. No new script, no new CLI flag, no second
allowlist.

## Work order

### A. Accept the plan and commit the red contract

1. Record acceptance in this file in its own commit. Nothing below is edited before it.
2. Add message unit tests to `scripts/test_privacy_scan.py`, reusing the throwaway-repository
   helpers the identity tests already use (empty `GIT_CONFIG_GLOBAL` / `GIT_CONFIG_SYSTEM`,
   identity through `GIT_AUTHOR_*` / `GIT_COMMITTER_*`, noreply identities so only the message can
   fail). Messages are passed with `git commit -F` from a file the test writes. Synthetic values
   are built at runtime with `chr(64)`. The allowlisted-trailer case reads the vendor value from
   `.privacy-allowlist.json` as the entry that is neither the web-flow address nor `Tim WU`, so no
   test literal names it. Cases are the spec 12 list exactly; the two encoding cases write the
   object with `git hash-object -t commit --literally -w` and point a branch at it.
3. Update the two existing summary assertions to the spec 8 wording.
4. Add the real-hook trailer case to `scripts/test_privacy_pre_push.py`: a commit whose only
   problem is a `Co-authored-by:` trailer is refused and the remote ref stays absent; the same
   commit with a noreply trailer is accepted.
5. Add three mutations to `METADATA_MUTATIONS` in `scripts/privacy_mutation_proof.py`, each an
   exact-once anchored replacement in the scanner source, run against `scripts/test_privacy_scan.py`:
   - `message_check_disabled`: the line that adds message findings becomes `pass`;
   - `message_trailers_dropped`: the text handed to `scan_text` becomes
     `message.rsplit("\n\n", 1)[0]`, so the final paragraph (where Git trailers live) is skipped;
   - `message_line_leaked`: the field label passed to the message finding has the line's text
     appended.

   An anchor that does not match exactly once reports `broken`, as today.
6. In `verify.py` `privacy_checks()`, replace the "uncovered commit messages" check with: the
   README lists commit messages and trailers as a covered surface; the not-covered line still names
   annotated-tag tagger identity and merge commits GitHub creates on `main`; the allowlist
   paragraph gives the vendor-address reason.
7. Run and record the red state, then commit: existing privacy tests still pass except the two
   summary assertions, and only new or updated tests fail; the mutation proof's control run passes
   and the three new mutations report `broken` (their anchors do not exist yet); `verify.py` fails
   only the new named checks with no traceback, and the other 385 stay green.

### B. Implement the scanner

8. Add `MetadataFinding.line: Optional[int] = None`. Render ` line=<n>` after `field=` only when
   it is set, so identity findings stay byte-for-byte the same.
9. Add `_commit_message(repo, sha)`: read `git cat-file commit` once (shared with
   `_commit_identity` through one helper, so each commit object is fetched once), take the bytes
   after the first blank line, reject a header `encoding` other than UTF-8 and any undecodable
   bytes with `ScanError` naming the 12-character id only.
10. Add `_message_findings(short, message, config)`: `scan_text(message, "message", config)`, each
    finding mapped to `MetadataFinding(short, "message", category, remediation, line)`.
11. `scan_commit_identities` (renamed in place to `scan_commits`, callers updated) adds message
    findings for the same deduplicated commit list, so `--pre-push` and `--commit-range` both
    cover messages with no CLI change.
12. Change the summary line to `privacy scan: <N> commits checked (identity and message)`.
13. Add the vendor value to `allowed_exact`, written by a short shell step from the measured value
    so the address is never typed into a reply. All tests turn green.

### C. Documentation

14. Update the README privacy section per spec 16, including the allowlist paragraph's reason.

### D. Prove it locally and commit

15. Portal verifier all green; privacy tests all passing; mutation proof 16 killed, 0 survived,
    0 broken; tracked-tree scan 0 findings.
16. `--commit-range $(git merge-base origin/main HEAD) HEAD` reports 0 findings; the read-only
    check of every `main` message with the new allowlist reports 0 findings; the pre-push hook over
    every unpushed commit reports 0 findings.
17. `git diff --check`, no host paths, and every changed file is on the spec's allowed list.

### E. Draft PR and CI

18. The owner pushes; I open a Draft PR that links Issue #20 without closing it, and wait for
    `portal verify`, `privacy scan` and `sdlc-gate`. The `privacy scan` log must show the new
    summary line for the branch's commits.
19. No portal page changes, so no rendered evidence. With all three checks green on the current
    head, the PR is marked Ready. The owner merges; a separate artifact-only PR marks the chain
    `shipped`.

## Tests that prove it

| Spec | Proof |
| --- | --- |
| 1, 3 | Body, subject and both trailer kinds are read; empty message allowed |
| 2 | `encoding: ISO-8859-1` and invalid UTF-8 objects exit 2, naming only the commit |
| 4 | Non-allowlisted email and home path are findings with their own categories |
| 5 | Noreply and allowlisted vendor trailers pass; `main` history check is 0 |
| 6, 7 | Finding shows the right line; output has no value, domain or line text; leak mutation killed |
| 8 | Updated summary assertions |
| 9 | Earlier-commit case on both paths; real hook refuses the trailer push |
| 14 | Mutation proof 16/16 |
| 15, 16 | `verify.py` README checks |

## Risks

- **Renaming `scan_commit_identities`** touches the identity mutation anchors. Step 11 updates
  them in the same commit, and the proof's `broken` status catches a missed anchor.
- **The trailer-dropped mutation is a heuristic.** It drops the final paragraph, which is where
  Git puts trailers. A test with a trailer in that paragraph kills it; a body-only test alone would
  not, so step 2 keeps each trailer case's trailer as the final paragraph.
- **Mutation proof scope** is unchanged: the real-hook test is not mutation-checked, and each
  message mutation is killed by unit tests.
- **The vendor value lives only in the allowlist.** If it ever changes, the 14 historical
  trailers stay allowed by the old value and a new value is a finding until reviewed.

## Rejected alternatives

- **A trailer parser (`git interpret-trailers --parse`).** It adds a second reading path and
  drops trailer-shaped lines it does not recognise; the whole message is already read.
- **Scanning messages from `git log --format=%B`.** Formatting and encoding conversion sit between
  the object and the check.
- **A `--messages` opt-in flag.** Messages are published on every push; an opt-in would leave CI
  unprotected unless the workflow changed too.

---
Gate: the owner accepts BEFORE tests, `verify.py`, the scanner, the allowlist or the README is
edited. Any departure requires a plan amendment and renewed acceptance.
