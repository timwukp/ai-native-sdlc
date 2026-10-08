#!/usr/bin/env python3
"""Deterministic high-confidence privacy scanner.

Findings deliberately carry no matched source value. A content diagnostic contains only category,
repository-relative path, line number, and remediation. A commit-identity diagnostic contains only
category, the first 12 hex digits of the commit id, the field name, and remediation.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import subprocess
import sys
from typing import Callable, Iterable, Optional, Pattern, Sequence


class ConfigError(ValueError):
    """The reviewed allowlist is malformed or unsupported."""


class ScanError(RuntimeError):
    """Tracked content or Git input could not be scanned safely."""


@dataclasses.dataclass(frozen=True)
class Config:
    allowed_exact: frozenset[str]
    allowed_patterns: tuple[Pattern[str], ...]
    markers: tuple[str, ...]
    max_text_bytes: int


@dataclasses.dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    category: str
    remediation: str


@dataclasses.dataclass(frozen=True, order=True)
class MetadataFinding:
    commit: str
    field: str
    category: str
    remediation: str


@dataclasses.dataclass(frozen=True)
class ScanResult:
    findings: tuple[Finding, ...]
    scanned_files: int
    skipped_binary: int
    metadata_findings: tuple[MetadataFinding, ...] = ()
    identities_checked: Optional[int] = None


EXPECTED_CONFIG_KEYS = {
    "schema_version",
    "allowed_exact",
    "allowed_patterns",
    "markers",
    "max_text_bytes",
}
ZERO_SHA = "0" * 40
FULL_SHA_RE = re.compile(r"[0-9a-fA-F]{40}")
IDENTITY_ROLES = ("author", "committer")
IDENTITY_RE = re.compile(r"(?P<name>[^<>\n]*?) <(?P<email>[^<>\n]*)> -?\d+ [+-]\d{4}")
EMAIL_RE = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
HOME_RES = (
    re.compile(r"(?<![A-Za-z0-9<])/(?:home|Users)/[A-Za-z0-9._-]+/"),
    re.compile(r"(?i)(?<![A-Za-z0-9<])[A-Z]:\\Users\\[A-Za-z0-9._-]+\\"),
)
PHONE_RE = re.compile(
    r"(?i)(?:^|\b)(?:phone|mobile|tel|telephone|contact|電話|手機)"
    r"\s*[:=]?\s*(\+?[0-9][0-9 ()-]{6,}[0-9])"
)
CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----")
BEARER_RE = re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{20,}\b", re.I)
AWS_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
GITHUB_RE = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
SLACK_RE = re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")

REMEDIATIONS = {
    "developer_home": "replace the machine-specific home path with a repository-relative path",
    "configured_marker": "replace the configured machine or user marker with a generic label",
    "email": "remove the address or add a reviewed public/example value to the narrow allowlist",
    "phone": "remove the phone number or replace it with an unmistakable example",
    "payment_card": "remove the card-shaped value and rotate/report it if it was real",
    "private_key": "remove and rotate the private key before publishing any commit",
    "bearer_token": "remove and rotate the bearer credential before publishing any commit",
    "aws_key": "remove and rotate the AWS credential before publishing any commit",
    "github_token": "remove and rotate the GitHub credential before publishing any commit",
    "slack_token": "remove and rotate the Slack credential before publishing any commit",
    "commit_email": "re-author the commit with a GitHub noreply or other reviewed public address",
}


def _string_list(data: object, field: str) -> list[str]:
    if not isinstance(data, list) or any(not isinstance(value, str) for value in data):
        raise ConfigError(f"{field} must be a list of strings")
    if len(data) != len(set(data)):
        raise ConfigError(f"{field} contains duplicate entries")
    return list(data)


def load_config(path: pathlib.Path) -> Config:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError("privacy allowlist is unreadable or invalid JSON") from exc
    if not isinstance(raw, dict):
        raise ConfigError("privacy allowlist root must be an object")
    unknown = set(raw) - EXPECTED_CONFIG_KEYS
    missing = EXPECTED_CONFIG_KEYS - set(raw)
    if unknown or missing:
        raise ConfigError("privacy allowlist has unknown or missing fields")
    if raw.get("schema_version") != 1:
        raise ConfigError("unsupported privacy allowlist schema")

    exact = _string_list(raw.get("allowed_exact"), "allowed_exact")
    pattern_text = _string_list(raw.get("allowed_patterns"), "allowed_patterns")
    markers = _string_list(raw.get("markers"), "markers")
    if any(not value for value in exact):
        raise ConfigError("allowed_exact entries must not be empty")
    if any(len(value) < 4 for value in markers):
        raise ConfigError("configured markers must be at least four characters")

    patterns: list[Pattern[str]] = []
    for pattern in pattern_text:
        if not pattern.startswith("^") or not pattern.endswith("$"):
            raise ConfigError("allowed patterns must be fully anchored")
        try:
            patterns.append(re.compile(pattern))
        except re.error as exc:
            raise ConfigError("allowed pattern is not valid regex") from exc

    maximum = raw.get("max_text_bytes")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or maximum <= 0:
        raise ConfigError("max_text_bytes must be a positive integer")
    return Config(frozenset(exact), tuple(patterns), tuple(markers), maximum)


def _allowed(value: str, config: Config) -> bool:
    return value in config.allowed_exact or any(pattern.fullmatch(value) for pattern in config.allowed_patterns)


def _line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _finding(category: str, path: str, text: str, start: int) -> Finding:
    return Finding(path, _line(text, start), category, REMEDIATIONS[category])


def _regex_findings(
    category: str, pattern: Pattern[str], text: str, path: str, config: Config,
    group: int = 0, predicate: Optional[Callable[[str], bool]] = None,
) -> list[Finding]:
    findings: list[Finding] = []
    for match in pattern.finditer(text):
        value = match.group(group)
        if _allowed(value, config):
            continue
        if predicate is not None and not predicate(value):
            continue
        findings.append(_finding(category, path, text, match.start(group)))
    return findings


def _scan_developer_home(text: str, path: str, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    for pattern in HOME_RES:
        findings.extend(_regex_findings("developer_home", pattern, text, path, config))
    return findings


def _scan_configured_marker(text: str, path: str, config: Config) -> list[Finding]:
    findings: list[Finding] = []
    for marker in config.markers:
        if _allowed(marker, config):
            continue
        for match in re.finditer(re.escape(marker), text):
            findings.append(_finding("configured_marker", path, text, match.start()))
    return findings


def _scan_email(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("email", EMAIL_RE, text, path, config)


def _scan_phone(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("phone", PHONE_RE, text, path, config, group=1)


def luhn_valid(value: str) -> bool:
    digits = [int(char) for char in value if char.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _scan_payment_card(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("payment_card", CARD_RE, text, path, config, predicate=luhn_valid)


def _scan_private_key(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("private_key", PRIVATE_KEY_RE, text, path, config)


def _scan_bearer_token(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("bearer_token", BEARER_RE, text, path, config)


def _scan_aws_key(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("aws_key", AWS_RE, text, path, config)


def _scan_github_token(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("github_token", GITHUB_RE, text, path, config)


def _scan_slack_token(text: str, path: str, config: Config) -> list[Finding]:
    return _regex_findings("slack_token", SLACK_RE, text, path, config)


RULES: tuple[tuple[str, Callable[[str, str, Config], list[Finding]]], ...] = (
        ("developer_home", _scan_developer_home),
        ("configured_marker", _scan_configured_marker),
        ("email", _scan_email),
        ("phone", _scan_phone),
        ("payment_card", _scan_payment_card),
        ("private_key", _scan_private_key),
        ("bearer_token", _scan_bearer_token),
        ("aws_key", _scan_aws_key),
        ("github_token", _scan_github_token),
        ("slack_token", _scan_slack_token),
)


def scan_text(text: str, path: str, config: Config) -> tuple[Finding, ...]:
    findings: set[Finding] = set()
    for category, rule in RULES:
        # A configured marker necessarily appears in the config that declares it. Suppress only
        # that self-reference; the allowlist file remains subject to every other category.
        if path == ".privacy-allowlist.json" and category == "configured_marker":
            continue
        findings.update(rule(text, path, config))
    return tuple(sorted(findings))


def format_findings(findings: Iterable[Finding | MetadataFinding]) -> str:
    content = sorted(f for f in findings if isinstance(f, Finding))
    metadata = sorted(f for f in findings if isinstance(f, MetadataFinding))
    lines = [
        "PRIVACY FINDING: "
        f"category={finding.category} path={finding.path} line={finding.line}; "
        f"{finding.remediation}; matched value redacted"
        for finding in content
    ]
    lines.extend(
        "PRIVACY FINDING: "
        f"category={finding.category} commit={finding.commit} field={finding.field}; "
        f"{finding.remediation}; matched value redacted"
        for finding in metadata
    )
    return "\n".join(lines)


def _git(repo: pathlib.Path, args: Sequence[str], input_bytes: Optional[bytes] = None) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        capture_output=True,
    )
    if proc.returncode:
        raise ScanError("required Git operation failed")
    return proc.stdout


def _repo_root(repo: pathlib.Path) -> pathlib.Path:
    output = _git(repo, ("rev-parse", "--show-toplevel"))
    try:
        return pathlib.Path(output.decode("utf-8").strip()).resolve()
    except UnicodeError as exc:
        raise ScanError("repository root is not valid UTF-8") from exc


def _decode_paths(raw: bytes) -> list[str]:
    try:
        return [item.decode("utf-8") for item in raw.split(b"\0") if item]
    except UnicodeError as exc:
        raise ScanError("tracked path is not valid UTF-8") from exc


def _scan_bytes(data: bytes, path: str, config: Config) -> tuple[tuple[Finding, ...], bool]:
    if len(data) > config.max_text_bytes:
        raise ScanError(f"tracked text exceeds configured size limit: {path}")
    if b"\0" in data:
        return (), True
    try:
        text = data.decode("utf-8")
    except UnicodeError as exc:
        raise ScanError(f"non-binary tracked file is not valid UTF-8: {path}") from exc
    return scan_text(text, path, config), False


def scan_repository(repo: pathlib.Path, config: Config) -> ScanResult:
    root = _repo_root(repo)
    paths = _decode_paths(_git(root, ("ls-files", "-z")))
    findings: set[Finding] = set()
    scanned = 0
    skipped = 0
    for relative in paths:
        path = root / relative
        if path.is_symlink():
            continue
        try:
            path.resolve().relative_to(root)
        except ValueError:
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise ScanError(f"tracked file cannot be read: {relative}") from exc
        file_findings, binary = _scan_bytes(data, relative, config)
        if binary:
            skipped += 1
        else:
            scanned += 1
            findings.update(file_findings)
    return ScanResult(tuple(sorted(findings)), scanned, skipped)


def _scan_treeish(repo: pathlib.Path, treeish: str, config: Config) -> ScanResult:
    paths = _decode_paths(_git(repo, ("ls-tree", "-rz", "--name-only", treeish)))
    findings: set[Finding] = set()
    scanned = 0
    skipped = 0
    for relative in paths:
        data = _git(repo, ("show", f"{treeish}:{relative}"))
        file_findings, binary = _scan_bytes(data, relative, config)
        if binary:
            skipped += 1
        else:
            scanned += 1
            findings.update(file_findings)
    return ScanResult(tuple(sorted(findings)), scanned, skipped)


def _commit_identity(repo: pathlib.Path, commit: str) -> dict[str, tuple[str, str]]:
    """Return {role: (name, email)} parsed from the raw commit object header."""
    short = commit[:12]
    raw = _git(repo, ("cat-file", "commit", commit))
    header = raw.split(b"\n\n", 1)[0]
    try:
        text = header.decode("utf-8")
    except UnicodeError as exc:
        raise ScanError(f"commit header is not valid UTF-8: {short}") from exc
    identity: dict[str, tuple[str, str]] = {}
    for line in text.split("\n"):
        for role in IDENTITY_ROLES:
            if not line.startswith(role + " "):
                continue
            if role in identity:
                raise ScanError(f"commit has more than one {role} line: {short}")
            match = IDENTITY_RE.fullmatch(line[len(role) + 1:])
            if match is None:
                raise ScanError(f"commit {role} line is malformed: {short}")
            identity[role] = (match.group("name"), match.group("email"))
    if set(identity) != set(IDENTITY_ROLES):
        raise ScanError(f"commit lacks an author or committer line: {short}")
    return identity


def _identity_findings(
    short: str, identity: dict[str, tuple[str, str]], config: Config
) -> list[MetadataFinding]:
    findings: list[MetadataFinding] = []
    for role in IDENTITY_ROLES:
        name, email = identity[role]
        for field, value in ((f"{role}-name", name), (f"{role}-email", email)):
            if field.endswith("-email"):
                # Allowlist-judged: anything not a reviewed public identity is a finding.
                categories = set() if value and _allowed(value, config) else {"commit_email"}
            else:
                # Names are not PII by themselves; only the content rules apply to them.
                categories = {finding.category for finding in scan_text(value, field, config)}
            for category in sorted(categories):
                findings.append(MetadataFinding(short, field, category, REMEDIATIONS[category]))
    return findings


def scan_commit_identities(
    repo: pathlib.Path, commits: Sequence[str], config: Config
) -> tuple[tuple[MetadataFinding, ...], int]:
    """Check author and committer identity of each commit; return findings and commits checked."""
    findings: set[MetadataFinding] = set()
    unique = list(dict.fromkeys(commits))
    for commit in unique:
        identity = _commit_identity(repo, commit)
        short = commit[:12]
        findings.update(_identity_findings(short, identity, config))
    return tuple(sorted(findings)), len(unique)


def scan_commit_range(repo: pathlib.Path, base: str, head: str, config: Config) -> ScanResult:
    """Check identities of the commits in merge-base(base, head)..head."""
    if not FULL_SHA_RE.fullmatch(base) or not FULL_SHA_RE.fullmatch(head):
        raise ScanError("--commit-range needs two full 40-hex commit ids")
    root = _repo_root(repo)
    try:
        merge_base = _git(root, ("merge-base", base, head)).decode("ascii").strip()
        raw = _git(root, ("rev-list", "--reverse", f"{merge_base}..{head}"))
        commits = [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeError as exc:
        raise ScanError("Git returned a non-ASCII commit id") from exc
    metadata, checked = scan_commit_identities(root, commits, config)
    return ScanResult((), 0, 0, metadata, checked)


def _outgoing_commits(repo: pathlib.Path, remote: str, local_sha: str, remote_sha: str) -> list[str]:
    if remote_sha == ZERO_SHA:
        raw = _git(repo, ("rev-list", "--reverse", local_sha, "--not", f"--remotes={remote}"))
    else:
        raw = _git(repo, ("rev-list", "--reverse", f"{remote_sha}..{local_sha}"))
    try:
        return [line for line in raw.decode("ascii").splitlines() if line]
    except UnicodeError as exc:
        raise ScanError("Git returned a non-ASCII commit id") from exc


def scan_pre_push(repo: pathlib.Path, remote: str, updates: str, config: Config) -> ScanResult:
    if not remote or any(char.isspace() for char in remote):
        raise ScanError("pre-push remote name is invalid")
    root = _repo_root(repo)
    commits: list[str] = []
    for line in updates.splitlines():
        parts = line.split()
        if len(parts) != 4:
            raise ScanError("pre-push update input is malformed")
        _local_ref, local_sha, _remote_ref, remote_sha = parts
        if local_sha == ZERO_SHA:
            continue
        if not re.fullmatch(r"[0-9a-fA-F]{40}", local_sha) or not re.fullmatch(
            r"[0-9a-fA-F]{40}", remote_sha
        ):
            raise ScanError("pre-push update contains an invalid object id")
        commits.extend(_outgoing_commits(root, remote, local_sha, remote_sha))

    findings: set[Finding] = set()
    scanned = 0
    skipped = 0
    unique = list(dict.fromkeys(commits))
    for commit in unique:
        result = _scan_treeish(root, commit, config)
        findings.update(result.findings)
        scanned += result.scanned_files
        skipped += result.skipped_binary
    metadata, checked = scan_commit_identities(root, unique, config)
    return ScanResult(tuple(sorted(findings)), scanned, skipped, metadata, checked)


def _render_result(result: ScanResult) -> int:
    every = (*result.findings, *result.metadata_findings)
    if every:
        print(format_findings(every), file=sys.stderr)
    print(
        f"privacy scan: {result.scanned_files} text files, "
        f"{result.skipped_binary} binary files skipped, {len(every)} findings"
    )
    if result.identities_checked is not None:
        print(f"privacy scan: {result.identities_checked} commit identities checked")
    return 1 if every else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repo", default=".", help="repository root or a path inside it")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--pre-push", action="store_true", help="read Git pre-push updates")
    mode.add_argument(
        "--commit-range", nargs=2, metavar=("BASE", "HEAD"),
        help="check commit identities in merge-base(BASE, HEAD)..HEAD (full ids)",
    )
    parser.add_argument("--remote", default="", help="remote name for --pre-push")
    args = parser.parse_args(argv)
    try:
        root = _repo_root(pathlib.Path(args.repo))
        config = load_config(root / ".privacy-allowlist.json")
        if args.pre_push:
            result = scan_pre_push(root, args.remote, sys.stdin.read(), config)
        elif args.commit_range:
            result = scan_commit_range(root, args.commit_range[0], args.commit_range[1], config)
        else:
            result = scan_repository(root, config)
        return _render_result(result)
    except (ConfigError, ScanError) as exc:
        print(f"privacy scan error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
