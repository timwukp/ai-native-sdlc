# AI-Native SDLC — a training portal

**Read it here: <https://timwukp.github.io/ai-native-sdlc/>**

One page, nothing to install, works offline once loaded. Written to be worked through in one
sitting.

A training site for the AI-native software development lifecycle: six stages, one committed
artifact per stage, and stage gates that are enforceable rather than aspirational.

**This is not the skill's source repository.** The `ai-native-sdlc` skill — its gate scripts,
templates, hooks, CI gate and reference docs — lives in
[agent-skills-best-practice](https://github.com/timwukp/agent-skills-best-practice/tree/main/skills/skills/ai-native-sdlc).
This repository holds a study guide *about* it. The two share a name, which is why this paragraph
exists.

Independent, and not affiliated with or endorsed by Anthropic.

## What you will learn

Work through the page once and you should be able to:

- **run one change through the loop** — `intent.md` → `spec.md` → `plan.md` → diff + tests →
  PR review → control bands — and name the artifact and the gate at each stage;
- **tell the three enforcement strengths apart** — advisory skill, fail-open write-time hook,
  fail-closed required check — and say why a green-or-red check is not a gate until branch
  protection makes it one;
- **recognise the four traps before paying for them**: a skipped required check that reads as
  passing, an approval bound to no base, a merged chain left `accepted` that launders the next
  change, and a weak eval that passes while the feature is broken. Each was a real defect in
  the reference implementation's history, not a hypothetical;
- **state honestly where this is and is not adoptable** — the reference implementation scores
  itself 36/80 against an enterprise control rubric, and the page explains why publishing that
  number is the point rather than a confession.

The page ends with a **hands-on lab**: install the write-time hook (Kiro or Claude Code) and
the CI gate into a scratch repository, then let the gate refuse you a few times on purpose.
A self-check at the end tells you whether it stuck.

## Sources

The portal is a study guide over two primary sources, both linked from the page:

- [The AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) — Anthropic,
  21 August 2026, by Louis Claxton. The framework: stages, shifts, governance, metrics.
- The [`ai-native-sdlc` skill](https://github.com/timwukp/agent-skills-best-practice/tree/main/skills/skills/ai-native-sdlc)
  — the enforceable implementation: artifact templates, a write-time `PreToolUse` hook for Kiro
  and Claude Code, a CI merge gate, and reference docs on enforcement and limitations.

## How this site was built

Through the lifecycle it teaches. `intent/` holds the committed chain: an accepted `intent.md`, a
signed-off `spec.md`, an accepted `plan.md` bound to the commit its approval covered, a red
verification target committed before the page existed, and then the implementation. The history
is meant to be read as a worked example, including the places where the plan had to be amended
and re-accepted.

One thing stated plainly because the process cares about it: a prototype of this page was written
*before* the intent existed, and was deliberately kept out of this repository as an unreviewed
draft rather than committed on the strength of already existing.

## Layout

```
index.html   the entire site: markup, CSS and JS inline, no dependencies
verify.py    the verification target — run it before committing a change
intent/      the artifact chain this site was built through
.sdlc/       which intent is active, and the artifact schema version
```

## Verify it locally

```sh
python3 verify.py
```

Standard library only, no install step. It exits non-zero on failure and prints the number of
checks it performed, so a verification that silently checks nothing is visible rather than
reported as success. Four groups:

- **structure** — landmarks, exactly one `h1`, a skip link that resolves, and the full ARIA tab
  pattern (six tabs, six panels, `aria-controls` resolving, one selected tab, roving `tabindex`);
- **isolation** — no external asset and no network call, so the page works opened from `file://`;
- **content** — every claim the spec requires, asserted against *extracted text* rather than raw
  markup, so a comment or an attribute cannot satisfy a requirement;
- **honesty** — a forbidden-phrase list, because a training page fails by overclaiming rather
  than by crashing.

Open `index.html` directly in a browser to preview; there is nothing to serve or build.

## What is checked by hand

`verify.py` cannot judge these, so they are done manually and recorded in the commit that
changes them:

- keyboard-only traversal of every control, with visible focus throughout;
- the page with JavaScript disabled — all six stage panels must remain readable, which holds
  because the panels ship without `hidden` and only the script applies it;
- contrast of the actual colour pairs used (measured, not estimated).

## Contributing changes

Every portal revision goes through a pull request before GitHub Pages changes. Start a fresh
artifact chain, make sure its accepted plan names every source file the change touches, and run:

```sh
python3 verify.py
```

Paste the actual check count and result into the pull request. Visual changes also carry viewport,
keyboard-only and JavaScript-disabled evidence using the pull-request template.

A workflow check is not a gate until branch protection marks it required. This repository requires
the portal verifier and SDLC gate on `main`, applies those checks to the owner, and requires the
branch to be up to date. That prevents accidental bypass during ordinary work; it is not an
unbypassable enterprise control, because a personal-repository owner can still edit or remove the
protection rule. [Issue #4](https://github.com/timwukp/ai-native-sdlc/issues/4) is the bootstrap
record for these controls.

## Privacy guardrails

The repository carries one deterministic scanner for high-confidence sensitive data. Run the full
tracked-tree check locally with:

```sh
python3 scripts/privacy_scan.py --repo .
```

It checks developer-home and configured machine markers, email addresses, explicitly labelled phone
numbers, Luhn-valid payment-card-shaped values, private-key headers, bearer credentials, and selected
AWS, GitHub and Slack credential prefixes. The scanner reports category, repository-relative path and
line number, but **never prints the matched value** or its hash.

The Kiro write-time hook **fails open** on infrastructure errors so a broken local hook cannot stop
all editing. The pull-request `privacy scan` check **fails closed** and is the binding backstop. The
human-terminal pre-push hook is POSIX-only and opt-in; install it for this repository with:

```sh
sh scripts/install_privacy_hooks.sh
git config --local --get core.hooksPath   # must print .githooks
```

A committed Git hook is not active until that installer succeeds. The installer refuses to replace
another `core.hooksPath` or an existing pre-push hook. A user can bypass a Git hook with
`--no-verify`, and CI cannot prevent a sensitive value reaching a public feature branch before CI
starts; review findings and rotate/remove real credentials immediately.

The narrow allowlist in `.privacy-allowlist.json` is reviewed like code. It permits public/example
values only and cannot skip a path or category. This scanner does not infer names or free-form prose,
and a clean result **does not prove the repository contains no PII**. Its selected credential
patterns are **not a replacement for a specialist secret scanner** such as Gitleaks, and the feature
is not privacy certification or a compliance control.

## How it publishes

GitHub Pages serves this repository from branch `main`, path `/`, so `index.html` must stay at
the repository root. There is no build step: a pull request is verified and merged to `main`, then
<https://timwukp.github.io/ai-native-sdlc/> is updated from that branch.

## Licence

The prose and code here are original. The two sources are cited and linked, not reproduced.
