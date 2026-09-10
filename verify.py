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


def figure_checks(html: str, fig_id: str, label: str, content_px: int) -> None:
    """Verify one inline SVG figure.

    Takes fig_id so a failure names WHICH figure — three copy-pasted blocks would drift as
    the checks grow, and an unattributed "effective font too small" tells the reader nothing.
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

    # --- legibility, by the spec's formula rather than by eye --------------------
    vb = re.search(r'viewBox="\s*[\d.]+\s+[\d.]+\s+([\d.]+)\s+([\d.]+)\s*"', root)
    fonts = [float(f) for f in re.findall(r'font-size="([\d.]+)"', fig)]
    if not vb or not fonts:
        check(f"{label}: has a viewBox and sized text", False,
              "cannot compute legibility without both a viewBox width and a font-size")
    else:
        vb_w = float(vb.group(1))
        eff = min(fonts) * content_px / vb_w
        check(
            f"{label}: effective font >= 12px at {content_px}px content",
            eff >= 12.0,
            f"min font {min(fonts)}px over viewBox width {vb_w} renders at {eff:.2f}px; "
            f"either narrow the canvas or raise the type",
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


def main() -> int:
    print("portal verification")

    # Absence is a FINDING, not a crash: this is the state the target was written in.
    if not PAGE.is_file():
        check("index.html exists", False, f"not found at {PAGE}")
        print(f"\n{CHECKS} checks, {len(FAILURES)} failed")
        print("FAILED: the page has not been implemented yet")
        return 1

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

    print(" figures")
    # The divisor is the CONTENT width, not the viewport. .wrap has horizontal padding, so
    # a 360px viewport gives less than 360px to the figure, and measuring against the
    # viewport is what made a draft look like it passed at 12.0px when it renders at 10.7px.
    # Read the padding out of the stylesheet rather than hard-coding it, so a future CSS
    # change fails this check instead of silently invalidating every figure.
    pad = re.search(r"\.wrap\{[^}]*padding:\s*0\s+(\d+)px", raw)
    check("the .wrap padding is readable from the stylesheet", pad is not None,
          "without it the legibility divisor would be a guess")
    content_px = 360 - 2 * int(pad.group(1)) if pad else 360
    print(f"  (mobile content width = 360 - 2x{pad.group(1) if pad else '?'} = {content_px}px)")

    for fig_id, label in (
        ("dg1", "loop"),
        ("dg2", "enforcement"),
        ("dg3", "unbound approval"),
    ):
        figure_checks(raw, fig_id, label, content_px)

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
