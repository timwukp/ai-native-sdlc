# Intent: a training portal that teaches the AI-native SDLC by enforcing it

- **Slug:** loopsmith-training-portal
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** accepted

## Problem

The AI-native SDLC is documented in two places that serve different needs and neither works
as training material on its own:

- The **playbook** (Anthropic/Claude, 21 Aug 2026) explains the *why* and *what*: six stages,
  the traditional-versus-AI-native shift per stage, and each play's prerequisites, governance
  considerations and metrics. It is long-form prose, vendor-framed, and stops short of a
  runnable control.
- The **`ai-native-sdlc` skill** provides the *how*: artifact templates, a stage gate, a
  `PreToolUse` hook, a CI gate, and reference docs. It is written for an agent to execute, not
  for a person to learn from, and its honest-limits material is spread across four files.

Someone who wants to adopt this has to read both, hold the mapping between them in their
head, and discover the traps by hitting them. The traps are the expensive part: a skipped
required check reads as passing, an approval with no recorded base outlives its change, a
merged chain left `accepted` launders the next change, and an eval can pass while the feature
is broken. Each of those was a real defect, not a hypothetical.

There is also no honest, consolidated statement of where this is safe to adopt. The skill
scores itself at 36/80 (45%) against an enterprise control rubric, with roughly 48% the
ceiling a standalone repository can reach — but a reader arriving from the playbook has no
reason to know that, and could reasonably mistake a documented process for a compliance
control.

## Desired outcome

A public training portal that a practitioner can work through in one sitting and come away
able to run one change through the loop, name the artifact and gate at each stage, and state
correctly where this is and is not adoptable. It must teach the traps explicitly rather than
leaving them to be discovered, and it must state the honest limits in the same voice as the
source material rather than softening them.

The portal is itself built through this lifecycle, so its own commit history is a worked
example of the process it teaches.

## Affected users / systems

- **Primary audience:** engineers and platform engineers evaluating or adopting the process.
- **Secondary:** product owners and tech leads who own the gates (Stage 1/2 acceptance,
  `REVIEW.md`, branch protection) and need to know what they are signing.
- A new public repository, published as a GitHub Pages project site.
- No change to the `ai-native-sdlc` skill or to `agent-skills-best-practice`. This is a new,
  separate deliverable that cites them.

## Constraints

- **Deployment shape is fixed by the target URL.** A project site at
  `https://timwukp.github.io/<repo>/` requires a repository of that name serving Pages from
  branch `main`, path `/`, with `index.html` at the repository root — the same configuration
  the existing `Kiro-Crew-Training` site uses (verified).
- **Static and dependency-free.** No build step, no framework, no third-party runtime asset.
  A single page must render correctly from `file://` and from Pages with nothing installed.
- **Accessible.** Semantic markup, keyboard-operable interactive elements, visible focus,
  adequate contrast, and no interaction that is mouse-only.
- **Truthful.** No claim may exceed the sources. The four adoption positions, the 36/80 score,
  the ~48% ceiling, and the three enterprise-owned controls must appear unsoftened. Synthetic
  test coverage must not be presented as production evidence, and self-authored tests must not
  be presented as independent assurance.
- **Attribution and independence.** The playbook must be credited to its author and publisher;
  the portal must state it is independent and not endorsed by Anthropic, and must not imply
  affiliation.
- **No secrets, no analytics, no third-party tracking.** Nothing that phones home.
- **Process.** This change follows the skill's own lifecycle: no implementation before an
  accepted plan, and no artifact self-approved by its author.

## Prior art to be treated as a draft, not as work product

A 752-line single-page prototype was written **before** this intent existed, and is kept
outside the repository at a scratch path as reference only. It was not produced by this
process and carries no review. The plan may reuse material from it, but it must be treated as
an unreviewed draft: anything adopted from it has to be justified against the spec like new
work. It must not be committed as-is on the strength of already existing.

## Success criteria

1. The portal is reachable at a project-site URL of the agreed shape and renders with no
   console errors and no external network requests.
2. It covers all six stages, and for each one states: the shift from traditional practice, the
   artifact committed, the gate and who holds it, and how the stage is measured.
3. It presents the artifact chain as a loop, showing that Stage 6 writes a new `intent.md`.
4. It explains the three enforcement strengths (advisory skill, write-time hook that fails
   open, merge gate that fails closed) and states that an unmarked required check is not a
   gate.
5. It teaches at least four named traps, each with the mechanism and the consequence, and at
   least one exercise per trap that makes the failure observable.
6. It contains a hands-on lab that takes a reader from installing the enforcement layers to
   closing a chain as `shipped`.
7. It states all four adoption positions with the two unmet ones marked not achieved, the
   36/80 (45%) score, and the ~48% standalone ceiling.
8. It names the three enterprise-owned controls and says plainly that the skill does not
   provide them.
9. It credits both sources and states its own independence.
10. Interactive elements are operable by keyboard alone, and the page is usable with
    JavaScript disabled (content must not be JS-gated).
11. The portal's own repository carries the committed artifact chain for this slug, with
    acceptance and sign-off in separate human commits.

## Open questions

1. **Repository name, which fixes the URL.** Proposed `Loopsmith`, giving
   `https://timwukp.github.io/Loopsmith/`. No such repository exists today. The owner decides;
   the name cannot change after publication without breaking links.
2. **Who creates the repository and enables Pages?** Both are owner actions on the owner's
   account. Proposed: the agent prepares the content and the owner creates the repository,
   pushes, and enables Pages — consistent with the existing rule that the agent does not push
   feature branches.
3. **Single page or multi-page?** Proposed single page for the first release: it is linkable,
   printable, and has no navigation to maintain. Multi-page can follow if the content outgrows
   it.
4. **Does a self-check quiz belong in the first release,** given criterion 10 requires the page
   to work without JavaScript? Proposed: yes, as a progressive enhancement that is absent
   rather than broken when JS is off. To be settled in design.
