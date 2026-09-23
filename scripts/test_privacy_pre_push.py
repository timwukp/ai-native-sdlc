#!/usr/bin/env python3
"""Integration contracts for outgoing-commit scanning and hook installation."""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "privacy_scan.py"
HOOK = ROOT / ".githooks" / "pre-push"
INSTALLER = ROOT / "scripts" / "install_privacy_hooks.sh"
ZERO = "0" * 40


def private_email() -> str:
    return "".join(("learner", chr(64), "private.invalid"))


def config_text() -> str:
    return json.dumps(
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
    )


class PrivacyPrePushTests(unittest.TestCase):
    def require_files(self) -> None:
        for path in (SCANNER, HOOK, INSTALLER):
            self.assertTrue(path.is_file(), f"{path.relative_to(ROOT)} is missing")

    def run_cmd(self, cwd: pathlib.Path, *args: str, input_text: str = "", check: bool = True):
        proc = subprocess.run(
            list(args), cwd=cwd, input=input_text, text=True, capture_output=True
        )
        if check and proc.returncode:
            self.fail(f"command failed ({proc.returncode}): {' '.join(args)}\n{proc.stderr}")
        return proc

    def git(self, cwd: pathlib.Path, *args: str) -> str:
        return self.run_cmd(cwd, "git", *args).stdout.strip()

    def prepare(self, base: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
        self.require_files()
        remote = base / "remote.git"
        repo = base / "repo"
        self.run_cmd(base, "git", "init", "--bare", "-q", str(remote))
        self.run_cmd(base, "git", "init", "-q", str(repo))
        self.git(repo, "config", "user.name", "Privacy Test")
        self.git(repo, "config", "user.email", "privacy-test@example.com")
        self.git(repo, "remote", "add", "origin", str(remote))
        (repo / "scripts").mkdir()
        (repo / ".githooks").mkdir()
        shutil.copy2(SCANNER, repo / "scripts" / SCANNER.name)
        shutil.copy2(INSTALLER, repo / "scripts" / INSTALLER.name)
        shutil.copy2(HOOK, repo / ".githooks" / HOOK.name)
        os.chmod(repo / ".githooks" / HOOK.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        os.chmod(repo / "scripts" / INSTALLER.name, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        (repo / ".privacy-allowlist.json").write_text(config_text(), encoding="utf-8")
        (repo / "safe.txt").write_text("safe\n", encoding="utf-8")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "initial")
        self.git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        return repo, remote

    def invoke_hook(
        self, repo: pathlib.Path, local_ref: str, local_sha: str, remote_ref: str,
        remote_sha: str
    ) -> subprocess.CompletedProcess[str]:
        line = f"{local_ref} {local_sha} {remote_ref} {remote_sha}\n"
        return self.run_cmd(
            repo, "/bin/sh", str(repo / ".githooks" / "pre-push"), "origin",
            str(repo.parent / "remote.git"), input_text=line, check=False
        )

    def assert_blocked_without_value(
        self, proc: subprocess.CompletedProcess[str], value: str
    ) -> None:
        combined = proc.stdout + proc.stderr
        self.assertNotEqual(proc.returncode, 0, combined)
        self.assertIn("email", combined)
        self.assertNotIn(value, combined)

    def test_existing_branch_scans_outgoing_commit(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            remote_sha = self.git(repo, "rev-parse", "HEAD")
            (repo / "notes.txt").write_text(value, encoding="utf-8")
            self.git(repo, "add", "notes.txt")
            self.git(repo, "commit", "-qm", "sensitive")
            local_sha = self.git(repo, "rev-parse", "HEAD")
            self.assert_blocked_without_value(
                self.invoke_hook(repo, "refs/heads/main", local_sha,
                                 "refs/heads/main", remote_sha), value
            )

    def test_new_branch_scans_unpublished_commits(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            self.git(repo, "switch", "-qc", "feature")
            (repo / "notes.txt").write_text(value, encoding="utf-8")
            self.git(repo, "add", "notes.txt")
            self.git(repo, "commit", "-qm", "sensitive")
            local_sha = self.git(repo, "rev-parse", "HEAD")
            self.assert_blocked_without_value(
                self.invoke_hook(repo, "refs/heads/feature", local_sha,
                                 "refs/heads/feature", ZERO), value
            )

    def test_add_then_remove_is_still_blocked(self) -> None:
        value = private_email()
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            remote_sha = self.git(repo, "rev-parse", "HEAD")
            (repo / "notes.txt").write_text(value, encoding="utf-8")
            self.git(repo, "add", "notes.txt")
            self.git(repo, "commit", "-qm", "add")
            (repo / "notes.txt").write_text("redacted\n", encoding="utf-8")
            self.git(repo, "add", "notes.txt")
            self.git(repo, "commit", "-qm", "remove")
            local_sha = self.git(repo, "rev-parse", "HEAD")
            self.assert_blocked_without_value(
                self.invoke_hook(repo, "refs/heads/main", local_sha,
                                 "refs/heads/main", remote_sha), value
            )

    def test_deleting_remote_ref_scans_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            remote_sha = self.git(repo, "rev-parse", "HEAD")
            proc = self.invoke_hook(repo, "(delete)", ZERO, "refs/heads/main", remote_sha)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_installer_sets_local_hooks_path_and_hook_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            proc = self.run_cmd(repo, "/bin/sh", "scripts/install_privacy_hooks.sh", check=False)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(self.git(repo, "config", "--local", "--get", "core.hooksPath"),
                             ".githooks")

    def test_installer_refuses_existing_hooks_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            self.git(repo, "config", "--local", "core.hooksPath", "other-hooks")
            proc = self.run_cmd(repo, "/bin/sh", "scripts/install_privacy_hooks.sh", check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(self.git(repo, "config", "--local", "--get", "core.hooksPath"),
                             "other-hooks")

    def test_installer_refuses_active_legacy_pre_push(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo, _ = self.prepare(pathlib.Path(td))
            legacy = repo / ".git" / "hooks" / "pre-push"
            legacy.parent.mkdir(parents=True, exist_ok=True)
            legacy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            legacy.chmod(0o755)
            proc = self.run_cmd(repo, "/bin/sh", "scripts/install_privacy_hooks.sh", check=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(
                self.run_cmd(repo, "git", "config", "--local", "--get", "core.hooksPath",
                         check=False).returncode,
                1,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
