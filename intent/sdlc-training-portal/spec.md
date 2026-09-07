# Spec: a training portal that teaches the AI-native SDLC by enforcing it

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Open questions from the intent, now closed

**Q1 — repository name.** Closed by Amendment 1: `ai-native-sdlc`, published at
`https://timwukp.github.io/ai-native-sdlc/`.

**Q2 — who creates the repository and enables Pages?** The owner. Both are account-level actions
on the owner's GitHub account, and the existing rule that the agent does not push branches
applies with more force to creating a public repository. The agent prepares the content and the
exact commands; the owner runs them. Consequence for verification: no success criterion may
depend on the live URL responding, because that is outside this change's control. Criteria are
therefore written against the built artifact, with the live URL confirmed by the owner after
publication.

**Q3 — single page or multi-page?** Single page, `index.html` at the repository root. It is
required anyway by the Pages configuration (branch `main`, path `/`), it is linkable and
printable in one piece, and there is no navigation to keep in sync. If the content outgrows it,
splitting later costs one redirect, not a rewrite.

**Q4 — does the quiz ship, given the no-JavaScript requirement?** Yes, as a progressive
enhancement. The rule is that the quiz is *absent* rather than *broken* without JavaScript: its
container is empty in the markup and populated by script, so a no-JS reader sees the section
heading and an explanatory line rather than dead buttons. No other content may be
script-populated.

## Requirements

### Structure and delivery

1. **One file, no build, no dependencies.** The deliverable is `index.html` at the repository
   root, with CSS and JavaScript inline. No framework, no external font, script, stylesheet,
   image, or analytics. The page must render correctly opened from `file://`.
2. **Zero external network requests** at runtime. This is verifiable statically: the built file
   must contain no `http://` or `https://` reference in a `src`, `href` to a stylesheet, or
   `fetch`/`XMLHttpRequest` call. Outbound *hyperlinks* to the two sources are expected and are
   not requests.
3. **Pages-compatible.** Nothing that requires a Jekyll build or a `.nojekyll` exemption; a
   plain static file served from the branch root.

### Content — what must be taught

4. **All six stages**, each stating: the shift from traditional practice, the artifact it
   commits, the gate and who holds it, and how the stage is measured.
5. **The loop, not a line.** The artifact chain must be shown with Stage 6 writing a new
   `intent.md` that re-enters Stage 1.
6. **The three enforcement strengths** — advisory skill, write-time hook that fails *open*,
   merge gate that fails *closed* — with the explicit statement that a check which is not marked
   *required* in branch protection is not a gate.
7. **At least four named traps**, each with its mechanism and its consequence:
   - a skipped required check reads as passing;
   - an approval with no recorded base outlives the change it approved;
   - a merged chain left `accepted` authorises the next unrelated change;
   - an eval can pass while the feature is broken (the weak-eval hole).
8. **A hands-on lab** taking a reader from installing the two enforcement layers to closing a
   chain as `shipped`, including the one step only a human can do (marking the check required)
   and the merge-base binding for `Accepted-for`.
9. **At least one exercise per trap** that makes the failure observable rather than described.

### Content — honesty

10. **The four adoption positions** stated with the two unmet ones marked not achieved, plus
    **36/80 (45%)** and the **~48%** standalone ceiling.
11. **The three enterprise-owned controls** named — organisation policy plane, external
    tamper-evident audit sink, independent assurance — each stated as not provided by the skill.
12. **No overclaim.** The page must not describe the skill as enterprise-ready, compliant,
    independently audited, or production-proven at scale. Synthetic CI coverage must be labelled
    synthetic; self-authored tests must be stated not to be independent assurance.
13. **Attribution and independence.** The playbook credited to Louis Claxton, published by
    Anthropic/Claude, 21 August 2026, with a link; the skill linked at its actual location. A
    statement that the portal is independent and not endorsed by Anthropic.
14. **Disambiguation (Intent SC10).** Because the repository name is identical to the skill's
    name, the page must state that it is a training site *about* the skill and is not the skill's
    source repository, and link to where the skill lives. This must be visible without
    scrolling to the footer.

### Accessibility

15. **Semantic markup**: one `h1`, ordered heading levels, `main`/`section`/`nav`/`footer`
    landmarks, a skip link, `lang` set, and tables with real `th` scope.
16. **Keyboard operable.** Every interactive element reachable and operable by keyboard alone.
    The stage selector must implement the tab pattern: `role="tablist"`/`tab`/`tabpanel`,
    `aria-selected`, roving `tabindex`, and Left/Right/Home/End keys.
17. **Visible focus** on every focusable element, not suppressed.
18. **Contrast** of at least 4.5:1 for body text and 3:1 for large text, against the actual
    background used.
19. **No content behind JavaScript** except the quiz (Q4). With scripting disabled, all six
    stage panels' content must remain readable.

### Verification

20. **A checked-in verification target.** `python3 verify.py` must exit non-zero on failure and
    check, at minimum: the file exists and parses as HTML; no external asset reference; exactly
    one `h1`; a skip link; the tab pattern's required attributes present on every tab and panel;
    every required content marker present (six stages, the four traps, the four adoption
    positions, 36/80, 45%, 48%, the three enterprise-owned controls, both attributions, the
    disambiguation statement); and no forbidden overclaim phrase.
21. **Red first.** `verify.py` must be committed and observed failing before `index.html` exists,
    for the reasons above rather than as a crash.
22. **Stdlib only** for the verification target: `html.parser`, `re`, `pathlib`. No dependency,
    because a training repository that needs `pip install` to check itself teaches the wrong
    lesson.

### Process

23. **Dogfood chain.** `.sdlc/active` names `sdlc-training-portal`; the artifact chain stays
    committed; no artifact this agent authored is set to `accepted`/`signed-off` by the agent.
24. **The pre-process prototype is a draft.** Material may be reused from it, but every reused
    part must satisfy a requirement above, and it must not be committed wholesale. It is not
    evidence of review.

## Non-functional requirements

- **Readability.** Prose written for a practitioner, not marketing copy. No claim without a
  mechanism.
- **Print.** The page should print legibly: no fixed-position overlay, and stage panels' content
  should not be permanently hidden in print. Best-effort, not a hard criterion.
- **Weight.** Target under 100 KB total for the single file.
- **Longevity.** Only figures that come from the sources; no dated claim that will silently rot
  (no "currently", no version numbers that move).

## Design

### 1. Page order

Hero → why the lifecycle changes → the loop and its artifacts → the six stages (tabbed) →
enforcement strengths and the three failure modes → hands-on lab with exercises → honest limits →
self-check → sources. The honest-limits section sits *before* the self-check so a reader reaches
it even if they stop early, and the disambiguation line sits in the hero, not the footer.

### 2. The stage selector

A tablist of six buttons over six panels. All panel markup is present in the document; the script
only toggles `hidden` and the ARIA state. With scripting off, `hidden` is never applied, so every
panel renders stacked — which satisfies requirement 19 by construction rather than by a
fallback.

### 3. The quiz

An empty `<div id="quiz">` plus a `<noscript>` line explaining that the self-check needs
scripting. Questions are built by script. Each question reveals the correct option and an
explanation; the explanation is the teaching, so it states the mechanism rather than "correct".

### 4. The verification target

`verify.py` parses `index.html` with `html.parser` and asserts:

- structure: one `h1`, `lang`, skip link, landmarks, `role` attributes on tabs/panels, matching
  `aria-controls`/`id` pairs, and a roving `tabindex`;
- isolation: no `src`/stylesheet `href`/`fetch(`/`XMLHttpRequest` pointing outside the file;
- content: required markers as literal or regex probes, checked against the text content rather
  than raw markup so an HTML comment cannot satisfy one;
- honesty: a forbidden-phrase list.

Content probes assert *semantic* markers rather than whole sentences, so editorial improvement
is not blocked while a missing claim still fails.

### 5. Rejected alternatives

- **A static-site generator or framework — rejected.** Requirement 1; a build step is exactly the
  friction that stops a reader running the thing.
- **Multi-page with a nav — rejected for the first release.** Q3.
- **Committing the pre-process prototype and back-filling artifacts — rejected.** It would make
  the portal's own history a counter-example of the process it teaches.
- **Gating stage content behind the tab script — rejected.** Requirement 19; the fix is to ship
  all panels in the markup.
- **A CI job that fetches the live URL — rejected.** Publication is the owner's action; a check
  that depends on it would fail for reasons this change cannot control.
- **Softening the honest limits for a training audience — rejected.** The limits are the most
  useful thing the portal can teach; a reader who adopts this as a compliance control on the
  strength of a friendly page has been actively misled.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| The repo name implies this is the skill's source | Owner | Requirement 14: disambiguation visible in the hero, with a link to the real location. |
| A page about governance could itself be unverified | Skill maintainer | Requirements 20–22: a stdlib verification target, committed red first. |
| Reusing the unreviewed prototype could smuggle in unreviewed claims | Owner | Requirement 24: every reused part must satisfy a stated requirement. |
| Honest limits could be read as disparaging the sources | Owner | State them as the sources state them, with attribution; the skill's own docs are the origin of every figure. |
| A quiz could imply certification | Owner | Label it a self-check; no scoring claim, no badge, no completion record. |

## Out of scope

- Creating the repository, pushing it, or enabling Pages (owner actions, Q2).
- A custom domain, favicon set, social preview image, or analytics.
- Translations.
- Any change to the `ai-native-sdlc` skill or to `agent-skills-best-practice`.
- Video, downloadable slides, or an exercise repository to clone.
- Claiming the portal has been reviewed by anyone other than its author until that is true.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` as installed at `/home/ec2-user/.kiro/skills/ai-native-sdlc`, matching
`agent-skills-best-practice` main at commit 3a343d5d55b8af60d17e033568f1a7908722cb3d.
