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
