#!/usr/bin/env python3
"""Prove each privacy detection category is required by the scanner tests."""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "privacy_scan.py"
TEST = ROOT / "scripts" / "test_privacy_scan.py"
CATEGORIES = (
    "developer_home",
    "configured_marker",
    "email",
    "phone",
    "payment_card",
    "private_key",
    "bearer_token",
    "aws_key",
    "github_token",
    "slack_token",
)


def main() -> int:
    if not SCANNER.is_file():
        print("FAILED: scripts/privacy_scan.py has not been implemented")
        return 1
    source = SCANNER.read_text(encoding="utf-8")
    results: list[tuple[str, str]] = []
    for category in CATEGORIES:
        anchor = f'        ("{category}", _scan_{category}),' 
        if source.count(anchor) != 1:
            results.append((category, "broken"))
            continue
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "privacy_scan.py").write_text(
                source.replace(anchor, "", 1), encoding="utf-8"
            )
            shutil.copy2(TEST, scripts / TEST.name)
            proc = subprocess.run(
                [sys.executable, str(scripts / TEST.name)],
                cwd=root,
                text=True,
                capture_output=True,
            )
            results.append((category, "killed" if proc.returncode else "survived"))
    for category, state in results:
        print(f"{category}: {state}")
    killed = sum(state == "killed" for _, state in results)
    survived = sum(state == "survived" for _, state in results)
    broken = sum(state == "broken" for _, state in results)
    print(f"{killed} killed, {survived} survived, {broken} broken")
    return 0 if killed == len(CATEGORIES) and not survived and not broken else 1


if __name__ == "__main__":
    raise SystemExit(main())
