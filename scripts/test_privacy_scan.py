#!/usr/bin/env python3
"""Contract tests for the deterministic privacy scanner."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCANNER = ROOT / "scripts" / "privacy_scan.py"
LOAD_ERROR = ""


def load_scanner():
    global LOAD_ERROR
    if not SCANNER.is_file():
        LOAD_ERROR = "scripts/privacy_scan.py has not been implemented"
        return None
    try:
        spec = importlib.util.spec_from_file_location("privacy_scan_under_test", SCANNER)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not create module spec")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except Exception as exc:  # converted to a named test failure, not an import traceback
        LOAD_ERROR = f"privacy scanner could not load: {type(exc).__name__}"
        return None


SCANNER_MODULE = load_scanner()


def synthetic_values() -> dict[str, str]:
    at = chr(64)
    return {
        "developer_home": "/".join(("", "home", "pii-test-user", "project", "file.txt")),
        "configured_marker": "".join(("synthetic", "-host-marker")),
        "email": "".join(("learner", at, "private.invalid")),
        "phone": "".join(("phone: +1 ", "202 ", "555 ", "0147")),
        "payment_card": "".join(("4111", "1111", "1111", "1111")),
        "private_key": "".join(("-----BEGIN ", "PRIVATE KEY-----")),
        "bearer_token": "".join(("Bearer ", "synthetic", "-credential-value-123456")),
        "aws_key": "".join(("AK", "IA", "A" * 16)),
        "github_token": "".join(("gh", "p_", "a" * 36)),
        "slack_token": "".join(("xo", "xb-", "1111111111-", "2222222222-", "a" * 24)),
    }


def config_document(**overrides) -> dict[str, object]:
    data: dict[str, object] = {
        "schema_version": 1,
        "allowed_exact": ["Tim WU"],
        "allowed_patterns": [
            r"^[^@\s]+@users\.noreply\.github\.com$",
            r"^[^@\s]+@example\.(com|org|net)$",
        ],
        "markers": ["synthetic-host-marker"],
        "max_text_bytes": 1_000_000,
    }
    data.update(overrides)
    return data


class PrivacyScannerTests(unittest.TestCase):
    def scanner(self):
        if SCANNER_MODULE is None:
            self.fail(LOAD_ERROR)
        return SCANNER_MODULE

    def write_config(self, root: pathlib.Path, **overrides):
        path = root / ".privacy-allowlist.json"
        path.write_text(json.dumps(config_document(**overrides)), encoding="utf-8")
        return self.scanner().load_config(path)

    def git(self, root: pathlib.Path, *args: str) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True, check=True
        )
        return proc.stdout.strip()

    def init_repo(self, root: pathlib.Path) -> None:
        self.git(root, "init", "-q")
        self.git(root, "config", "user.name", "Privacy Test")
        self.git(root, "config", "user.email", "privacy-test@example.com")

    def test_scanner_module_exists(self) -> None:
        self.assertIsNotNone(SCANNER_MODULE, LOAD_ERROR)

    def test_every_supported_category_is_detected(self) -> None:
        scanner = self.scanner()
        with tempfile.TemporaryDirectory() as td:
            config = self.write_config(pathlib.Path(td))
            for expected, value in synthetic_values().items():
                with self.subTest(category=expected):
                    findings = scanner.scan_text(value, "sample.txt", config)
                    self.assertIn(expected, {finding.category for finding in findings})

    def test_luhn_rejects_same_length_invalid_number(self) -> None:
        scanner = self.scanner()
        valid = synthetic_values()["payment_card"]
        invalid = valid[:-1] + ("2" if valid[-1] != "2" else "3")
        self.assertTrue(scanner.luhn_valid(valid))
        self.assertFalse(scanner.luhn_valid(invalid))

    def test_phone_requires_an_explicit_label(self) -> None:
        scanner = self.scanner()
        with tempfile.TemporaryDirectory() as td:
            config = self.write_config(pathlib.Path(td))
            labeled = synthetic_values()["phone"]
            unlabeled = labeled.split(": ", 1)[1]
            self.assertIn("phone", {f.category for f in scanner.scan_text(labeled, "x", config)})
            self.assertNotIn(
                "phone", {f.category for f in scanner.scan_text(unlabeled, "x", config)}
            )

    def test_public_noreply_and_reserved_examples_are_allowed(self) -> None:
        scanner = self.scanner()
        at = chr(64)
        with tempfile.TemporaryDirectory() as td:
            config = self.write_config(pathlib.Path(td))
            for value in (
                "".join(("8848995+timwukp", at, "users.noreply.github.com")),
                "".join(("learner", at, "example.com")),
            ):
                self.assertNotIn(
                    "email", {f.category for f in scanner.scan_text(value, "x", config)}
                )

    def test_findings_and_rendering_never_carry_the_match(self) -> None:
        scanner = self.scanner()
        value = synthetic_values()["email"]
        with tempfile.TemporaryDirectory() as td:
            config = self.write_config(pathlib.Path(td))
            findings = scanner.scan_text(value, "lesson.txt", config)
            self.assertTrue(findings)
            for finding in findings:
                self.assertNotIn("value", vars(finding))
                self.assertNotIn("match", vars(finding))
                self.assertNotIn(value, repr(finding))
            rendered = scanner.format_findings(findings)
            self.assertIn("email", rendered)
            self.assertIn("lesson.txt", rendered)
            self.assertNotIn(value, rendered)

    def test_config_rejects_unknown_broad_duplicate_and_unanchored_entries(self) -> None:
        scanner = self.scanner()
        cases = (
            {"unknown": True},
            {"allowed_patterns": ["private.invalid"]},
            {"allowed_exact": ["same", "same"]},
            {"schema_version": 2},
            {"skip_directories": ["intent"]},
        )
        for override in cases:
            with self.subTest(override=tuple(override)):
                with tempfile.TemporaryDirectory() as td:
                    root = pathlib.Path(td)
                    path = root / ".privacy-allowlist.json"
                    path.write_text(json.dumps(config_document(**override)), encoding="utf-8")
                    with self.assertRaises(scanner.ConfigError):
                        scanner.load_config(path)

    def test_scan_repository_reads_tracked_files_only_and_counts_binary(self) -> None:
        scanner = self.scanner()
        private_email = synthetic_values()["email"]
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.init_repo(root)
            config = self.write_config(root)
            (root / "tracked.txt").write_text(private_email, encoding="utf-8")
            (root / "untracked.txt").write_text(private_email, encoding="utf-8")
            (root / "binary.dat").write_bytes(b"\x00" + private_email.encode())
            self.git(root, "add", ".privacy-allowlist.json", "tracked.txt", "binary.dat")
            result = scanner.scan_repository(root, config)
            self.assertEqual([f.path for f in result.findings], ["tracked.txt"])
            self.assertEqual(result.skipped_binary, 1)
            self.assertGreaterEqual(result.scanned_files, 2)

    def test_external_symlink_is_not_followed(self) -> None:
        scanner = self.scanner()
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
            root = pathlib.Path(td)
            outside = pathlib.Path(outside_td) / "outside.txt"
            outside.write_text(synthetic_values()["email"], encoding="utf-8")
            self.init_repo(root)
            config = self.write_config(root)
            (root / "external-link").symlink_to(outside)
            self.git(root, "add", ".privacy-allowlist.json", "external-link")
            result = scanner.scan_repository(root, config)
            self.assertEqual(result.findings, ())

    def test_invalid_nonbinary_utf8_fails_closed(self) -> None:
        scanner = self.scanner()
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.init_repo(root)
            config = self.write_config(root)
            (root / "bad.txt").write_bytes(b"\xff\xfeplain")
            self.git(root, "add", ".privacy-allowlist.json", "bad.txt")
            with self.assertRaises(scanner.ScanError):
                scanner.scan_repository(root, config)

    def test_findings_are_stably_sorted(self) -> None:
        scanner = self.scanner()
        values = synthetic_values()
        with tempfile.TemporaryDirectory() as td:
            config = self.write_config(pathlib.Path(td))
            text = "\n".join((values["email"], values["private_key"]))
            findings = scanner.scan_text(text, "z.txt", config)
            keys = [(f.path, f.line, f.category) for f in findings]
            self.assertEqual(keys, sorted(keys))

    def test_cli_redacts_a_finding_and_uses_exit_one(self) -> None:
        self.scanner()
        value = synthetic_values()["email"]
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            self.init_repo(root)
            (root / ".privacy-allowlist.json").write_text(
                json.dumps(config_document()), encoding="utf-8"
            )
            (root / "tracked.txt").write_text(value, encoding="utf-8")
            self.git(root, "add", ".privacy-allowlist.json", "tracked.txt")
            proc = subprocess.run(
                [sys.executable, str(SCANNER), "--repo", str(root)],
                text=True,
                capture_output=True,
            )
            combined = proc.stdout + proc.stderr
            self.assertEqual(proc.returncode, 1, combined)
            self.assertIn("email", combined)
            self.assertIn("tracked.txt", combined)
            self.assertNotIn(value, combined)


if __name__ == "__main__":
    unittest.main(verbosity=2)
