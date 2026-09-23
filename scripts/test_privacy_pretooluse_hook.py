#!/usr/bin/env python3
"""Contract tests for the privacy PreToolUse adapter."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOK = ROOT / "scripts" / "privacy_pretooluse_hook.py"


def private_email() -> str:
    return "".join(("learner", chr(64), "private.invalid"))


def write_config(root: pathlib.Path) -> None:
    (root / ".privacy-allowlist.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "allowed_exact": ["Tim WU"],
                "allowed_patterns": [
                    r"^[^@\s]+@users\.noreply\.github\.com$",
                    r"^[^@\s]+@example\.(com|org|net)$",
                ],
                "markers": [],
                "max_text_bytes": 1_000_000,
            }
        ),
        encoding="utf-8",
    )


class PrivacyPreToolUseTests(unittest.TestCase):
    def require_hook(self) -> None:
        self.assertTrue(HOOK.is_file(), "scripts/privacy_pretooluse_hook.py is missing")

    def run_hook(self, event: object, cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
        self.require_hook()
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=event if isinstance(event, str) else json.dumps(event),
            text=True,
            capture_output=True,
            cwd=cwd,
        )

    def event(self, spelling: str, tool_input: object) -> dict[str, object]:
        return {
            "hook_event_name": spelling,
            "tool_name": "write",
            "tool_input": tool_input,
        }

    def repo(self, root: pathlib.Path) -> None:
        (root / ".git").mkdir()
        write_config(root)

    def assert_redacted_block(
        self, proc: subprocess.CompletedProcess[str], value: str
    ) -> None:
        combined = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 2, combined)
        self.assertIn("email", combined)
        self.assertIn("notes.txt", combined)
        self.assertNotIn(value, combined)

    def test_hook_file_exists(self) -> None:
        self.require_hook()

    def test_both_event_name_spellings_block(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            for spelling in ("preToolUse", "PreToolUse"):
                with self.subTest(spelling=spelling):
                    proc = self.run_hook(
                        self.event(spelling, {"path": "notes.txt", "content": value}), root
                    )
                    self.assert_redacted_block(proc, value)

    def test_every_new_content_key_is_scanned(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            for key in ("content", "newStr", "new_str", "text"):
                with self.subTest(key=key):
                    proc = self.run_hook(
                        self.event("preToolUse", {"path": "notes.txt", key: value}), root
                    )
                    self.assert_redacted_block(proc, value)

    def test_nested_multi_operation_payload_is_scanned(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            payload = {
                "operations": [
                    {"path": "safe.txt", "content": "safe"},
                    {"path": "notes.txt", "content": value},
                ]
            }
            self.assert_redacted_block(
                self.run_hook(self.event("preToolUse", payload), root), value
            )

    def test_old_value_can_be_removed(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            proc = self.run_hook(
                self.event(
                    "preToolUse",
                    {"path": "notes.txt", "oldStr": value, "newStr": "redacted"},
                ),
                root,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn(value, proc.stdout + proc.stderr)

    def test_irrelevant_events_and_tools_are_inert(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            cases = (
                {"hook_event_name": "PostToolUse", "tool_name": "write",
                 "tool_input": {"path": "notes.txt", "content": value}},
                {"hook_event_name": "preToolUse", "tool_name": "read",
                 "tool_input": {"path": "notes.txt", "content": value}},
            )
            for event in cases:
                proc = self.run_hook(event, root)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertNotIn(value, proc.stdout + proc.stderr)

    def test_bad_json_and_missing_content_fail_open_without_echo(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.repo(root)
            for event in (
                "{not-json " + value,
                self.event("preToolUse", {"path": "notes.txt"}),
            ):
                proc = self.run_hook(event, root)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertNotIn(value, proc.stdout + proc.stderr)

    def test_write_outside_opted_in_repo_is_inert(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            proc = self.run_hook(
                self.event("preToolUse", {"path": "notes.txt", "content": value}), root
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn(value, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
