# AI-Native SDLC — a training portal

A single-page training site for the AI-native software development lifecycle: six stages, one
committed artifact per stage, and stage gates that are enforceable rather than aspirational.

**This is not the skill's source repository.** The `ai-native-sdlc` skill — its gate scripts,
templates, hook, CI gate and reference docs — lives in
[agent-skills-best-practice](https://github.com/timwukp/agent-skills-best-practice/tree/main/skills/skills/ai-native-sdlc).
This repository holds a study guide *about* it. The two share a name, which is why this paragraph
exists.

Independent, and not affiliated with or endorsed by Anthropic.

## Sources

The portal is a study guide over two primary sources, both linked from the page:

- [The AI-Native SDLC playbook](https://claude.com/blog/the-ai-native-sdlc-playbook) — Anthropic,
  21 August 2026, by Louis Claxton. The framework: stages, shifts, governance, metrics.
- The [`ai-native-sdlc` skill](https://github.com/timwukp/agent-skills-best-practice/tree/main/skills/skills/ai-native-sdlc)
  — the enforceable implementation.

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

## How it publishes

GitHub Pages serves this repository from branch `main`, path `/`, so `index.html` must stay at
the repository root. There is no build step and no workflow — a push to `main` is the deploy.

## How this site was built

Through the lifecycle it teaches. `intent/` holds the committed chain: an accepted `intent.md`, a
signed-off `spec.md`, an accepted `plan.md` bound to the commit its approval covered, a red
verification target committed before the page existed, and then the implementation. The history
is meant to be read as a worked example, including the places where the plan had to be amended
and re-accepted.

One thing stated plainly because the process cares about it: a prototype of this page was written
*before* the intent existed, and was deliberately kept out of this repository as an unreviewed
draft rather than committed on the strength of already existing.

## Licence

The prose and code here are original. The two sources are cited and linked, not reproduced.
