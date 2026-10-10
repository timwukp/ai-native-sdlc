#!/usr/bin/env python3
"""Contract tests for the deterministic privacy scanner."""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from typing import Optional

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


def identities() -> dict[str, str]:
    """Synthetic commit identities, assembled at runtime so no literal address is committed."""
    at = chr(64)
    return {
        "noreply": "".join(("8848995+timwukp", at, "users.noreply.github.com")),
        "web_flow": "".join(("noreply", at, "github.com")),
        "other_github": "".join(("someone", at, "github.com")),
        "private": "".join(("learner", at, "private.invalid")),
        "internal_host": "".join(("builder", at, "ip-192-0-2-1.compute.internal")),
    }


def redaction_parts(value: str) -> tuple[str, str, str]:
    local, domain = value.split(chr(64), 1)
    return value, local, domain


class CommitRepoCase(unittest.TestCase):
    """A throwaway repository isolated from the host's Git configuration."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.base = pathlib.Path(self._td.name)
        empty = self.base / "empty-gitconfig"
        empty.write_text("", encoding="utf-8")
        # Isolate from the host's identity, hooks and defaults.
        self.env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        self.env.update(
            GIT_CONFIG_GLOBAL=str(empty), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_SYSTEM=str(empty)
        )
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        ids = identities()
        (self.repo / ".privacy-allowlist.json").write_text(
            json.dumps(config_document(allowed_exact=["Tim WU", ids["web_flow"]])),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._td.cleanup()

    def scanner(self):
        if SCANNER_MODULE is None:
            self.fail(LOAD_ERROR)
        return SCANNER_MODULE

    def config(self):
        return self.scanner().load_config(self.repo / ".privacy-allowlist.json")

    def git(self, *args: str, input_text: Optional[str] = None, extra=None) -> str:
        env = dict(self.env)
        env.update(extra or {})
        proc = subprocess.run(
            ["git", *args], cwd=self.repo, text=True, capture_output=True, env=env,
            input=input_text,
        )
        if proc.returncode:
            self.fail(f"git {' '.join(args[:2])} failed: {proc.stderr}")
        return proc.stdout.strip()

    def commit(self, author_email: str, committer_email: Optional[str] = None,
               author_name: str = "Tim WU", committer_name: str = "Tim WU") -> str:
        self.git(
            "commit", "-q", "--allow-empty", "-m", "synthetic",
            extra={
                "GIT_AUTHOR_NAME": author_name,
                "GIT_AUTHOR_EMAIL": author_email,
                "GIT_COMMITTER_NAME": committer_name,
                "GIT_COMMITTER_EMAIL": committer_email or identities()["noreply"],
            },
        )
        return self.git("rev-parse", "HEAD")

    def keys(self, findings) -> set[tuple[str, str, str]]:
        return {(f.commit, f.field, f.category) for f in findings}

    def check(self, commits: list[str]):
        return self.scanner().scan_commit_identities(self.repo, commits, self.config())

    def run_cli(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCANNER), "--repo", str(self.repo), *args],
            text=True, capture_output=True, env=self.env, input=stdin,
        )

    def assert_redacted(self, text: str, value: str) -> None:
        for part in redaction_parts(value):
            self.assertNotIn(part, text)


class PrivacyMetadataTests(CommitRepoCase):
    """Commit identity metadata: the second published surface."""

    def test_untrusted_author_email_is_a_finding(self) -> None:
        sha = self.commit(identities()["private"])
        findings, checked = self.check([sha])
        self.assertEqual(self.keys(findings), {(sha[:12], "author-email", "commit_email")})
        self.assertEqual(checked, 1)

    def test_untrusted_committer_email_is_a_finding(self) -> None:
        ids = identities()
        sha = self.commit(ids["noreply"], ids["private"])
        findings, _ = self.check([sha])
        self.assertEqual(self.keys(findings), {(sha[:12], "committer-email", "commit_email")})

    def test_internal_host_shaped_email_is_a_finding(self) -> None:
        sha = self.commit(identities()["internal_host"])
        findings, _ = self.check([sha])
        self.assertEqual(self.keys(findings), {(sha[:12], "author-email", "commit_email")})

    def test_noreply_and_web_flow_identities_are_allowed(self) -> None:
        ids = identities()
        first = self.commit(ids["noreply"])
        second = self.commit(ids["noreply"], ids["web_flow"])
        findings, checked = self.check([first, second])
        self.assertEqual(findings, ())
        self.assertEqual(checked, 2)

    def test_repository_allowlist_admits_web_flow_exactly(self) -> None:
        ids = identities()
        config = self.scanner().load_config(ROOT / ".privacy-allowlist.json")
        sha = self.commit(ids["noreply"], ids["web_flow"])
        findings, _ = self.scanner().scan_commit_identities(self.repo, [sha], config)
        self.assertEqual(findings, ())
        other = self.commit(ids["other_github"])
        findings, _ = self.scanner().scan_commit_identities(self.repo, [other], config)
        self.assertEqual(self.keys(findings), {(other[:12], "author-email", "commit_email")})

    def test_developer_home_in_a_name_is_a_finding(self) -> None:
        name = "Dev " + "/".join(("", "home", "pii-test-user", ""))
        sha = self.commit(identities()["noreply"], author_name=name)
        findings, _ = self.check([sha])
        self.assertEqual(self.keys(findings), {(sha[:12], "author-name", "developer_home")})

    def test_plain_names_are_not_findings(self) -> None:
        sha = self.commit(identities()["noreply"], author_name="Ada Example")
        findings, _ = self.check([sha])
        self.assertEqual(findings, ())

    def test_earlier_commit_is_reported_once_per_field(self) -> None:
        ids = identities()
        first = self.commit(ids["private"], ids["private"])
        second = self.commit(ids["noreply"])
        third = self.commit(ids["noreply"])
        findings, checked = self.check([first, second, third, first])
        self.assertEqual(
            sorted(self.keys(findings)),
            [(first[:12], "author-email", "commit_email"),
             (first[:12], "committer-email", "commit_email")],
        )
        self.assertEqual(len(findings), 2)
        self.assertEqual(checked, 3)

    def test_pre_push_checks_every_outgoing_commit_identity(self) -> None:
        ids = identities()
        (self.repo / "safe.txt").write_text("safe\n", encoding="utf-8")
        self.git("add", ".")
        base = self.commit(ids["noreply"])
        bad = self.commit(ids["private"])
        self.commit(ids["noreply"])
        tip = self.commit(ids["noreply"])
        updates = f"refs/heads/main {tip} refs/heads/main {base}\n"
        result = self.scanner().scan_pre_push(self.repo, "origin", updates, self.config())
        self.assertEqual(
            self.keys(result.metadata_findings), {(bad[:12], "author-email", "commit_email")}
        )
        self.assertEqual(result.identities_checked, 3)

    def write_raw_commit(self, body: str) -> str:
        tree = self.git("mktree", input_text="")
        return self.git(
            "hash-object", "-t", "commit", "-w", "--literally", "--stdin",
            input_text=body.replace("TREE", tree),
        )

    def test_malformed_commit_objects_fail_closed(self) -> None:
        noreply = identities()["noreply"]
        person = f"Tim WU <{noreply}> 1700000000 +0000"
        cases = {
            "missing committer": f"tree TREE\nauthor {person}\n\nmsg\n",
            "duplicate author": f"tree TREE\nauthor {person}\nauthor {person}\n"
                                f"committer {person}\n\nmsg\n",
            "unparseable author": f"tree TREE\nauthor Tim WU {noreply}\n"
                                  f"committer {person}\n\nmsg\n",
        }
        for label, body in cases.items():
            with self.subTest(case=label):
                sha = self.write_raw_commit(body)
                with self.assertRaises(self.scanner().ScanError) as caught:
                    self.check([sha])
                self.assert_redacted(str(caught.exception), noreply)

    def test_unknown_commit_fails_closed(self) -> None:
        with self.assertRaises(self.scanner().ScanError):
            self.check(["1" * 40])

    def test_commit_range_checks_only_the_range_and_redacts(self) -> None:
        ids = identities()
        value = ids["private"]
        base = self.commit(value)
        head = self.commit(ids["noreply"], value)
        proc = self.run_cli("--commit-range", base, head)
        combined = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, combined)
        self.assertIn("category=commit_email", combined)
        self.assertIn(f"commit={head[:12]}", combined)
        self.assertIn("field=committer-email", combined)
        self.assertNotIn("field=author-email", combined)
        self.assertNotIn(base[:12], combined)
        self.assertIn("1 commits checked (identity and message)", combined)
        self.assert_redacted(combined, value)

    def test_commit_range_rejects_bad_arguments(self) -> None:
        sha = self.commit(identities()["noreply"])
        for args in (
            ("--commit-range", sha[:12], sha),
            ("--commit-range", sha, "HEAD"),
            ("--commit-range", sha, sha, "--pre-push", "--remote", "origin"),
        ):
            with self.subTest(args=args[1:3]):
                self.assertEqual(self.run_cli(*args).returncode, 2)

    def test_commit_range_with_no_new_commits_passes(self) -> None:
        sha = self.commit(identities()["noreply"])
        proc = self.run_cli("--commit-range", sha, sha)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("0 commits checked (identity and message)", proc.stdout)

    def test_metadata_findings_never_carry_the_value(self) -> None:
        value = identities()["private"]
        sha = self.commit(value)
        findings, _ = self.check([sha])
        self.assertTrue(findings)
        rendered = self.scanner().format_findings(findings)
        self.assertIn(f"commit={sha[:12]} field=author-email", rendered)
        self.assert_redacted(rendered + repr(findings), value)


def vendor_bot_address() -> str:
    """The reviewed bot address, read from the repository allowlist rather than written here."""
    data = json.loads((ROOT / ".privacy-allowlist.json").read_text(encoding="utf-8"))
    web_flow = identities()["web_flow"]
    rest = [v for v in data.get("allowed_exact", []) if v not in ("Tim WU", web_flow)]
    return rest[0] if len(rest) == 1 else ""


class PrivacyMessageTests(CommitRepoCase):
    """Commit messages and trailers: the third published surface."""

    def commit_message(self, message: str, author_email: Optional[str] = None) -> str:
        path = self.base / "message.txt"
        path.write_text(message, encoding="utf-8")
        noreply = identities()["noreply"]
        self.git(
            "commit", "-q", "--allow-empty", "--cleanup=verbatim", "-F", str(path),
            extra={
                "GIT_AUTHOR_NAME": "Tim WU",
                "GIT_AUTHOR_EMAIL": author_email or noreply,
                "GIT_COMMITTER_NAME": "Tim WU",
                "GIT_COMMITTER_EMAIL": noreply,
            },
        )
        return self.git("rev-parse", "HEAD")

    def scan(self, commits: list[str], config=None):
        return self.scanner().scan_commits(self.repo, commits, config or self.config())

    def line_keys(self, findings) -> set[tuple[str, str, str, Optional[int]]]:
        return {(f.commit, f.field, f.category, getattr(f, "line", None)) for f in findings}

    def write_raw_bytes(self, body: bytes) -> str:
        tree = self.git("mktree", input_text="")
        proc = subprocess.run(
            ["git", "hash-object", "-t", "commit", "-w", "--literally", "--stdin"],
            cwd=self.repo, input=body.replace(b"TREE", tree.encode("ascii")),
            capture_output=True, env=self.env,
        )
        if proc.returncode:
            self.fail(f"git hash-object failed: {proc.stderr!r}")
        return proc.stdout.decode("ascii").strip()

    def test_email_in_message_body_is_a_finding_at_its_line(self) -> None:
        value = identities()["private"]
        sha = self.commit_message(f"Subject\n\nBody line one.\nContact {value} for access.\n")
        findings, checked = self.scan([sha])
        self.assertEqual(self.line_keys(findings), {(sha[:12], "message", "email", 4)})
        self.assertEqual(checked, 1)

    def test_email_in_co_authored_by_trailer_is_a_finding(self) -> None:
        value = identities()["private"]
        sha = self.commit_message(f"Subject\n\nBody.\n\nCo-authored-by: Learner <{value}>\n")
        findings, _ = self.scan([sha])
        self.assertEqual(self.line_keys(findings), {(sha[:12], "message", "email", 5)})

    def test_email_in_signed_off_by_trailer_is_a_finding(self) -> None:
        value = identities()["private"]
        sha = self.commit_message(f"Subject\n\nBody.\n\nSigned-off-by: Learner <{value}>\n")
        findings, _ = self.scan([sha])
        self.assertEqual(self.line_keys(findings), {(sha[:12], "message", "email", 5)})

    def test_developer_home_in_subject_is_a_finding(self) -> None:
        path = "/".join(("", "home", "pii-test-user", "repo", "notes.txt"))
        sha = self.commit_message(f"Fix {path}\n")
        findings, _ = self.scan([sha])
        self.assertEqual(self.line_keys(findings), {(sha[:12], "message", "developer_home", 1)})

    def test_noreply_and_reviewed_bot_trailers_are_allowed(self) -> None:
        vendor = vendor_bot_address()
        self.assertTrue(vendor, "the allowlist holds no single reviewed bot address")
        config = self.scanner().load_config(ROOT / ".privacy-allowlist.json")
        noreply = identities()["noreply"]
        sha = self.commit_message(
            f"Subject\n\nBody.\n\nCo-authored-by: Tim WU <{noreply}>\n"
            f"Co-Authored-By: Agent <{vendor}>\n"
        )
        findings, _ = self.scan([sha], config)
        self.assertEqual(findings, ())

    def test_plain_message_and_empty_message_are_allowed(self) -> None:
        plain = self.commit_message("Subject\n\nA plain body with no personal data.\n")
        noreply = identities()["noreply"]
        person = f"Tim WU <{noreply}> 1700000000 +0000"
        empty = self.write_raw_bytes(
            f"tree TREE\nauthor {person}\ncommitter {person}\n\n".encode("utf-8")
        )
        findings, checked = self.scan([plain, empty])
        self.assertEqual(findings, ())
        self.assertEqual(checked, 2)

    def test_earlier_bad_message_is_found_by_pre_push_and_commit_range(self) -> None:
        value = identities()["private"]
        (self.repo / "safe.txt").write_text("safe\n", encoding="utf-8")
        self.git("add", ".")
        base = self.commit_message("Base\n")
        bad = self.commit_message(f"Bad\n\nCo-authored-by: Learner <{value}>\n")
        self.commit_message("Middle\n")
        tip = self.commit_message("Tip\n")
        updates = f"refs/heads/main {tip} refs/heads/main {base}\n"
        result = self.scanner().scan_pre_push(self.repo, "origin", updates, self.config())
        self.assertEqual(
            self.line_keys(result.metadata_findings), {(bad[:12], "message", "email", 3)}
        )
        proc = self.run_cli("--commit-range", base, tip)
        combined = proc.stdout + proc.stderr
        self.assertEqual(proc.returncode, 1, combined)
        self.assertIn(f"commit={bad[:12]} field=message line=3;", combined)
        self.assertIn("3 commits checked (identity and message)", combined)
        self.assert_redacted(combined, value)

    def test_undecodable_messages_fail_closed(self) -> None:
        noreply = identities()["noreply"]
        base = self.commit_message("Base\n")
        head = b"tree TREE\nparent " + base.encode("ascii")
        person = f"Tim WU <{noreply}> 1700000000 +0000".encode("utf-8")
        cases = {
            "legacy encoding header": head + b"\nauthor " + person + b"\ncommitter " + person
            + b"\nencoding ISO-8859-1\n\nCaf\xe9\n",
            "invalid UTF-8 bytes": head + b"\nauthor " + person + b"\ncommitter " + person
            + b"\n\nBroken \xff\xfe bytes\n",
        }
        for label, body in cases.items():
            with self.subTest(case=label):
                sha = self.write_raw_bytes(body)
                with self.assertRaises(self.scanner().ScanError) as caught:
                    self.scan([sha])
                self.assertIn(sha[:12], str(caught.exception))
                self.assert_redacted(str(caught.exception), noreply)
                proc = self.run_cli("--commit-range", base, sha)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(sha[:12], proc.stderr)

    def test_utf8_encoding_header_is_accepted(self) -> None:
        noreply = identities()["noreply"]
        person = f"Tim WU <{noreply}> 1700000000 +0000"
        sha = self.write_raw_bytes(
            f"tree TREE\nauthor {person}\ncommitter {person}\nencoding utf8\n\nCafé\n"
            .encode("utf-8")
        )
        findings, _ = self.scan([sha])
        self.assertEqual(findings, ())

    def test_message_findings_never_carry_the_value_or_line(self) -> None:
        value = identities()["private"]
        line_text = f"Ping {value} about the rollout"
        sha = self.commit_message(f"Subject\n\n{line_text}\n")
        findings, _ = self.scan([sha])
        self.assertTrue(findings)
        rendered = self.scanner().format_findings(findings)
        self.assertIn(f"commit={sha[:12]} field=message line=3;", rendered)
        self.assert_redacted(rendered + repr(findings), value)
        self.assertNotIn("about the rollout", rendered + repr(findings))

    def test_identity_findings_render_without_a_line(self) -> None:
        sha = self.commit(identities()["private"])
        findings, _ = self.scan([sha])
        rendered = self.scanner().format_findings(findings)
        self.assertIn(f"commit={sha[:12]} field=author-email;", rendered)
        self.assertNotIn("line=", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
