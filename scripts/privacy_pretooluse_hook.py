#!/usr/bin/env python3
"""Kiro PreToolUse adapter for the shared privacy scanner."""

from __future__ import annotations

import json
import os
import pathlib
import sys
from typing import Iterable, Optional

WRITE_TOOL_HINTS = ("write", "edit", "creating", "editing", "str_replace", "insert")
NEW_TEXT_KEYS = ("content", "newStr", "new_str", "text")
OLD_TEXT_KEYS = ("oldStr", "old_str")
PATH_KEYS = ("path", "file_path", "filePath")


def _allow(message: str = "") -> int:
    if message:
        print(message, file=sys.stderr)
    return 0


def _repo_root(start: pathlib.Path) -> Optional[pathlib.Path]:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists() and (candidate / ".privacy-allowlist.json").is_file():
            return candidate.resolve()
    return None


def _extract_new_text(value: object, inherited_path: str = "") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        local_path = inherited_path
        for key in PATH_KEYS:
            candidate = value.get(key)
            if isinstance(candidate, str):
                local_path = candidate
                break
        for key, child in value.items():
            if key in OLD_TEXT_KEYS:
                continue
            if key in NEW_TEXT_KEYS and isinstance(child, str):
                found.append((local_path, child))
            elif key not in PATH_KEYS:
                found.extend(_extract_new_text(child, local_path))
    elif isinstance(value, (list, tuple)):
        for child in value:
            found.extend(_extract_new_text(child, inherited_path))
    return found


def _relative_path(root: pathlib.Path, cwd: pathlib.Path, raw_path: str) -> Optional[str]:
    if not raw_path:
        return "<proposed-content>"
    target = pathlib.Path(raw_path)
    absolute = target if target.is_absolute() else cwd / target
    try:
        return str(absolute.resolve().relative_to(root))
    except ValueError:
        return None


def _load_scanner():
    try:
        import privacy_scan
        return privacy_scan
    except Exception:
        return None


def main() -> int:
    raw = sys.stdin.read() or "{}"
    try:
        event = json.loads(raw)
    except Exception:
        return _allow("privacy hook unavailable: invalid event; allowing write")
    if not isinstance(event, dict):
        return _allow()
    if str(event.get("hook_event_name") or "").casefold() != "pretooluse":
        return _allow()
    tool_name = str(event.get("tool_name") or "").casefold()
    if not any(hint in tool_name for hint in WRITE_TOOL_HINTS):
        return _allow()

    cwd = pathlib.Path(str(event.get("cwd") or os.getcwd())).resolve()
    root = _repo_root(cwd)
    if root is None:
        return _allow()
    proposed = _extract_new_text(event.get("tool_input"))
    if not proposed:
        return _allow()

    scanner = _load_scanner()
    if scanner is None:
        return _allow("privacy hook unavailable: scanner could not load; allowing write")
    try:
        config = scanner.load_config(root / ".privacy-allowlist.json")
        findings = set()
        for raw_path, text in proposed:
            relative = _relative_path(root, cwd, raw_path)
            if relative is None:
                continue
            findings.update(scanner.scan_text(text, relative, config))
        if findings:
            print("PRIVACY HOOK BLOCKED", file=sys.stderr)
            print(scanner.format_findings(findings), file=sys.stderr)
            return 2
        return 0
    except Exception:
        return _allow("privacy hook unavailable: internal error; allowing write")


if __name__ == "__main__":
    raise SystemExit(main())
