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

import pathlib
import re
import sys
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
PAGE = HERE / "index.html"

FAILURES: list[str] = []
CHECKS = 0

# Spec requirement 7. The page was 44,972 bytes before the figures; three inline SVGs at
# roughly 4-5 KB each land near 58 KB. The ceiling is deliberately close: a fourth figure
# would not fit, which is one of the reasons the spec ships three.
PAGE_BUDGET = 75_000

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


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{(' — ' + detail) if detail else ''}")
        FAILURES.append(name)


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
    ):
        check(f"README privacy: {label}", needle in readme)

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
    check("hero spacing is fluid", bool(re.search(r"\.hero\{[^}]*padding:clamp\(", html)))
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
    old_figure = re.search(r"figure\.dg\{[^}]*border:(\d+)px[^}]*padding:(\d+)px", html)
    gutter = values["page-gutter"] if values["page-gutter"] else (
        float(old_wrap.group(1)) if old_wrap else 0.0
    )
    border = float(old_figure.group(1)) if old_figure else 0.0
    figure_padding = values["figure-padding"] if values["figure-padding"] else (
        float(old_figure.group(2)) if old_figure else 0.0
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


def main() -> int:
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
