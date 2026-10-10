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
ALLOWLIST = ROOT / ".privacy-allowlist.json"
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


# Metadata mutations: (name, exact-once anchor, replacement). Each must fail the unit tests.
METADATA_MUTATIONS = (
    (
        "identity_check_disabled",
        "        findings.update(_identity_findings(short, identity, config))",
        "        pass",
    ),
    (
        "identity_last_commit_only",
        "scan_commit_identities(root, unique, config)",
        "scan_commit_identities(root, unique[-1:], config)",
    ),
    (
        "identity_value_leaked",
        "MetadataFinding(short, field, category,",
        "MetadataFinding(short, field + value, category,",
    ),
    (
        "message_check_disabled",
        "        findings.update(_message_findings(short, message, config))",
        "        pass",
    ),
    (
        "message_trailers_dropped",
        'scan_text(message, "message", config)',
        'scan_text(message.rsplit("\\n\\n", 1)[0], "message", config)',
    ),
    (
        "message_line_leaked",
        'MetadataFinding(short, "message",',
        'MetadataFinding(short, "message" + message.splitlines()[finding.line - 1],',
    ),
)


def run_tests(source: str) -> int:
    """Run the scanner tests against ``source`` in a throwaway tree and return the exit code."""
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        scripts = root / "scripts"
        scripts.mkdir()
        (scripts / "privacy_scan.py").write_text(source, encoding="utf-8")
        shutil.copy2(TEST, scripts / TEST.name)
        shutil.copy2(ALLOWLIST, root / ALLOWLIST.name)
        proc = subprocess.run(
            [sys.executable, str(scripts / TEST.name)],
            cwd=root,
            text=True,
            capture_output=True,
        )
        return proc.returncode


def main() -> int:
    if not SCANNER.is_file():
        print("FAILED: scripts/privacy_scan.py has not been implemented")
        return 1
    source = SCANNER.read_text(encoding="utf-8")
    # A mutant only counts as killed if the unmutated copy passes in the same throwaway tree;
    # otherwise every mutant would be "killed" by the environment rather than by a test.
    if run_tests(source):
        print("FAILED: unmutated scanner does not pass its tests in the proof tree")
        return 1
    mutations = [
        (category, f'        ("{category}", _scan_{category}),', "") for category in CATEGORIES
    ]
    mutations.extend(METADATA_MUTATIONS)
    results: list[tuple[str, str]] = []
    for name, anchor, replacement in mutations:
        if source.count(anchor) != 1:
            results.append((name, "broken"))
            continue
        code = run_tests(source.replace(anchor, replacement, 1))
        results.append((name, "killed" if code else "survived"))
    for name, state in results:
        print(f"{name}: {state}")
    killed = sum(state == "killed" for _, state in results)
    survived = sum(state == "survived" for _, state in results)
    broken = sum(state == "broken" for _, state in results)
    print(f"{killed} killed, {survived} survived, {broken} broken")
    return 0 if killed == len(mutations) and not survived and not broken else 1

if __name__ == "__main__":
    raise SystemExit(main())
