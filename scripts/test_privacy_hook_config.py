#!/usr/bin/env python3
"""Contract tests for the checked-in Kiro privacy hook configuration."""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".kiro" / "hooks" / "privacy-scan.json"
SCANNER = ROOT / "scripts" / "privacy_scan.py"
ADAPTER = ROOT / "scripts" / "privacy_pretooluse_hook.py"


def private_email() -> str:
    return "".join(("learner", chr(64), "private.invalid"))


class PrivacyHookConfigTests(unittest.TestCase):
    def load_config(self) -> dict[str, object]:
        self.assertTrue(CONFIG.is_file(), ".kiro/hooks/privacy-scan.json is missing")
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception as exc:
            self.fail(f"privacy hook JSON is invalid: {type(exc).__name__}")

    def action(self) -> dict[str, object]:
        data = self.load_config()
        hooks = data.get("hooks")
        self.assertIsInstance(hooks, list)
        self.assertEqual(len(hooks), 1)
        return hooks[0]

    def test_official_kiro_shape(self) -> None:
        data = self.load_config()
        hook = self.action()
        self.assertEqual(data.get("version"), "v1")
        self.assertEqual(hook.get("trigger"), "PreToolUse")
        self.assertEqual(hook.get("matcher"), "write")
        self.assertEqual(hook.get("timeout"), 15)
        self.assertIs(hook.get("enabled"), True)
        self.assertEqual(hook.get("action", {}).get("type"), "command")

    def test_command_guards_python_and_checked_in_adapter(self) -> None:
        command = str(self.action().get("action", {}).get("command", ""))
        self.assertIn("command -v python3", command)
        self.assertIn("scripts/privacy_pretooluse_hook.py", command)
        self.assertIn("exit 0", command)
        self.assertIn("exec python3", command)

    def test_shipped_command_blocks_and_redacts_in_a_hermetic_repo(self) -> None:
        self.assertTrue(SCANNER.is_file(), "scripts/privacy_scan.py is missing")
        self.assertTrue(ADAPTER.is_file(), "scripts/privacy_pretooluse_hook.py is missing")
        command = str(self.action().get("action", {}).get("command", ""))
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            (root / ".git").mkdir()
            (root / "scripts").mkdir()
            shutil.copy2(SCANNER, root / "scripts" / SCANNER.name)
            shutil.copy2(ADAPTER, root / "scripts" / ADAPTER.name)
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
            event = json.dumps(
                {
                    "hook_event_name": "preToolUse",
                    "tool_name": "write",
                    "tool_input": {"path": "notes.txt", "content": value},
                }
            )
            proc = subprocess.run(
                command,
                shell=True,
                cwd=root,
                input=event,
                text=True,
                capture_output=True,
                executable="/bin/sh",
            )
            combined = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 2, combined)
            self.assertIn("email", combined)
            self.assertNotIn(value, combined)

    def test_shipped_command_self_disables_when_adapter_is_missing(self) -> None:
        command = str(self.action().get("action", {}).get("command", ""))
        with tempfile.TemporaryDirectory() as td:
            proc = subprocess.run(
                command,
                shell=True,
                cwd=td,
                input="{}",
                text=True,
                capture_output=True,
                executable="/bin/sh",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
