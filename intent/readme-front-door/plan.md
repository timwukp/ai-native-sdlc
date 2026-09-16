# Plan: one file, reordered around the reader

- **Spec:** ./spec.md
- **Author:** Claude (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** 57b97d6159802146b5c0fafb4ce47594e7878c42
- **Status:** accepted

`Accepted-for` is `git merge-base origin/main HEAD` at acceptance: `57b97d6`.

## Files changed

1. `README.md` — link-first header; new "What you will learn" section; existing sections
   retained and reordered reader-first (What you will learn, Sources, How this site was
   built, then Layout / Verify / checked-by-hand / publishes / Licence); the publishes
   section now names the URL it deploys to.
2. `.sdlc/active` — points at this slug.
3. `intent/readme-front-door/` — this chain.

Deliberately NOT changed: `index.html`, `verify.py`. Two draft claims were removed during
self-review for keeping the page's own honesty rule: an invented time estimate, and "every
claim links back to its source" (the page deliberately carries only two external links).

## Verification

`python3 verify.py` unchanged-green (128 checks, 0 failed) before and after, since the
README is outside its scope; the requirement-2 correspondence was checked by hand against
the page's section list.
