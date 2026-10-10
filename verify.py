#!/usr/bin/env python3
"""verify.py — the training portal must satisfy its own spec.

A site that teaches "write the verification target first, watch it fail" has no business being
unverified. This is that target for `index.html`, and it was committed and observed failing
before the page existed.

What it checks, in four groups:

  structure  — landmarks, one h1, a working skip link, and the full ARIA tab pattern
  isolation  — no external asset, no network call: the page must work from file://
  content    — every claim the spec requires, asserted against EXTRACTED TEXT rather than raw
               markup, so an HTML comment or an attribute cannot satisfy a requirement
  honesty    — a forbidden-phrase list, because the failure mode of a training page is
               overclaiming rather than crashing

The check count is printed on every run. A verification that silently checks nothing is worse
than none, since it reports success.

Standard library only: a training repository that needs `pip install` to check itself teaches
the wrong lesson.

Exit 0 = all checks pass.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import pathlib
import re
import subprocess
import sys
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"
# Top-level tracked entries the README Layout block must list.
LAYOUT_ENTRIES = ("index.html", "plays.html", "verify.py", "intent/", ".sdlc/", "evals/",
                  "scripts/", ".githooks/", ".privacy-allowlist.json", ".github/", ".kiro/")

FAILURES: list[str] = []
CHECKS = 0

# The learning-mode spec raises the measured responsive page's 75 KB ceiling to 85 KB.
# This remains a hard cap: it authorises the accepted mode UI, not unrelated expansion.
PAGE_BUDGET = 85_000

# Text that must appear somewhere in the rendered text. Semantic markers, not whole sentences,
# so editorial improvement is not blocked while a missing claim still fails.
REQUIRED_TEXT: tuple[tuple[str, str], ...] = (
    # the six stages
    ("stage 1", "Stage 1"), ("stage 2", "Stage 2"), ("stage 3", "Stage 3"),
    ("stage 4", "Stage 4"), ("stage 5", "Stage 5"), ("stage 6", "Stage 6"),
    ("stage name Plan", "Plan"), ("stage name Design", "Design"),
    ("stage name Build", "Build"), ("stage name Test", "Test"),
    ("stage name Deploy", "Deploy"), ("stage name Maintain", "Maintain"),
    # the artifacts
    ("artifact intent.md", "intent.md"), ("artifact spec.md", "spec.md"),
    ("artifact plan.md", "plan.md"), ("artifact evals/", "evals/"),
    ("artifact REVIEW.md", "REVIEW.md"), ("artifact bands.yaml", "bands.yaml"),
    # the four traps
    ("trap: skipped check reads as passing", "skipped"),
    ("trap: unbound approval", "merge base"),
    ("trap: chain left accepted", "shipped"),
    ("trap: weak eval", "display:none"),
    # enforcement
    ("enforcement: fails open", "fails open"),
    ("enforcement: fails closed", "fails closed"),
    ("enforcement: required check", "required"),
    # honest limits
    ("score 36/80", "36/80"),
    ("percentage 45%", "45%"),
    ("ceiling 48%", "48%"),
    ("adoption: usable now", "Usable now"),
    ("adoption: conditional", "Conditional"),
    ("control: policy plane", "policy plane"),
    ("control: audit sink", "audit sink"),
    ("control: independent assurance", "Independent assurance"),
    ("self-authored tests are not independence", "not independence"),
    # attribution
    ("playbook author", "Louis Claxton"),
    ("independence statement", "not affiliated"),
    # disambiguation (spec requirement 14)
    ("disambiguation", "not the skill's source repository"),
    # dual-surface lab (review-follow-ups requirement 1): the hands-on lab must show the
    # write-time hook on BOTH runtimes the skill ships configs for
    ("lab: Kiro hook install path", ".kiro/hooks"),
    ("lab: Claude Code hook install path", ".claude/settings.json"),
    ("lab: Claude Code template name", "claude-code-hooks"),
    # scope declaration (review-follow-ups requirement 2): plays the playbook has and
    # this material deliberately does not cover, declared rather than implied
    ("scope: auto mode declared out of scope", "auto mode"),
    ("scope: recurring security scans declared", "recurring security scans"),
    ("scope: Claude on call declared", "Claude on call"),
    ("scope: legacy onboarding declared", "legacy-system onboarding"),
)

# Phrases whose presence is a failure. The page must not be able to claim these.
FORBIDDEN: tuple[str, ...] = (
    "is enterprise-ready",
    "fully compliant",
    "independently audited",
    "production-proven",
    "guarantees compliance",
    "soc 2",
    "certified",
)

REQUIRED_LINKS: tuple[tuple[str, str], ...] = (
    ("playbook link", "claude.com/blog/the-ai-native-sdlc-playbook"),
    ("skill link", "github.com/timwukp/agent-skills-best-practice"),
)


class Page(HTMLParser):
    """Collect the little bit of structure the checks need. Text excludes script and style."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.text_parts: list[str] = []
        self.hrefs: list[str] = []
        self._suppress = 0
        self.h1_count = 0
        self.lang = ""
        self.has_noscript = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        self.tags.append((tag, a))
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang", "")
        if tag == "h1":
            self.h1_count += 1
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        if tag == "noscript":
            self.has_noscript = True
        if tag in ("script", "style"):
            self._suppress += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._suppress:
            self._suppress -= 1

    def handle_data(self, data: str) -> None:
        if not self._suppress:
            self.text_parts.append(data)

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.text_parts))


def figure_checks(
    html: str, fig_id: str, label: str, compact_svg_px: float, wide_svg_px: float
) -> None:
    """Verify one inline SVG figure at both accepted layout extremes.

    Takes fig_id so a failure names WHICH figure — three copy-pasted blocks would drift as
    the checks grow, and an unattributed effective-font failure tells the reader nothing.
    """
    # Isolate this figure: from its <figure> wrapper to the matching close.
    m = re.search(
        rf'<figure[^>]*id="{re.escape(fig_id)}"[^>]*>(.*?)</figure>', html, re.S
    )
    if not m:
        check(f"{label}: figure {fig_id} is present", False,
              f"no <figure id=\"{fig_id}\"> in index.html")
        return
    fig = m.group(1)

    svg = re.search(r"<svg\b[^>]*>", fig)
    if not svg:
        check(f"{label}: contains an inline <svg>", False, "the figure has no SVG root")
        return
    root = svg.group(0)

    # --- legibility, using the actual compact and wide component content boxes ---
    vb = re.search(r'viewBox="\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*"', root)
    fonts = [float(f) for f in re.findall(r'font-size="([\d.]+)"', fig)]
    if not vb or not fonts:
        check(f"{label}: has a viewBox and sized text", False,
              "cannot compute legibility without both a viewBox width and a font-size")
    else:
        vb_w = float(vb.group(1))
        compact_eff = min(fonts) * compact_svg_px / vb_w
        wide_eff = max(fonts) * wide_svg_px / vb_w
        print(
            f"  ({label}: compact min {compact_eff:.2f}px at {compact_svg_px:.0f}px SVG; "
            f"wide max {wide_eff:.2f}px at {wide_svg_px:.0f}px SVG)"
        )
        check(
            f"{label}: compact effective font >= 12px",
            compact_eff >= 12.0,
            f"min font {min(fonts)} over viewBox {vb_w} renders at {compact_eff:.2f}px",
        )
        check(
            f"{label}: wide effective font <= 18px",
            wide_eff <= 18.0,
            f"max font {max(fonts)} over viewBox {vb_w} renders at {wide_eff:.2f}px",
        )

    # height="auto" is INVALID on <svg> (it expects a length) and threw a console error in
    # every draft. The container controls height via CSS.
    check(f"{label}: no height attribute on the <svg> root",
          "height=" not in root,
          "height on the root is either invalid (auto) or fights the container")

    # --- accessibility ----------------------------------------------------------
    check(f"{label}: role=\"img\"", 'role="img"' in root)
    labelled = re.search(r'aria-labelledby="([^"]+)"', root)
    check(f"{label}: aria-labelledby present", labelled is not None)
    if labelled:
        for ref in labelled.group(1).split():
            check(f"{label}: aria-labelledby target {ref} exists",
                  f'id="{ref}"' in fig,
                  "a dangling reference sends a screen reader to nothing")
    title = re.search(r"<title[^>]*>(.*?)</title>", fig, re.S)
    desc = re.search(r"<desc[^>]*>(.*?)</desc>", fig, re.S)
    check(f"{label}: <title> is non-empty", bool(title and title.group(1).strip()))
    check(f"{label}: <desc> conveys the mechanism (>= 80 chars)",
          bool(desc and len(desc.group(1).strip()) >= 80),
          "a desc that only repeats the title is a dead end for assistive technology")

    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", fig, re.S)
    check(f"{label}: has a <figcaption>", cap is not None)
    if cap and title:
        ct = re.sub(r"<[^>]*>", "", cap.group(1)).strip()
        check(f"{label}: figcaption says something the title does not",
              ct.casefold() != title.group(1).strip().casefold(),
              "the title names the diagram; the caption should say what to take from it")

    # --- id namespacing ---------------------------------------------------------
    ids = re.findall(r'\sid="([^"]+)"', fig)
    stray = [i for i in ids if not i.startswith(f"{fig_id}-")]
    check(f"{label}: every id is prefixed {fig_id}-", not stray, f"unprefixed: {stray}")

    # --- no dependency, no script ----------------------------------------------
    for token, why in (
        ("<script", "a figure must render with scripting disabled"),
        ("<image", "an external raster breaks file:// and the single-file property"),
        ("@import", "an import is a network dependency"),
    ):
        check(f"{label}: no {token}", token not in fig, why)
    check(f"{label}: no inline event handlers",
          re.search(r'\son[a-z]+="', fig) is None,
          "an event handler is script by another name")
    ext = [u for u in re.findall(r'(?:href|src)="([^"]+)"', fig)
           if u.startswith(("http://", "https://", "//"))]
    check(f"{label}: no external reference", not ext, f"found {ext}")


QUIET = False


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILURES.append(name)
    if QUIET:
        return
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")


def checked_text(path: pathlib.Path, label: str) -> str:
    """Read a required governance file, reporting absence as a finding."""
    exists = path.is_file()
    check(f"{label} exists", exists, f"not found: {path.relative_to(HERE)}")
    return path.read_text(encoding="utf-8") if exists else ""


def yaml_mapping_block(text: str, key: str) -> tuple[bool, str]:
    """Return one indentation-bounded YAML mapping block.

    This is intentionally narrower than a YAML parser: the repository stays stdlib-only, and the
    final syntax proof is GitHub accepting and running the workflow. Bounding the block matters
    because `push` may correctly use `branches: [main]` while a required `pull_request` trigger
    must remain unfiltered.
    """
    lines = text.splitlines()
    key_re = re.compile(rf"^(\s*){re.escape(key)}:\s*(?:#.*)?$")
    for i, line in enumerate(lines):
        match = key_re.match(line)
        if not match:
            continue
        indent = len(match.group(1))
        block: list[str] = []
        for child in lines[i + 1:]:
            stripped = child.strip()
            if not stripped or stripped.startswith("#"):
                block.append(child)
                continue
            child_indent = len(child) - len(child.lstrip())
            if child_indent <= indent:
                break
            block.append(child)
        return True, "\n".join(block)
    return False, ""


def unfiltered_pull_request(text: str, label: str) -> None:
    """Require a pull_request trigger with no condition that can suppress a required check."""
    found, block = yaml_mapping_block(text, "pull_request")
    check(f"{label}: pull_request trigger exists", found)
    forbidden = re.findall(
        r"^\s*(branches|branches-ignore|paths|paths-ignore):", block, re.M
    )
    check(
        f"{label}: pull_request trigger is unfiltered",
        found and not forbidden,
        f"forbidden filters: {forbidden}",
    )
    check(
        f"{label}: never uses pull_request_target",
        bool(text) and "pull_request_target" not in text,
        "fork-controlled content must not run with base-repository privileges",
    )


def read_only_permissions(text: str, label: str) -> None:
    """Require exactly one workflow-level permission: contents read."""
    found, block = yaml_mapping_block(text, "permissions")
    entries = re.findall(r"^\s*([A-Za-z_-]+):\s*([^#\s]+)", block, re.M)
    check(
        f"{label}: workflow permissions are contents read only",
        found and entries == [("contents", "read")],
        f"permissions={entries}",
    )
    check(
        f"{label}: no repository secret",
        bool(text) and "secrets." not in text,
        "the two deterministic gates need no credential",
    )


def artifact_status(relative: str) -> str:
    path = HERE / relative
    if not path.is_file():
        return ""
    match = re.search(r"^- \*\*Status:\*\*\s*(\S+)", path.read_text(encoding="utf-8"), re.M)
    return match.group(1) if match else ""


def governance_checks() -> None:
    """Verify the repository controls that make the portal's own contribution path honest."""
    portal = checked_text(
        HERE / ".github/workflows/portal-verify.yml", "portal verification workflow"
    )
    sdlc = checked_text(HERE / ".github/workflows/sdlc-gate.yml", "SDLC caller workflow")
    template = checked_text(
        HERE / ".github/pull_request_template.md", "pull-request evidence template"
    )
    readme = checked_text(HERE / "README.md", "README")

    unfiltered_pull_request(portal, "portal workflow")
    read_only_permissions(portal, "portal workflow")
    push_found, push_block = yaml_mapping_block(portal, "push")
    check("portal workflow: main push trigger exists",
          push_found and bool(re.search(r"branches:\s*\[main\]", push_block)))
    dispatch_found, _ = yaml_mapping_block(portal, "workflow_dispatch")
    check("portal workflow: manual trigger exists", dispatch_found)
    check(
        "portal workflow: stable check name",
        bool(re.search(r"^\s{4}name:\s*portal verify\s*$", portal, re.M)),
        "the job display name is the branch-protection contract",
    )
    check("portal workflow: runs the checked-in verifier",
          bool(re.search(r"^\s*run:\s*python3 verify\.py\s*$", portal, re.M)))
    check("portal workflow: verifier is fail-closed",
          bool(portal) and "continue-on-error" not in portal)

    unfiltered_pull_request(sdlc, "SDLC workflow")
    read_only_permissions(sdlc, "SDLC workflow")
    check(
        "SDLC workflow: stable caller job id",
        bool(re.search(r"^\s{2}sdlc-gate:\s*$", sdlc, re.M)),
        "the caller job id is part of the required-check identity",
    )
    gate_sha = "582c818fbb6699ed8813df2d5a722a2c4da32f5c"
    check(
        "SDLC workflow: immutable binding-capable pin",
        f"sdlc-gate-reusable.yml@{gate_sha}" in sdlc,
    )
    check(
        "SDLC workflow: gate script uses the same immutable ref",
        bool(re.search(rf"^\s*gate-ref:\s*{gate_sha}\s*$", sdlc, re.M)),
        "cross-repository callers cannot rely on github.workflow_sha selecting the gate repo",
    )
    check("SDLC workflow: active intent is required",
          bool(re.search(r"^\s*require-active:\s*true\s*$", sdlc, re.M)))

    template_needles = (
        ("tracking issue", "Tracking issue"),
        ("active intent", "Active intent"),
        ("actual verification", "python3 verify.py"),
        ("plan compliance", "matches the accepted plan"),
        ("conditional visual evidence", "Visual changes only"),
        ("360px evidence", "360px"),
        ("768px evidence", "768px"),
        ("1440px evidence", "1440px"),
        ("keyboard evidence", "keyboard-only"),
        ("no-JavaScript evidence", "JavaScript disabled"),
        ("unavailable-check disclosure", "could not run"),
    )
    for name, needle in template_needles:
        check(f"pull-request template: {name}", bool(template) and needle in template)

    readme_needles = (
        ("contribution section", "## Contributing changes"),
        ("pull-request path", "Every portal revision goes through a pull request"),
        ("local verification", "python3 verify.py"),
        ("required-check distinction", "A workflow check is not a gate until"),
        ("owner bypass limit", "personal-repository owner can still edit or remove"),
        ("bootstrap record", "issues/4"),
    )
    for name, needle in readme_needles:
        check(f"README governance: {name}", bool(readme) and needle in readme)

    for relative in (
        "intent/review-follow-ups/intent.md",
        "intent/review-follow-ups/spec.md",
        "intent/review-follow-ups/plan.md",
        "intent/readme-front-door/intent.md",
        "intent/readme-front-door/spec.md",
        "intent/readme-front-door/plan.md",
    ):
        check(
            f"spent chain closed: {relative}",
            artifact_status(relative) == "shipped",
            f"status={artifact_status(relative)!r}, need 'shipped'",
        )


def privacy_checks() -> None:
    """Verify every checked-in surface of the layered privacy guardrail."""
    required = {
        "privacy scanner": "scripts/privacy_scan.py",
        "scanner tests": "scripts/test_privacy_scan.py",
        "PreToolUse hook tests": "scripts/test_privacy_pretooluse_hook.py",
        "Kiro config tests": "scripts/test_privacy_hook_config.py",
        "pre-push tests": "scripts/test_privacy_pre_push.py",
        "privacy mutation proof": "scripts/privacy_mutation_proof.py",
        "privacy allowlist": ".privacy-allowlist.json",
        "privacy PreToolUse hook": "scripts/privacy_pretooluse_hook.py",
        "Kiro privacy hook config": ".kiro/hooks/privacy-scan.json",
        "privacy Git pre-push hook": ".githooks/pre-push",
        "privacy hook installer": "scripts/install_privacy_hooks.sh",
        "privacy workflow": ".github/workflows/privacy-scan.yml",
    }
    texts = {
        name: checked_text(HERE / relative, name)
        for name, relative in required.items()
    }

    workflow = texts["privacy workflow"]
    unfiltered_pull_request(workflow, "privacy workflow")
    read_only_permissions(workflow, "privacy workflow")
    push_found, push_block = yaml_mapping_block(workflow, "push")
    check("privacy workflow: main push trigger exists",
          push_found and bool(re.search(r"branches:\s*\[main\]", push_block)))
    dispatch_found, _ = yaml_mapping_block(workflow, "workflow_dispatch")
    check("privacy workflow: manual trigger exists", dispatch_found)
    check(
        "privacy workflow: stable job id",
        bool(re.search(r"^\s{2}privacy-scan:\s*$", workflow, re.M)),
    )
    check(
        "privacy workflow: stable check name",
        bool(re.search(r"^\s{4}name:\s*privacy scan\s*$", workflow, re.M)),
    )
    check("privacy workflow: full-history checkout",
          bool(re.search(r"^\s*fetch-depth:\s*0\s*$", workflow, re.M)))
    for label, command in (
        ("runs privacy tests", "python3 -m unittest discover -s scripts -p 'test_privacy*.py'"),
        ("runs mutation proof", "python3 scripts/privacy_mutation_proof.py"),
        ("scans the tracked tree", "python3 scripts/privacy_scan.py --repo ."),
    ):
        check(f"privacy workflow: {label}", bool(workflow) and command in workflow)
    check("privacy workflow: required steps fail closed",
          bool(workflow) and "continue-on-error" not in workflow)
    check(
        "privacy workflow: checks pull-request commit identities",
        bool(workflow) and 'python3 scripts/privacy_scan.py --repo . --commit-range '
        '"$BASE_SHA" "$HEAD_SHA"' in workflow,
    )
    check(
        "privacy workflow: identity step runs on pull requests only",
        bool(re.search(r"^\s*if:\s*github\.event_name\s*==\s*'pull_request'\s*$", workflow, re.M)),
    )
    for label, ref in (("base", "base.sha"), ("head", "head.sha")):
        check(
            f"privacy workflow: {label} SHA arrives through env",
            bool(re.search(
                rf"^\s*{label.upper()}_SHA:\s*\$\{{\{{\s*github\.event\.pull_request\."
                rf"{re.escape(ref)}\s*\}}\}}\s*$", workflow, re.M,
            )),
        )
    check(
        "privacy workflow: no expression is interpolated into a run line",
        bool(workflow) and not re.search(r"^\s*run:.*\$\{\{", workflow, re.M),
        "pass event values through env: and reference them as shell variables",
    )

    hook_json = texts["Kiro privacy hook config"]
    for label, needle in (
        ("v1 format", '"version": "v1"'),
        ("PreToolUse trigger", '"trigger": "PreToolUse"'),
        ("write matcher", '"matcher": "write"'),
        ("command action", '"type": "command"'),
        ("checked-in adapter", "scripts/privacy_pretooluse_hook.py"),
        ("bounded timeout", '"timeout": 15'),
        ("enabled", '"enabled": true'),
    ):
        check(f"Kiro privacy hook: {label}", bool(hook_json) and needle in hook_json)

    allowlist = texts["privacy allowlist"]
    check("privacy allowlist: schema 1",
          bool(re.search(r'"schema_version"\s*:\s*1', allowlist)))
    for forbidden in ("exclude_paths", "exclude_categories", "skip_files", "skip_directories"):
        check(f"privacy allowlist: no {forbidden}",
              bool(allowlist) and forbidden not in allowlist)

    readme = (HERE / "README.md").read_text(encoding="utf-8")
    for label, needle in (
        ("full scan command", "python3 scripts/privacy_scan.py --repo ."),
        ("POSIX-only terminal hook", "POSIX-only"),
        ("hook installer", "scripts/install_privacy_hooks.sh"),
        ("pre-push bypass", "--no-verify"),
        ("agent fail-open", "fails open"),
        ("CI fail-closed", "fails closed"),
        ("redacted findings", "never prints the matched value"),
        ("clean-scan limit", "does not prove the repository contains no PII"),
        ("specialist scanner limit", "not a replacement for a specialist secret scanner"),
        ("tree content surface", "**tree content**"),
        ("commit identity surface", "**commit identity metadata**"),
        ("commit message surface", "**commit messages**"),
        ("trailers covered", "trailers such as `Co-authored-by:` and `Signed-off-by:`"),
        ("uncovered tag identity", "annotated-tag tagger identity"),
        ("uncovered main merges", "merge commits GitHub creates on `main`"),
        ("web-flow allowlist reason", "web-flow committer address"),
        ("bot trailer allowlist reason", "public bot address that a coding agent"),
    ):
        check(f"README privacy: {label}", needle in readme)
    uncovered = re.search(r"^Not covered:(.*?)(?:\n\n|\Z)", readme, re.S | re.M)
    check("README privacy: commit messages are not listed as uncovered",
          bool(uncovered) and "commit messages" not in uncovered.group(1),
          "no 'Not covered:' paragraph" if not uncovered else "")

    layout = re.search(r"^## Layout\s*\n+```[^\n]*\n(.*?)^```", readme, re.S | re.M)
    block = layout.group(1) if layout else ""
    missing = [e for e in LAYOUT_ENTRIES
               if not re.search(rf"^{re.escape(e)}(\s|$)", block, re.M)]
    check("README layout: lists the published tree",
          bool(layout) and not missing and "entire site" not in block,
          "no fenced block under '## Layout'" if not layout
          else f"missing={missing} entire-site={'entire site' in block}")

    # Build the old machine identity at runtime so this verifier does not become a fresh leak of
    # the literal it is removing. Only the two measured baseline artifacts should need remediation.
    old_user = "".join(("ec2", "-user"))
    old_home = "/" + "/".join(("home", old_user)) + "/"
    for relative in (
        "intent/review-follow-ups/intent.md",
        "intent/review-follow-ups/plan.md",
    ):
        body = (HERE / relative).read_text(encoding="utf-8")
        check(f"privacy baseline genericized: {relative}",
              old_user not in body and old_home not in body,
              "a real developer-home marker remains in tracked history prose")


def _css_number(html: str, name: str, unit: str) -> tuple[bool, float]:
    match = re.search(rf"--{re.escape(name)}:\s*([\d.]+){re.escape(unit)}", html)
    return (match is not None, float(match.group(1)) if match else 0.0)


def responsive_checks(html: str, page: Page) -> tuple[float, float]:
    """Check responsive contracts and return actual compact/wide SVG widths."""
    expected = {
        "page-gutter": (16.0, "px"),
        "measure": (70.0, "ch"),
        "touch-target": (44.0, "px"),
        "figure-padding": (14.0, "px"),
        "figure-max": (420.0, "px"),
        "diagram-max": (360.0, "px"),
    }
    values: dict[str, float] = {}
    for name, (wanted, unit) in expected.items():
        found, value = _css_number(html, name, unit)
        values[name] = value
        check(
            f"responsive token --{name} is {wanted:g}{unit}",
            found and value == wanted,
            f"found {value:g}{unit}" if found else "token missing",
        )

    check("wrap consumes the page gutter token",
          ".wrap{max-width:1020px;margin:0 auto;padding:0 var(--page-gutter)}" in html)
    check("medium layout raises the page gutter to 20px",
          bool(re.search(r"@media\(min-width:48rem\).*?:root\{--page-gutter:20px\}", html, re.S)))
    check("medium responsive breakpoint exists", "@media(min-width:48rem)" in html)
    check("wide responsive breakpoint exists", "@media(min-width:64rem)" in html)
    check("old 700px breakpoint is removed", "min-width:700px" not in html)
    check("old 760px breakpoint is removed", "min-width:760px" not in html)
    check("top-level prose consumes the readable measure",
          bool(re.search(r"section>\.wrap>p[^}]*max-width:var\(--measure\)", html)))
    check("hero spacing is fluid without resetting inline gutter",
          bool(re.search(r"\.hero\{[^}]*padding-block:clamp\(", html)))
    check("section spacing is fluid", bool(re.search(r"section\{[^}]*padding:clamp\(", html)))

    check("compact navigation is a two-column grid",
          bool(re.search(r"nav\.top\{[^}]*display:grid[^}]*grid-template-columns:repeat\(2,minmax\(0,1fr\)\)", html)))
    check("navigation links use the touch target",
          bool(re.search(r"nav\.top a\{[^}]*min-height:var\(--touch-target\)", html)))
    check("medium navigation restores flex",
          bool(re.search(r"@media\(min-width:48rem\).*?nav\.top\{display:flex", html, re.S)))
    check("compact tabs do not wrap",
          bool(re.search(r"\.tabs\{[^}]*flex-wrap:nowrap", html)))
    check("compact tabs scroll locally",
          bool(re.search(r"\.tabs\{[^}]*overflow-x:auto", html)))
    check("tab buttons use the touch target",
          bool(re.search(r"\.tabs button\{[^}]*min-height:var\(--touch-target\)", html)))
    check("medium tabs restore wrapping",
          bool(re.search(r"@media\(min-width:48rem\).*?\.tabs\{[^}]*flex-wrap:wrap", html, re.S)))

    regions = [
        attrs for tag, attrs in page.tags
        if tag == "div" and "table-scroll" in attrs.get("class", "").split()
    ]
    check("exactly two table overflow regions", len(regions) == 2, f"found {len(regions)}")
    check("table regions are labeled and keyboard focusable",
          len(regions) == 2 and all(
              attrs.get("role") == "region"
              and attrs.get("tabindex") == "0"
              and bool(attrs.get("aria-label"))
              for attrs in regions
          ))
    check("each table is directly wrapped by its region",
          len(re.findall(r'<div class="table-scroll"[^>]*>\s*<table>', html)) == 2
          and len(re.findall(r'</table>\s*</div>', html)) == 2)
    check("table regions scroll locally",
          bool(re.search(r"\.table-scroll\{[^}]*overflow-x:auto", html)))
    check("compact tables retain a readable minimum width",
          bool(re.search(r"\.table-scroll table\{[^}]*min-width:", html)))
    check("code blocks keep bounded local overflow",
          bool(re.search(r"pre\{[^}]*max-width:100%[^}]*overflow:auto", html)))

    check("figure cards are centered and capped",
          bool(re.search(r"figure\.dg\{[^}]*max-width:var\(--figure-max\)[^}]*margin:", html)))
    check("SVGs are centered and capped",
          bool(re.search(r"figure\.dg svg\{[^}]*max-width:var\(--diagram-max\)[^}]*margin:", html)))
    check("reduced motion disables smooth scrolling",
          "@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}" in html)
    check("print forces every hidden panel visible",
          bool(re.search(r"@media print\{.*?\.panel\[hidden\]\{display:block!important\}", html, re.S)))

    sniffers = ("navigator.userAgent", "navigator.platform", "maxTouchPoints", "screen.width")
    found_sniffers = [token for token in sniffers if token in html]
    check("layout uses no device or user-agent sniffing", not found_sniffers,
          f"found {found_sniffers}")

    # Fallbacks expose today's real box model in the red state instead of replacing one guessed
    # divisor with another. The accepted tokens take over once the responsive CSS exists.
    old_wrap = re.search(r"\.wrap\{[^}]*padding:\s*0\s+(\d+)px", html)
    old_border = re.search(r"figure\.dg\{[^}]*border:(\d+)px", html)
    old_padding = re.search(r"figure\.dg\{[^}]*padding:(\d+)px", html)
    gutter = values["page-gutter"] if values["page-gutter"] else (
        float(old_wrap.group(1)) if old_wrap else 0.0
    )
    border = float(old_border.group(1)) if old_border else 0.0
    figure_padding = values["figure-padding"] if values["figure-padding"] else (
        float(old_padding.group(1)) if old_padding else 0.0
    )
    compact_inner = 360.0 - 2 * gutter - 2 * figure_padding - 2 * border
    compact_svg = min(
        compact_inner,
        values["diagram-max"] if values["diagram-max"] else compact_inner,
    )
    wide_figure = values["figure-max"] if values["figure-max"] else 980.0
    wide_inner = wide_figure - 2 * figure_padding - 2 * border
    wide_svg = min(
        wide_inner,
        values["diagram-max"] if values["diagram-max"] else wide_inner,
    )
    check("compact SVG content box is positive", compact_svg > 0, f"width={compact_svg}")
    check("wide SVG content box is positive", wide_svg > 0, f"width={wide_svg}")
    check("compact SVG content box is exactly 298px",
          compact_svg == 298.0, f"width={compact_svg}")
    check("wide SVG content box is exactly 360px",
          wide_svg == 360.0, f"width={wide_svg}")
    print(
        f"  (responsive boxes: compact SVG {compact_svg:.0f}px; "
        f"wide SVG {wide_svg:.0f}px)"
    )
    return compact_svg, wide_svg


LEARNING_STAGES = ("plan", "design", "build", "test", "deploy", "maintain")


def learning_mode_checks(html: str, page: Page) -> None:
    """Verify the signed-off two-mode projection without requiring implementation to exist."""
    tags = page.tags
    tabs = [a for _, a in tags if a.get("role") == "tab"]
    panels = [a for _, a in tags if a.get("role") == "tabpanel"]
    tablists = [a for _, a in tags if a.get("role") == "tablist"]

    tab_stages = [a.get("data-stage", "") for a in tabs]
    panel_stages = [a.get("data-stage", "") for a in panels]
    check("learning modes: one lifecycle tablist", len(tablists) == 1,
          f"found {len(tablists)}")
    check("learning modes: six canonical tabs remain", len(tabs) == 6,
          f"found {len(tabs)}")
    check("learning modes: six canonical panels remain", len(panels) == 6,
          f"found {len(panels)}")
    check("learning modes: tabs use the six semantic stage ids",
          tuple(tab_stages) == LEARNING_STAGES, f"found {tab_stages}")
    check("learning modes: panels use the six semantic stage ids",
          tuple(panel_stages) == LEARNING_STAGES, f"found {panel_stages}")
    check("learning modes: canonical panel ids stay unique",
          len({a.get("id", "") for a in panels}) == 6)

    groups = [a for _, a in tags if "data-learning-mode-group" in a]
    choices = [a for tag, a in tags
               if tag == "button" and "data-learning-mode-choice" in a]
    choice_values = [a.get("data-learning-mode-choice", "") for a in choices]
    check("learning modes: one labeled mode group", len(groups) == 1 and
          bool(groups[0].get("aria-label") or groups[0].get("aria-labelledby")) if groups else False,
          f"found {len(groups)}")
    check("learning modes: exactly Mentor and Self-paced choices",
          len(choices) == 2 and set(choice_values) == {"mentor", "self-paced"},
          f"found {choice_values}")
    check("learning modes: choices expose pressed state",
          len(choices) == 2 and all(a.get("aria-pressed") in {"true", "false"} for a in choices))
    self_paced = [a for a in choices if a.get("data-learning-mode-choice") == "self-paced"]
    check("learning modes: Self-paced is the markup default",
          len(self_paced) == 1 and self_paced[0].get("aria-pressed") == "true")

    guides = [a for _, a in tags if "data-mentor-guide" in a]
    guide_stages = [a.get("data-stage", "") for a in guides]
    durations = []
    for guide in guides:
        try:
            durations.append(int(guide.get("data-duration", "")))
        except ValueError:
            durations.append(0)
    mentor_parts = [a.get("data-mentor-part", "") for _, a in tags
                    if "data-mentor-part" in a]
    check("learning modes: six uniquely staged Mentor guides",
          len(guides) == 6 and tuple(guide_stages) == LEARNING_STAGES,
          f"found {guide_stages}")
    check("learning modes: Mentor duration totals 45 to 60 minutes",
          len(durations) == 6 and 45 <= sum(durations) <= 60,
          f"durations={durations} total={sum(durations)}")
    for part in ("objective", "ask", "demonstrate"):
        check(f"learning modes: each Mentor guide has {part}",
              mentor_parts.count(part) == 6, f"found {mentor_parts.count(part)}")

    mentor_controls = [a for _, a in tags if "data-mentor-controls" in a]
    mentor_prev = [a for _, a in tags if "data-mentor-previous" in a]
    mentor_next = [a for _, a in tags if "data-mentor-next" in a]
    mentor_position = [a for _, a in tags if "data-mentor-position" in a]
    check("learning modes: one shared Mentor control bar",
          len(mentor_controls) == len(mentor_prev) == len(mentor_next) ==
          len(mentor_position) == 1)

    recaps = [a for _, a in tags if "data-self-paced-recap" in a]
    recap_stages = [a.get("data-stage", "") for a in recaps]
    mounts = [a for _, a in tags if "data-question-stage" in a]
    mount_stages = [a.get("data-question-stage", "") for a in mounts]
    check("learning modes: six uniquely staged Self-paced recaps",
          len(recaps) == 6 and tuple(recap_stages) == LEARNING_STAGES,
          f"found {recap_stages}")
    check("learning modes: six unique stage question mounts",
          len(mounts) == 6 and tuple(mount_stages) == LEARNING_STAGES,
          f"found {mount_stages}")

    progress_regions = [a for _, a in tags if "data-learning-progress" in a]
    progress_values = [a for tag, a in tags if tag == "progress" and a.get("max") == "6"]
    continues = [a for _, a in tags if "data-learning-continue" in a]
    completes = [a for _, a in tags if "data-mark-complete" in a]
    resets = [a for _, a in tags if "data-learning-reset" in a]
    live = [a for _, a in tags if "data-learning-live" in a and a.get("aria-live") == "polite"]
    check("learning modes: one shared Self-paced progress region",
          len(progress_regions) == 1)
    check("learning modes: progress exposes an accessible six-stage value",
          len(progress_values) == 1 and bool(progress_values[0].get("aria-label") or
                                             progress_values[0].get("aria-labelledby")))
    check("learning modes: Continue, Mark Complete and Reset exist once",
          len(continues) == len(completes) == len(resets) == 1)
    check("learning modes: one polite shared live region", len(live) == 1)

    dialogs = [a for tag, a in tags if tag == "dialog" and "data-reset-dialog" in a]
    cancels = [a for _, a in tags if "data-reset-cancel" in a]
    confirms = [a for _, a in tags if "data-reset-confirm" in a]
    check("learning modes: one accessible reset dialog",
          len(dialogs) == 1 and bool(dialogs[0].get("aria-label") or
                                     dialogs[0].get("aria-labelledby")))
    check("learning modes: reset dialog has one Cancel and one Reset action",
          len(cancels) == len(confirms) == 1)
    check("learning modes: browser-native dialogs are absent",
          not re.search(r"\b(?:window\.)?(?:confirm|alert|prompt)\s*\(", html))

    additions = [a for _, a in tags if any(k in a for k in (
        "data-learning-mode-group", "data-mentor-guide", "data-self-paced-recap",
        "data-question-stage", "data-mentor-controls", "data-learning-progress",
        "data-reset-dialog",
    ))]
    check("learning modes: every learning node is marked as an addition",
          bool(additions) and all("data-learning-addition" in a for a in additions))

    question_block = re.search(r"var\s+QUESTIONS\s*=\s*\[(.*?)\];", html, re.S)
    question_source = question_block.group(1) if question_block else ""
    question_stages = re.findall(r"\bstage\s*:\s*['\"]([^'\"]+)['\"]", question_source)
    check("learning modes: one six-entry staged question source",
          bool(question_block) and tuple(question_stages) == LEARNING_STAGES,
          f"found {question_stages}")
    check("learning modes: questions render into stage mounts",
          "data-question-stage" in html and "item.stage" in html)

    check("learning modes: exact storage namespace",
          "ai-native-sdlc.learning.v1" in html)
    fields_match = re.search(r"LEARNING_STORAGE_FIELDS\s*=\s*\[([^\]]*)\]", html, re.S)
    fields = re.findall(r"['\"]([A-Za-z]+)['\"]",
                        fields_match.group(1) if fields_match else "")
    expected_fields = ["version", "mode", "currentStage", "completedStages"]
    check("learning modes: storage schema has exactly four approved fields",
          fields == expected_fields, f"found {fields}")
    check("learning modes: schema version is one",
          bool(re.search(r"LEARNING_SCHEMA_VERSION\s*=\s*1\b", html)))
    for function in (
        "defaultLearningState", "validateLearningState", "loadLearningState",
        "saveLearningState", "clearLearningState", "setLearningMode",
        "markStageComplete", "openResetDialog", "closeResetDialog",
        "confirmLearningReset",
    ):
        check(f"learning modes: {function} is implemented",
              bool(re.search(rf"function\s+{function}\s*\(", html)))
    check("learning modes: invalid records reject unknown fields",
          "LEARNING_STORAGE_FIELDS.indexOf(key)" in html and "Object.keys(record)" in html)
    check("learning modes: storage operations are guarded",
          html.count("localStorage.getItem") == 1 and
          html.count("localStorage.setItem") == 1 and
          html.count("localStorage.removeItem") == 1 and
          html.count("try{") >= 3)
    check("learning modes: session-only fallback is visible",
          "session-only" in page.text.casefold())
    check("learning modes: completion is explicitly button-bound",
          "addEventListener('click', markStageComplete)" in html or
          'addEventListener("click", markStageComplete)' in html)
    check("learning modes: reset confirm is the only clear-state action",
          "addEventListener('click', confirmLearningReset)" in html or
          'addEventListener("click", confirmLearningReset)' in html)

    prohibited_fields = {"answer", "correctness", "score", "timestamp", "duration",
                         "identity", "analytics"}
    check("learning modes: persisted fields exclude answer and telemetry data",
          bool(fields_match) and not (set(fields) & prohibited_fields))
    check("learning modes: enhancement applies a learning-mode attribute",
          "data-learning-mode" in html and "setAttribute('data-learning-mode'" in html)
    check("learning modes: guidance remains visible before enhancement",
          "[data-mode-content]{display:none" not in html)
    check("learning modes: accurate no-JavaScript guidance is present",
          page.has_noscript and "mentor" in page.text.casefold() and
          "self-paced" in page.text.casefold())
    check("learning modes: print exposes both guidance projections",
          bool(re.search(r"@media print\{.*?data-mode-content.*?display:block", html, re.S)))
    check("learning modes: print hides mode and progress mutation controls",
          bool(re.search(r"@media print\{.*?data-learning-controls.*?display:none", html, re.S)))

    print(
        f"  (learning modes: {len(guides)} Mentor guides, {len(recaps)} recaps, "
        f"{len(mounts)} question mounts, {len(fields)} persisted fields, "
        f"{sum(durations)} Mentor minutes)"
    )


# ---------------------------------------------------------------------------------------------
# Play catalogue (plays.html), its links from index.html, and the source-overlap ratchet.
# Every constant below is copied from the signed-off spec for intent/playbook-play-coverage.

PLAYS_PAGE = HERE / "plays.html"
PLAYS_BUDGET = 55_000
SOURCE_URL = "https://claude.com/blog/the-ai-native-sdlc-playbook"
SOURCE_DATE = "2026-08-21"
SOURCE_SHINGLES = HERE / "evals" / "source-shingles.txt"
OVERLAP_BASELINE = HERE / "evals" / "index-source-overlap-baseline.txt"
BASELINE_REF = "514366c8b9d99e38b7fa17e4547ce61e9c713581"
WINDOW = 8
NOT_STATED = "Not stated in the source"
OOS = "declared out of scope"
STATUSES = ("implemented", "partial", OOS)
FIELDS = ("summary", "prerequisites", "governance", "leading", "lagging", "status", "evidence")

# id, stage, source play name, status, evidence paths (globs allowed)
PLAYS: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    ("capture-intent", "plan", "Capture as intent.md", "implemented", ("intent/", ".sdlc/active")),
    ("requirements-design", "design", "Requirements and design", "partial", ("intent/*/spec.md",)),
    ("plan-mode", "build", "Claude Code plan mode as the default starting point", "implemented",
     ("intent/*/plan.md", ".github/workflows/sdlc-gate.yml")),
    ("auto-mode", "build", "Claude Code on auto mode", OOS, ()),
    ("claude-md", "build", "The CLAUDE.md", OOS, ()),
    ("skills", "build", "Skills as institutional knowledge", "partial", ("README.md",)),
    ("build-hooks", "build", "Hooks as build-time guardrails", "implemented",
     (".kiro/hooks/privacy-scan.json", "scripts/privacy_pretooluse_hook.py")),
    ("parallel-sessions", "build", "Parallel sessions and subagents", OOS, ()),
    ("feedback-loop", "test", "Give Claude a feedback loop", "implemented",
     ("verify.py", ".github/workflows/portal-verify.yml")),
    ("continuous-evals", "test", "Continuous evals in CI", "partial",
     ("scripts/privacy_mutation_proof.py", ".github/workflows/portal-verify.yml")),
    ("pr-review", "deploy", "AI in the PR review loop", "partial",
     (".github/pull_request_template.md", ".github/workflows/sdlc-gate.yml")),
    ("approval-hooks", "deploy", "Hooks as approval gates", "partial", (".githooks/pre-push",)),
    ("cicd", "deploy", "CI/CD integration and deployment", "partial", (".github/workflows/",)),
    ("closing-loop", "maintain", "Closing the loop", OOS, ()),
    ("recurring-scans", "maintain", "Recurring codebase scans", OOS, ()),
    ("claude-tag", "maintain", "Claude on call with Claude Tag", OOS, ()),
)
PLAY_IDS = tuple(p[0] for p in PLAYS)
OOS_IDS = frozenset(p[0] for p in PLAYS if p[3] == OOS)


def _edges(play: str, required: str, helps: str) -> set[tuple[str, str, str]]:
    out = {(src, play, "required") for src in required.split()}
    return out | {(src, play, "helps") for src in helps.split()}


# Edge = (prerequisite, dependent play, kind), from each play's Prerequisites paragraph.
EDGES: frozenset[tuple[str, str, str]] = frozenset().union(
    _edges("requirements-design", "capture-intent skills", ""),
    _edges("plan-mode", "", "capture-intent requirements-design claude-md"),
    _edges("skills", "", "claude-md"),
    _edges("parallel-sessions", "claude-md", "feedback-loop"),
    _edges("continuous-evals", "claude-md feedback-loop", ""),
    _edges("pr-review", "claude-md", "skills parallel-sessions"),
    _edges("cicd", "pr-review approval-hooks", ""),
    _edges("closing-loop", "capture-intent pr-review approval-hooks cicd", ""),
    _edges("recurring-scans", "pr-review approval-hooks capture-intent", ""),
)
INTERPRETIVE_EDGES = frozenset({
    ("parallel-sessions", "pr-review", "helps"),
    ("approval-hooks", "closing-loop", "required"),
})
NONE_PREREQ = frozenset({"capture-intent", "claude-md", "feedback-loop", "approval-hooks"})
NO_SOURCE_SECTION = frozenset({"auto-mode", "build-hooks", "claude-tag"})
CROSSCUTS = ("legacy-systems", "managed-settings")
GLOSSARY_SLUGS = (
    "intent", "spec", "plan", "play", "gate", "control-band", "hook", "skill", "subagent",
    "worktree", "eval", "mcp", "managed-settings", "merge-base",
)
TERMINOLOGY = (
    "CLAUDE.md", ".claude/skills/", ".claude/settings.json hooks", ".claude/agents/",
    "REVIEW.md", "bands.yaml", "evals/", "managed settings",
)
VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


class Tree(HTMLParser):
    """Element tree with per-element visible text, enough to scope checks to one element."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[dict] = []
        self._stack: list[int] = []
        self._suppress = 0

    def _add(self, tag: str, attrs: list[tuple[str, str | None]]) -> int:
        parent = self._stack[-1] if self._stack else -1
        self.nodes.append({"tag": tag, "attrs": {k: (v or "") for k, v in attrs},
                           "parent": parent, "text": []})
        return len(self.nodes) - 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        i = self._add(tag, attrs)
        if tag in VOID:
            return
        self._stack.append(i)
        if tag in ("script", "style"):
            self._suppress += 1

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._add(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        for depth in range(len(self._stack) - 1, -1, -1):
            if self.nodes[self._stack[depth]]["tag"] == tag:
                for j in self._stack[depth:]:
                    if self.nodes[j]["tag"] in ("script", "style") and self._suppress:
                        self._suppress -= 1
                del self._stack[depth:]
                return

    def handle_data(self, data: str) -> None:
        if not self._suppress:
            for i in self._stack:
                self.nodes[i]["text"].append(data)

    def attrs(self, i: int) -> dict[str, str]:
        return self.nodes[i]["attrs"]

    def text(self, i: int) -> str:
        return re.sub(r"\s+", " ", "".join(self.nodes[i]["text"])).strip()

    def ancestors(self, i: int) -> list[int]:
        out = []
        while (i := self.nodes[i]["parent"]) != -1:
            out.append(i)
        return out

    def within(self, i: int) -> list[int]:
        out = []
        for j in range(i + 1, len(self.nodes)):
            if i not in self.ancestors(j):
                break
            out.append(j)
        return out

    def find(self, **want: str) -> list[int]:
        return [i for i, n in enumerate(self.nodes)
                if all(n["tag"] == v if k == "tag" else n["attrs"].get(k) == v
                       for k, v in want.items())]


def parse_tree(html: str) -> Tree:
    t = Tree()
    t.feed(html)
    return t


def repo_path_exists(path: str) -> bool:
    if any(c in path for c in "*?["):
        return any(HERE.glob(path))
    return (HERE / path).exists()


def normalised_words(text: str) -> list[str]:
    return re.sub(r"[\W_]+", " ", text.casefold()).split()


def digest(data: bytes) -> str:
    """SHA-256 as lowercase unpadded base32 (52 characters).

    Hex is not used: its digit runs match the privacy scan's payment-card rule.
    """
    return base64.b32encode(hashlib.sha256(data).digest()).decode("ascii").rstrip("=").lower()


def windows(text: str) -> list[tuple[str, str]]:
    """Every eight-word window of visible text, as (sha256 base32, words)."""
    words = normalised_words(text)
    out = []
    for k in range(len(words) - WINDOW + 1):
        w = " ".join(words[k:k + WINDOW])
        out.append((digest(w.encode("utf-8")), w))
    return out


def visible_text(html: str) -> str:
    p = Page()
    p.feed(html)
    return p.text


def read_fixture(text: str) -> tuple[dict[str, str], list[str], list[str]]:
    """Header ('# key: value'), hash lines, and any line that is neither."""
    header: dict[str, str] = {}
    hashes: list[str] = []
    bad: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            m = re.match(r"#\s*([a-z-]+):\s*(.*)$", line)
            if m:
                header[m.group(1)] = m.group(2).strip()
        elif re.fullmatch(r"[a-z2-7]{52}", line):
            hashes.append(line)
        elif line.strip():
            bad.append(line[:40])
    return header, hashes, bad


def play_catalogue_checks(html: str) -> dict[str, int]:
    """Spec 1, 3, 5-18, 20-21 against plays.html. An absent page fails every check by name."""
    ok = bool(html)
    t = parse_tree(html)
    tags = [n["tag"] for n in t.nodes]
    style = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    hrefs = [t.attrs(i).get("href", "") for i in t.find(tag="a")]
    size = len(html.encode("utf-8"))

    check("plays: plays.html exists", ok, "not found beside index.html")
    check(f"plays: page is within the {PLAYS_BUDGET:,}-byte budget",
          ok and size <= PLAYS_BUDGET, f"page is {size:,} bytes")

    # isolation (spec 1)
    srcs = [n["attrs"]["src"] for n in t.nodes if "src" in n["attrs"]]
    check("plays: no script element", ok and "script" not in tags)
    check("plays: no external src, stylesheet, @import or url()", ok and not srcs
          and not any(t.attrs(i).get("rel", "").casefold() == "stylesheet" for i in t.find(tag="link"))
          and "@import" not in html and not re.search(r"url\(\s*['\"]?https?:", html),
          f"src={srcs[:3]}")
    ext = [h for h in hrefs if h.startswith(("http://", "https://"))]
    bad_ext = [h for h in ext if not re.match(r"https://(claude\.com|github\.com)/", h)]
    check("plays: external links are limited to the two sources", ok and not bad_ext,
          f"unexpected={bad_ext[:3]}")

    # structure and accessibility (spec 3, 20)
    html_tags = t.find(tag="html")
    check("plays: html lang is en", ok and bool(html_tags) and t.attrs(html_tags[0]).get("lang") == "en")
    check("plays: viewport meta tag", ok and bool(t.find(tag="meta", name="viewport")))
    check("plays: prefers-reduced-motion rule", ok and "prefers-reduced-motion" in style)
    check("plays: print rule", ok and "@media print" in style)
    check("plays: 44px touch-target rule", ok and "44px" in style)
    check("plays: exactly one h1", ok and tags.count("h1") == 1, f"found {tags.count('h1')}")
    levels = [int(tg[1]) for tg in tags if re.fullmatch(r"h[1-6]", tg)]
    check("plays: no skipped heading level",
          ok and bool(levels) and levels[0] == 1
          and all(b <= a + 1 for a, b in zip(levels, levels[1:])), f"levels={levels[:12]}")
    focusable = [i for i, n in enumerate(t.nodes)
                 if (n["tag"] == "a" and "href" in n["attrs"])
                 or n["tag"] in ("button", "input", "select", "textarea")
                 or n["attrs"].get("tabindex", "-1") not in ("-1", "")]
    first = t.attrs(focusable[0]).get("href", "") if focusable else ""
    all_ids = [n["attrs"]["id"] for n in t.nodes if "id" in n["attrs"]]
    check("plays: skip link is the first focusable element",
          ok and first.startswith("#") and first[1:] in all_ids
          and "skip" in t.text(focusable[0]).casefold(), f"first={first!r}")
    dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
    check("plays: no duplicate id", ok and not dupes, f"duplicated: {dupes}")
    back = [f"index.html#p{n}" for n in range(1, 7)]
    check("plays: links back to index.html and each stage panel",
          ok and "index.html" in hrefs and all(b in hrefs for b in back),
          f"missing={[b for b in back if b not in hrefs]}")
    check("plays: no <pre> block reproduces a source code sample", ok and "pre" not in tags)
    tables = t.find(tag="table")
    unscrolled = [i for i in tables if not any(
        t.attrs(a).get("tabindex") == "0" and t.attrs(a).get("role") == "region"
        and (t.attrs(a).get("aria-label") or t.attrs(a).get("aria-labelledby"))
        for a in t.ancestors(i))]
    check("plays: every table sits in a labelled, focusable scroll region",
          ok and bool(tables) and not unscrolled, f"{len(unscrolled)} of {len(tables)} unscrolled")

    # stage sections (spec 6)
    sections = [i for i in t.find(tag="section") if t.attrs(i).get("id") in LEARNING_STAGES]
    check("plays: six stage sections in canonical order",
          ok and tuple(t.attrs(i)["id"] for i in sections) == LEARNING_STAGES,
          f"found {[t.attrs(i)['id'] for i in sections]}")
    unattributed = [t.attrs(i)["id"] for i in sections if not any(
        SOURCE_URL in t.attrs(j).get("href", "") for j in t.within(i))]
    check("plays: every stage section links the source", ok and len(sections) == 6
          and not unattributed, f"unattributed={unattributed}")

    # closed play set (spec 5)
    articles = t.find(tag="article")
    art_ids = tuple(t.attrs(i).get("id", "") for i in articles)
    check("plays: exactly the 16 play ids in spec order", ok and art_ids == PLAY_IDS,
          f"found {len(art_ids)}: {[a for a in art_ids if a not in PLAY_IDS][:3]} extra, "
          f"{[p for p in PLAY_IDS if p not in art_ids][:3]} missing")
    by_id = {t.attrs(i).get("id", ""): i for i in articles}

    offenders: dict[str, list[str]] = {k: [] for k in (
        "data-play", "stage", "heading", "fields", "status", "visible", "evidence-set",
        "evidence-exists", "evidence-visible", "gap", "reason", "prereq", "marker", "summary")}
    statuses: dict[str, int] = {s: 0 for s in STATUSES}
    for pid, stage, name, status, evidence in PLAYS:
        i = by_id.get(pid)
        if i is None:
            for k in offenders:
                offenders[k].append(pid)
            continue
        a = t.attrs(i)
        inner = t.within(i)
        if a.get("data-play") != pid:
            offenders["data-play"].append(pid)
        section = next((s for s in t.ancestors(i) if t.nodes[s]["tag"] == "section"), -1)
        if a.get("data-stage") != stage or section == -1 or t.attrs(section).get("id") != stage:
            offenders["stage"].append(pid)
        heads = [j for j in inner if re.fullmatch(r"h[2-6]", t.nodes[j]["tag"])]
        if not heads or t.text(heads[0]) != name:
            offenders["heading"].append(pid)
        field_nodes: dict[str, int] = {}
        order = []
        for j in inner:
            f = t.attrs(j).get("data-field")
            if f:
                order.append(f)
                field_nodes.setdefault(f, j)
        if [f for f in order if f in FIELDS] != list(FIELDS):
            offenders["fields"].append(pid)
        ftext = {f: t.text(j) for f, j in field_nodes.items()}
        st = field_nodes.get("status")
        got = t.attrs(st).get("data-status") if st is not None else None
        if got != status:
            offenders["status"].append(pid)
        elif status in STATUSES:
            statuses[status] += 1
        if st is None or status not in ftext.get("status", "").casefold():
            offenders["visible"].append(pid)
        ev = field_nodes.get("evidence")
        paths = t.attrs(ev).get("data-evidence", "").split() if ev is not None else []
        if set(paths) != set(evidence):
            offenders["evidence-set"].append(pid)
        if status != OOS and (not paths or not all(repo_path_exists(p) for p in paths)):
            offenders["evidence-exists"].append(pid)
        if not all(p in ftext.get("evidence", "") for p in paths):
            offenders["evidence-visible"].append(pid)
        if status == "partial" and not ftext.get("gap"):
            offenders["gap"].append(pid)
        if status == OOS and not ftext.get("reason"):
            offenders["reason"].append(pid)
        if not ftext.get("summary"):
            offenders["summary"].append(pid)
        pre = field_nodes.get("prerequisites")
        links = {t.attrs(j).get("href", "")[1:] for j in (t.within(pre) if pre is not None else [])
                 if t.nodes[j]["tag"] == "a" and t.attrs(j).get("href", "").startswith("#")}
        incoming = {src for src, dst, _ in EDGES if dst == pid}
        pre_text = ftext.get("prerequisites", "")
        if pid in NONE_PREREQ:
            good = pre_text == "None" and not links
        elif pid in NO_SOURCE_SECTION:
            good = pre_text == NOT_STATED and not links
        else:
            good = links == incoming
        if not good:
            offenders["prereq"].append(pid)
        for f in ("governance", "leading", "lagging"):
            marked = ftext.get(f) == NOT_STATED
            expect = pid in NO_SOURCE_SECTION and not (pid == "claude-tag" and f == "governance")
            if marked != expect or not ftext.get(f):
                offenders["marker"].append(f"{pid}.{f}")

    for key, label in (
        ("data-play", "every entry's data-play equals its id"),
        ("stage", "every entry's data-stage matches the spec and its section"),
        ("heading", "every entry's heading is the source play name"),
        ("fields", "every entry has the seven fields in order"),
        ("status", "every status matches the spec table"),
        ("visible", "every status word is visible text"),
        ("evidence-set", "every entry's evidence equals the spec table"),
        ("evidence-exists", "every evidence path exists"),
        ("evidence-visible", "every evidence path is visible text"),
        ("gap", "every partial entry names its gap"),
        ("reason", "every out-of-scope entry states a reason"),
        ("summary", "every entry has a summary"),
        ("prereq", "every entry's prerequisite links equal its incoming edges"),
        ("marker", "'Not stated in the source' appears exactly where the source is silent"),
    ):
        check(f"plays: {label}", ok and not offenders[key], f"offenders={offenders[key][:5]}")
    check("plays: status totals are 4 implemented, 6 partial, 6 out of scope",
          ok and statuses == {"implemented": 4, "partial": 6, OOS: 6}, f"{statuses}")

    # out-of-scope section and cross-cutting notes (spec 5, 11)
    oos_node = t.find(id="out-of-scope")
    oos_links = {t.attrs(j).get("href", "")[1:] for j in (t.within(oos_node[0]) if oos_node else [])
                 if t.nodes[j]["tag"] == "a" and t.attrs(j).get("href", "").startswith("#")}
    oos_status = {t.attrs(i).get("id") for i in articles for j in t.within(i)
                  if t.attrs(j).get("data-status") == OOS}
    check("plays: #out-of-scope lists exactly the out-of-scope entries",
          ok and oos_links == OOS_IDS == oos_status, f"links={sorted(oos_links)}")
    cross = [i for i, n in enumerate(t.nodes) if "data-crosscut" in n["attrs"]]
    cross_vals = sorted(t.attrs(i)["data-crosscut"] for i in cross)
    check("plays: the two cross-cutting notes appear once each, outside any play",
          ok and cross_vals == sorted(CROSSCUTS)
          and not any(t.nodes[a]["tag"] == "article" for i in cross for a in [i, *t.ancestors(i)]),
          f"found {cross_vals}")

    # dependency list and figure (spec 13-15)
    dep = t.find(id="dependency-list")
    li_edges = [t.attrs(j)["data-edge"] for j in (t.within(dep[0]) if dep else [])
                if t.nodes[j]["tag"] == "li" and "data-edge" in t.attrs(j)]
    list_set = {tuple(e.split()) for e in li_edges}
    check("plays: dependency list equals the spec edge table",
          ok and len(li_edges) == len(list_set) and list_set == EDGES,
          f"{len(li_edges)} listed; missing={sorted(EDGES - list_set)[:2]} "
          f"extra={sorted(list_set - EDGES)[:2]}")
    uninterpreted = [e for e in INTERPRETIVE_EDGES
                     if not any(tuple(t.attrs(j).get("data-edge", "").split()) == e
                                and "interpret" in t.text(j).casefold()
                                for j in (t.within(dep[0]) if dep else []))]
    check("plays: the two interpretive edges are labelled as interpretive",
          ok and not uninterpreted, f"unlabelled={uninterpreted}")
    svgs = [i for i in t.find(tag="svg") if t.attrs(i).get("role") == "img"]
    svg = svgs[0] if svgs else None
    svg_in = t.within(svg) if svg is not None else []
    fig = next((a for a in t.ancestors(svg) if t.nodes[a]["tag"] == "figure"), None) \
        if svg is not None else None
    check("plays: figure has role=img, title, desc and a visible caption",
          ok and svg is not None and fig is not None
          and any(t.nodes[j]["tag"] == "title" and t.text(j) for j in svg_in)
          and any(t.nodes[j]["tag"] == "desc" and t.text(j) for j in svg_in)
          and any(t.nodes[j]["tag"] == "figcaption" and t.text(j) for j in t.within(fig)))
    groups = [j for j in svg_in if t.nodes[j]["tag"] == "g" and "data-edge" in t.attrs(j)]
    fig_set = {tuple(t.attrs(j)["data-edge"].split()) for j in groups}
    check("plays: figure edge set equals the dependency list",
          ok and bool(fig_set) and fig_set == list_set and len(groups) == len(fig_set),
          f"figure={len(groups)} list={len(list_set)}; "
          f"figure-only={sorted(fig_set - list_set)[:2]}")
    wrong_dash = []
    for j in groups:
        kind = t.attrs(j)["data-edge"].split()[-1]
        dashed = any("stroke-dasharray" in t.attrs(k) for k in [j, *t.within(j)])
        if dashed != (kind == "helps"):
            wrong_dash.append(t.attrs(j)["data-edge"])
    check("plays: figure distinguishes helps from required by dash pattern",
          ok and bool(groups) and not wrong_dash, f"wrong={wrong_dash[:3]}")

    # glossary and terminology map (spec 16-17)
    gl = t.find(id="glossary")
    dts = [j for j in (t.within(gl[0]) if gl else []) if t.nodes[j]["tag"] == "dt"]
    dt_ids = [t.attrs(j).get("id", "") for j in dts]
    dt_text = [t.text(j).casefold() for j in dts]
    slugs = [d[5:] for d in dt_ids if d.startswith("term-")]
    check("plays: glossary has no duplicate term",
          ok and bool(dts) and len(slugs) == len(dts) == len(set(slugs)) == len(set(dt_text)),
          f"{len(dts)} terms, {len(set(slugs))} unique ids")
    check("plays: glossary defines the 14 required terms",
          ok and all(s in slugs for s in GLOSSARY_SLUGS),
          f"missing={[s for s in GLOSSARY_SLUGS if s not in slugs]}")
    tm = t.find(id="terminology")
    rows = [j for j in (t.within(tm[0]) if tm else []) if "data-term" in t.attrs(j)]
    terms = [t.attrs(j)["data-term"] for j in rows]
    bad_rows = []
    for j in rows:
        cell = next((k for k in t.within(j) if "data-counterpart" in t.attrs(k)), None)
        value = t.attrs(cell)["data-counterpart"] if cell is not None else ""
        if not value or value not in t.text(cell) or (
                value != "No counterpart" and not repo_path_exists(value)):
            bad_rows.append(t.attrs(j)["data-term"])
    check("plays: terminology map has one row per Playbook term",
          ok and sorted(terms) == sorted(TERMINOLOGY), f"found {terms}")
    check("plays: every terminology row names an existing path or 'No counterpart'",
          ok and bool(rows) and not bad_rows, f"bad={bad_rows}")

    return {"plays": len(articles), "edges": len(list_set), "figure_edges": len(fig_set),
            "glossary": len(dts), "size": size, **statuses}


def index_play_link_checks(index_html: str, plays_html: str) -> None:
    """Spec 2 and 12: index.html links into plays.html and names the same out-of-scope set."""
    t = parse_tree(index_html)
    navs = t.find(tag="nav")
    nav_links = [j for j in (t.within(navs[0]) if navs else [])
                 if t.attrs(j).get("href") == "plays.html"]
    check("index plays: one header-nav link to plays.html", len(nav_links) == 1,
          f"found {len(nav_links)}")
    unlinked = []
    names: dict[str, str] = {}
    for i in (i for i, n in enumerate(t.nodes) if n["attrs"].get("role") == "tabpanel"):
        stage = t.attrs(i).get("data-stage", "")
        links = [j for j in t.within(i) if t.attrs(j).get("href") == f"plays.html#{stage}"]
        if len(links) != 1:
            unlinked.append(stage)
        if links:
            names[stage] = t.text(links[0])
    check("index plays: each stage panel links its plays.html section once",
          not unlinked, f"unlinked={unlinked}")
    folded = [n.casefold() for n in names.values()]
    dupes = sorted({s for s, n in names.items() if folded.count(n.casefold()) > 1})
    unnamed = sorted(s for s, n in names.items()
                     if not re.search(rf"\b{re.escape(s)}\b", n, re.I))
    check("index plays: stage links have distinct names that name their stage",
          len(names) == 6 and not dupes and not unnamed,
          f"duplicate={[(s, names[s]) for s in dupes]} "
          f"missing-stage={[(s, names[s]) for s in unnamed]} found={len(names)}")
    check("index plays: the 'does not cover' heading is kept",
          "what this deliberately does not cover" in visible_text(index_html).casefold())
    oos = [j for j, n in enumerate(t.nodes) if "data-oos" in n["attrs"]]
    oos_ids = [t.attrs(j)["data-oos"] for j in oos]
    bad_href = [x for j, x in zip(oos, oos_ids)
                if t.nodes[j]["tag"] != "a" or t.attrs(j).get("href") != f"plays.html#{x}"]
    pt = parse_tree(plays_html)
    plays_oos = {pt.attrs(a).get("id") for a in pt.find(tag="article") for j in pt.within(a)
                 if pt.attrs(j).get("data-status") == OOS}
    check("index plays: data-oos set equals plays.html out-of-scope set",
          len(oos_ids) == len(set(oos_ids)) and set(oos_ids) == OOS_IDS == plays_oos
          and not bad_href,
          f"index={sorted(oos_ids)} plays={sorted(x for x in plays_oos if x)} bad-href={bad_href}")
    cross = sorted(n["attrs"]["data-crosscut"] for n in t.nodes if "data-crosscut" in n["attrs"])
    check("index plays: the note names both cross-cutting notes", cross == sorted(CROSSCUTS),
          f"found {cross}")


def exempt_play_headings(html: str) -> str:
    """Drop each entry's first heading when its text is exactly the spec play name (spec 19)."""
    for pid, _, name, _, _ in PLAYS:
        start = re.search(rf'<article\b[^>]*\bid="{re.escape(pid)}"', html)
        if not start:
            continue
        head = re.compile(r"<(h[2-6])\b[^>]*>(.*?)</\1>", re.S).search(html, start.end())
        if not head:
            continue
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", head.group(2))).strip()
        if text == name:
            html = html[:head.start()] + html[head.end():]
    return html


def overlap_checks(index_html: str, plays_html: str,
                   source_text: str | None, baseline_text: str | None) -> None:
    """Spec 19: plays.html shares no window with the source; index.html may only shrink."""
    check("overlap: source fixture exists", source_text is not None,
          f"missing {SOURCE_SHINGLES.relative_to(HERE)}")
    check("overlap: baseline fixture exists", baseline_text is not None,
          f"missing {OVERLAP_BASELINE.relative_to(HERE)}")
    if source_text is None or baseline_text is None:
        return
    s_head, s_hashes, s_bad = read_fixture(source_text)
    b_head, b_hashes, b_bad = read_fixture(baseline_text)
    check("overlap: source fixture holds only hashes under its provenance header",
          not s_bad and bool(s_hashes) and s_hashes == sorted(set(s_hashes))
          and s_head.get("source") == SOURCE_URL and s_head.get("source-date") == SOURCE_DATE
          and s_head.get("count") == str(len(s_hashes)), f"header={s_head} bad={s_bad[:2]}")
    check("overlap: baseline fixture holds only hashes recorded at 514366c",
          not b_bad and b_hashes == sorted(set(b_hashes)) and b_head.get("ref") == BASELINE_REF
          and (b_head.get("count") or "").isdigit(), f"header={b_head} bad={b_bad[:2]}")
    source = set(s_hashes)
    baseline = set(b_hashes)
    plays_hits = sorted({w for h, w in windows(visible_text(exempt_play_headings(plays_html)))
                         if h in source})
    check("overlap: plays.html shares no eight-word window with the source",
          bool(plays_html) and not plays_hits, f"{len(plays_hits)} hits, e.g. {plays_hits[:2]}")
    idx = windows(visible_text(index_html))
    idx_hits = {h for h, _ in idx if h in source}
    outside = sorted({w for h, w in idx if h in idx_hits - baseline})
    check("overlap: every index.html source match is in the baseline", not outside,
          f"{len(outside)} unlisted, e.g. {outside[:2]}")
    stale = baseline - idx_hits
    check("overlap: baseline lists no stale hash", not stale, f"{len(stale)} stale")
    recorded = int(b_head["count"]) if (b_head.get("count") or "").isdigit() else -1
    check("overlap: baseline is no larger than the count recorded at 514366c",
          0 <= len(baseline) <= recorded, f"{len(baseline)} listed, header records {recorded}")
    if not QUIET:
        print(f"  (overlap: plays.html {len(plays_hits)} hits; index.html "
              f"{len(outside)} outside the baseline; baseline {len(baseline)} of {recorded})")
        seen = set()
        for h, w in idx:
            if h in baseline and h not in seen:
                seen.add(h)
                print(f"    baseline: {w}")


def optional_text(path: pathlib.Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.is_file() else None


def catalogue_checks(index_html: str, plays_html: str,
                     source_text: str | None, baseline_text: str | None) -> dict[str, int]:
    if not QUIET:
        print(" plays")
    stats = play_catalogue_checks(plays_html)
    if not QUIET:
        print(" index plays")
    index_play_link_checks(index_html, plays_html)
    if not QUIET:
        print(" overlap")
    overlap_checks(index_html, plays_html, source_text, baseline_text)
    return stats


def _fixture(header: list[str], hashes: list[str]) -> str:
    return "\n".join([*header, f"# count: {len(hashes)}", *hashes]) + "\n"


def build_source_shingles(page: pathlib.Path, fetched: str) -> int:
    """Write evals/source-shingles.txt from a fetched copy of the source page."""
    hashes = sorted({h for h, _ in windows(visible_text(page.read_text(encoding="utf-8")))})
    SOURCE_SHINGLES.parent.mkdir(exist_ok=True)
    SOURCE_SHINGLES.write_text(_fixture([
        "# SHA-256 (lowercase base32) of every eight-word window of the source's visible",
        "# text. Hashes only; the source prose is not redistributed here.",
        f"# source: {SOURCE_URL}",
        f"# source-date: {SOURCE_DATE}",
        f"# fetched: {fetched}",
        f"# command: python3 verify.py --build-source-shingles <fetched page> --fetched {fetched}",
    ], hashes), encoding="utf-8")
    print(f"wrote {len(hashes)} source hashes")
    return 0


def build_overlap_baseline() -> int:
    """Write evals/index-source-overlap-baseline.txt from index.html at BASELINE_REF."""
    source = set(read_fixture(SOURCE_SHINGLES.read_text(encoding="utf-8"))[1])
    old = subprocess.run(["git", "show", f"{BASELINE_REF}:index.html"], cwd=HERE,
                         capture_output=True, text=True, check=True).stdout
    hashes = sorted({h for h, _ in windows(visible_text(old)) if h in source})
    OVERLAP_BASELINE.write_text(_fixture([
        "# SHA-256 (lowercase base32) of eight-word windows index.html already shared with the",
        "# source at the ref below. The list may only shrink: stale entries fail, and so does",
        "# growth past count.",
        f"# ref: {BASELINE_REF}",
        "# command: python3 verify.py --build-overlap-baseline",
    ], hashes), encoding="utf-8")
    print(f"wrote {len(hashes)} baseline hashes")
    return 0


def _swap(text: str, pattern: str, repl, count: int = 1) -> str | None:
    """Apply one anchored edit, or None when the anchor is absent (the mutant is BROKEN)."""
    new, n = re.subn(pattern, repl, text, count=count, flags=re.S)
    return new if n else None


def _baseline_words(inp: dict) -> list[tuple[str, str]]:
    baseline = set(read_fixture(inp["baseline"] or "")[1])
    seen: dict[str, str] = {}
    for h, w in windows(visible_text(inp["index"])):
        if h in baseline:
            seen.setdefault(h, w)
    return sorted(seen.items(), key=lambda x: x[1])


def _mut_stale(inp: dict) -> dict | None:
    for h, w in _baseline_words(inp):
        words = w.split()
        pattern = r"(?i)\b" + r"[\W_]+".join(map(re.escape, words)) + r"\b"
        new = re.sub(pattern, lambda m: m.group(0).replace(words[4], "zzqxmutant", 1),
                     inp["index"])
        if new != inp["index"] and h not in {x for x, _ in windows(visible_text(new))}:
            return {**inp, "index": new}
    return None


def _mut_unlisted(inp: dict) -> dict | None:
    words = _baseline_words(inp)
    if not words:
        return None
    drop = words[0][0]
    lines = [ln for ln in (inp["baseline"] or "").splitlines() if ln != drop]
    return {**inp, "baseline": "\n".join(lines) + "\n"}


def _mut_extra_hash(inp: dict) -> dict | None:
    if not inp["baseline"]:
        return None
    head, hashes, _ = read_fixture(inp["baseline"])
    extra = digest(b"verify.py mutation: extra baseline hash")
    body = [ln for ln in inp["baseline"].splitlines() if ln.startswith("#")]
    return {**inp, "baseline": "\n".join(body + sorted(hashes + [extra])) + "\n"}


def _mut_paste_plays(inp: dict) -> dict | None:
    words = _baseline_words(inp)
    new = _swap(inp["plays"], r"</main>", f"<p>{words[0][1]}</p></main>") if words else None
    return {**inp, "plays": new} if new else None


def _mut_paste_heading(inp: dict) -> dict | None:
    """A heading that is more than its play name loses the spec 19 exemption."""
    words = _baseline_words(inp)
    pattern = r'(<article\b[^>]*\bid="capture-intent"[^>]*>\s*<h3>.*?)(</h3>)'
    new = _swap(inp["plays"], pattern, rf"\1 {words[0][1]}\2") if words else None
    return {**inp, "plays": new} if new else None


def _on(key: str, pattern: str, repl) -> object:
    def apply(inp: dict) -> dict | None:
        new = _swap(inp[key], pattern, repl)
        return {**inp, key: new} if new is not None else None
    return apply


MUTATIONS = (
    ("delete one entry", "plays: exactly the 16 play ids in spec order",
     _on("plays", r'<article\b[^>]*\bid="skills"[^>]*>.*?</article>', "")),
    ("invent one entry", "plays: exactly the 16 play ids in spec order",
     _on("plays", r'(<section\b[^>]*\bid="build"[^>]*>)',
         r'\1<article id="invented-play" data-play="invented-play" data-stage="build">'
         r'<h3>Invented play</h3></article>')),
    ("implemented evidence path points at a missing file", "plays: every evidence path exists",
     _on("plays", r'data-evidence="verify\.py', 'data-evidence="verify-missing.py')),
    ("rename the build stage link to \"Stage plays\"",
     "index plays: stage links have distinct names that name their stage",
     _on("index", r'(<a\b[^>]*\bhref="plays\.html#build"[^>]*>)[^<]*(</a>)', r"\1Stage plays\2")),
    ("drop one data-oos link", "index plays: data-oos set equals plays.html out-of-scope set",
     _on("index", r'<a\b[^>]*\bdata-oos="claude-tag"[^>]*>(.*?)</a>', r"\1")),
    ("add one edge to the figure only", "plays: figure edge set equals the dependency list",
     _on("plays", r"</svg>", '<g data-edge="skills capture-intent helps" stroke-dasharray="4 3">'
         '<line x1="0" y1="0" x2="1" y2="1"/></g></svg>')),
    ("duplicate one glossary term", "plays: glossary has no duplicate term",
     _on("plays", r'(<dt\b[^>]*\bid="term-hook"[^>]*>.*?</dt>)', r"\1\1")),
    ("paste an eight-word source window into plays.html",
     "overlap: plays.html shares no eight-word window with the source", _mut_paste_plays),
    ("append a source window to a play heading",
     "overlap: plays.html shares no eight-word window with the source", _mut_paste_heading),
    ("index.html source window missing from the baseline",
     "overlap: every index.html source match is in the baseline", _mut_unlisted),
    ("add one extra hash to the baseline",
     "overlap: baseline is no larger than the count recorded at 514366c", _mut_extra_hash),
    ("leave a stale hash after its index.html text is removed",
     "overlap: baseline lists no stale hash", _mut_stale),
)


def _run_quiet(inp: dict) -> list[str]:
    global CHECKS, QUIET
    saved = (FAILURES[:], CHECKS, QUIET)
    FAILURES.clear()
    QUIET = True
    try:
        catalogue_checks(inp["index"], inp["plays"], inp["source"], inp["baseline"])
        return FAILURES[:]
    finally:
        FAILURES[:] = saved[0]
        CHECKS, QUIET = saved[1], saved[2]


def run_mutations() -> int:
    """Spec 24: every mutant must turn its named check red. Nothing is written to the tree."""
    inp = {"index": PAGE.read_text(encoding="utf-8"),
           "plays": PLAYS_PAGE.read_text(encoding="utf-8") if PLAYS_PAGE.is_file() else "",
           "source": optional_text(SOURCE_SHINGLES), "baseline": optional_text(OVERLAP_BASELINE)}
    clean = _run_quiet(inp)
    print(f"mutation proof: unmutated catalogue checks fail {len(clean)}")
    killed = 0
    for name, finding, mutate in MUTATIONS:
        mutant = mutate(inp)
        if mutant is None:
            verdict = "BROKEN (anchor missing)"
        elif finding in clean:
            verdict = "INVALID (finding already red unmutated)"
        elif finding in _run_quiet(mutant):
            verdict = "killed"
            killed += 1
        else:
            verdict = "SURVIVED"
        print(f"  {verdict:<40} {name}  [{finding}]")
    print(f"{killed}/{len(MUTATIONS)} mutants killed")
    return 0 if killed == len(MUTATIONS) and not clean else 1


def main() -> int:
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--mutations", action="store_true")
    ap.add_argument("--build-source-shingles", metavar="FILE", type=pathlib.Path)
    ap.add_argument("--fetched", metavar="YYYY-MM-DD")
    ap.add_argument("--build-overlap-baseline", action="store_true")
    args = ap.parse_args()
    if args.build_source_shingles:
        if not args.fetched:
            ap.error("--build-source-shingles needs --fetched")
        return build_source_shingles(args.build_source_shingles, args.fetched)
    if args.build_overlap_baseline:
        return build_overlap_baseline()
    if args.mutations:
        return run_mutations()

    print("portal verification")

    # Absence is a FINDING, not a crash: this is the state the target was written in.
    if not PAGE.is_file():
        check("index.html exists", False, f"not found at {PAGE}")
        print(f"\n{CHECKS} checks, {len(FAILURES)} failed")
        print("FAILED: the page has not been implemented yet")
        return 1

    print(" governance")
    governance_checks()
    print(" privacy")
    privacy_checks()

    raw = PAGE.read_text(encoding="utf-8")
    p = Page()
    p.feed(raw)
    text = p.text
    low = text.casefold()

    print(" structure")
    check("index.html exists", True)
    check("html lang is set", bool(p.lang), f"lang={p.lang!r}")
    check("exactly one h1", p.h1_count == 1, f"found {p.h1_count}")
    check("a main landmark exists", any(t == "main" for t, _ in p.tags))
    check("a nav landmark exists", any(t == "nav" for t, _ in p.tags))
    check("a footer landmark exists", any(t == "footer" for t, _ in p.tags))

    skips = [a["href"][1:] for t, a in p.tags
             if t == "a" and a.get("href", "").startswith("#") and len(a.get("href", "")) > 1]
    check("a skip link points at an existing id",
          any(s in p.ids for s in skips), f"anchors={skips[:4]} ids present={len(p.ids)}")

    tabs = [a for t, a in p.tags if a.get("role") == "tab"]
    panels = [a for t, a in p.tags if a.get("role") == "tabpanel"]
    check("six tabs", len(tabs) == 6, f"found {len(tabs)}")
    check("six tabpanels", len(panels) == 6, f"found {len(panels)}")
    check("a tablist wraps them", any(a.get("role") == "tablist" for _, a in p.tags))

    panel_ids = {a.get("id", "") for a in panels}
    controls = [a.get("aria-controls", "") for a in tabs]
    check("every tab controls a real panel",
          bool(controls) and all(c in panel_ids for c in controls),
          f"controls={controls} panels={sorted(panel_ids)}")
    labelled = [a.get("aria-labelledby", "") for a in panels]
    tab_ids = {a.get("id", "") for a in tabs}
    check("every panel is labelled by its tab",
          bool(labelled) and all(l in tab_ids for l in labelled), f"labelledby={labelled}")
    selected = [a for a in tabs if a.get("aria-selected") == "true"]
    check("exactly one tab is selected", len(selected) == 1, f"found {len(selected)}")
    check("roving tabindex is used",
          any(a.get("tabindex") == "-1" for a in tabs),
          "no tab carries tabindex=-1, so all six are in the tab order")

    print(" isolation")
    srcs = [a["src"] for t, a in p.tags if "src" in a]
    check("no element loads an external src", not srcs, f"src={srcs[:3]}")
    sheets = [a.get("href", "") for t, a in p.tags
              if t == "link" and "stylesheet" in a.get("rel", "").casefold()]
    check("no external stylesheet", not sheets, f"stylesheets={sheets}")
    check("no fetch() call", "fetch(" not in raw)
    check("no XMLHttpRequest", "XMLHttpRequest" not in raw)
    check("no CSS @import", "@import" not in raw)
    ext = [h for h in p.hrefs if h.startswith(("http://", "https://"))]
    bad = [h for h in ext if not re.match(r"https://(claude\.com|github\.com)/", h)]
    check("external links are limited to the two sources", not bad, f"unexpected={bad[:3]}")

    print(" content")
    for name, needle in REQUIRED_TEXT:
        check(f"states {name}", needle.casefold() in low, f"missing {needle!r}")
    check("both unmet adoption positions say not achieved",
          low.count("not achieved") >= 2, f"found {low.count('not achieved')}")
    for name, frag in REQUIRED_LINKS:
        check(f"links the {name}", any(frag in h for h in p.hrefs), f"missing {frag}")
    # Requirement 14: visible early, not buried in the footer.
    head = low[:2200]
    check("the disambiguation appears early, not only in the footer",
          "not the skill's source repository" in head)
    check("a noscript explanation exists for the self-check", p.has_noscript)

    print(" honesty")
    for phrase in FORBIDDEN:
        check(f"avoids overclaim {phrase!r}", phrase not in low)

    print(" responsive")
    compact_svg_px, wide_svg_px = responsive_checks(raw, p)

    print(" learning modes")
    learning_mode_checks(raw, p)

    print(" figures")
    for fig_id, label in (
        ("dg1", "loop"),
        ("dg2", "enforcement"),
        ("dg3", "unbound approval"),
    ):
        figure_checks(raw, fig_id, label, compact_svg_px, wide_svg_px)

    # Truthfulness: the enforcement figure simplifies a ladder, and simplification is where
    # overclaiming hides. The strongest tier is still bypassable by a repository admin, and
    # that fact must survive into the figure rather than being tidied away.
    m2 = re.search(r'<figure[^>]*id="dg2"[^>]*>(.*?)</figure>', raw, re.S)
    fig2 = m2.group(1).casefold() if m2 else ""
    check("enforcement figure keeps the admin bypass on the record",
          "admin" in fig2,
          "the strongest tier leaks to a repository administrator; a figure that omits it "
          "claims more than the honest-limits section does")

    # Every id in the document must be unique, figures included.
    all_ids = re.findall(r'\sid="([^"]+)"', raw)
    dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})
    check("no duplicate id anywhere in the page", not dupes, f"duplicated: {dupes}")

    size = len(raw.encode("utf-8"))
    check(f"page is within the {PAGE_BUDGET:,}-byte budget", size <= PAGE_BUDGET,
          f"page is {size:,} bytes")
    print(f"  (page size = {size:,} bytes of {PAGE_BUDGET:,})")

    stats = catalogue_checks(raw, optional_text(PLAYS_PAGE) or "",
                             optional_text(SOURCE_SHINGLES), optional_text(OVERLAP_BASELINE))
    print(f"  (plays: {stats['plays']} entries; {stats['implemented']} implemented, "
          f"{stats['partial']} partial, {stats[OOS]} out of scope; {stats['edges']} edges, "
          f"{stats['figure_edges']} in figure; {stats['glossary']} glossary terms; "
          f"{stats['size']:,} of {PLAYS_BUDGET:,} bytes)")

    print()
    print(f"{CHECKS} checks, {len(FAILURES)} failed")
    if FAILURES:
        print("FAILED:")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("the portal satisfies its spec")
    return 0


if __name__ == "__main__":
    sys.exit(main())
