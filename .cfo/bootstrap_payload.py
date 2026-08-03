#!/usr/bin/env python3
"""Assemble, validate, and materialize the CFOAgent base and v0.2 payloads."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Iterable

DELTA_PARTS = (
    "part-00",
    "part-01",
    "part-01a",
    "part-02",
    "part-03",
    "part-03a",
    "part-03b",
    "part-04a",
    "part-04b",
    "part-05a",
    "part-05b",
    "part-06",
)

ALLOWED_WORKFLOWS = {".github/workflows/cfo-ci.yml"}
BASE_REQUIRED = {
    "cfo_agent/cli.py",
    "scripts/patch_upstream.py",
    "scripts/sync_upstream.py",
}
DELTA_REQUIRED = {"cfo_agent/__init__.py"}


def clean_base64(text: str) -> str:
    return "".join(text.split())


def decode_payload(encoded: str, label: str) -> tuple[bytes, int]:
    encoded = clean_base64(encoded)
    if not encoded:
        raise SystemExit(f"{label} is empty")
    if "=" in encoded.rstrip("="):
        raise SystemExit(f"{label} contains embedded base64 padding")

    padding = (-len(encoded)) % 4
    encoded += "=" * padding
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise SystemExit(f"Invalid base64 in {label}: {exc}") from exc

    if raw[:2] != b"\x1f\x8b":
        raise SystemExit(f"{label} is not a gzip archive")
    return raw, padding


def normalize_member_name(name: str) -> str:
    normalized = name[2:] if name.startswith("./") else name
    return normalized.rstrip("/")


def inspect_archive(raw: bytes, label: str) -> set[str]:
    names: set[str] = set()
    try:
        archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    except tarfile.TarError as exc:
        raise SystemExit(f"Invalid tar archive in {label}: {exc}") from exc

    with archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"Unsafe path in {label}: {member.name}")
            if not (member.isdir() or member.isfile()):
                raise SystemExit(
                    f"Unsupported tar member in {label}: {member.name} ({member.type!r})"
                )

            normalized = normalize_member_name(member.name)
            if normalized in {".git", ".github/workflows/bootstrap-hermes.yml"}:
                raise SystemExit(f"Protected path in {label}: {member.name}")
            if normalized.startswith(".git/"):
                raise SystemExit(f"Protected path in {label}: {member.name}")
            if (
                normalized.startswith(".github/workflows/")
                and normalized not in ALLOWED_WORKFLOWS
            ):
                raise SystemExit(f"Protected workflow in {label}: {member.name}")
            names.add(normalized)
    return names


def require_members(names: set[str], required: Iterable[str], label: str) -> None:
    missing = sorted(set(required) - names)
    if missing:
        preview = ", ".join(sorted(names)[:20])
        raise SystemExit(
            f"{label} is incomplete; missing: {', '.join(missing)}. "
            f"Archive preview: {preview}"
        )


def append_github_env(path: Path, values: dict[str, str | int]) -> None:
    with path.open("a", encoding="utf-8") as env_file:
        for key, value in values.items():
            rendered = str(value)
            if "\n" in rendered or "\r" in rendered:
                raise SystemExit(f"Unsafe newline in environment value: {key}")
            env_file.write(f"{key}={rendered}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--runner-temp",
        type=Path,
        default=Path(os.environ.get("RUNNER_TEMP", "/tmp")),
    )
    parser.add_argument(
        "--github-env",
        type=Path,
        default=Path(os.environ.get("GITHUB_ENV", "/tmp/cfo-github-env")),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runner_temp = args.runner_temp.resolve()
    github_env = args.github_env.resolve()
    runner_temp.mkdir(parents=True, exist_ok=True)
    github_env.parent.mkdir(parents=True, exist_ok=True)

    base_b64 = repo_root / ".cfo" / "overlay.tar.gz.b64"
    delta_dir = repo_root / ".cfo" / "delta-v0.2.0"
    if not base_b64.is_file() or base_b64.stat().st_size == 0:
        raise SystemExit(f"Missing CFO base payload: {base_b64}")

    missing_parts = [name for name in DELTA_PARTS if not (delta_dir / name).is_file()]
    if missing_parts:
        raise SystemExit("Missing CFO delta parts: " + ", ".join(missing_parts))

    delta_encoded = "".join(
        clean_base64((delta_dir / name).read_text(encoding="ascii"))
        for name in DELTA_PARTS
    )
    base_raw, base_padding = decode_payload(
        base_b64.read_text(encoding="ascii"), "CFO base overlay"
    )
    delta_raw, delta_padding = decode_payload(delta_encoded, "CFO v0.2 delta")

    base_names = inspect_archive(base_raw, "CFO base overlay")
    delta_names = inspect_archive(delta_raw, "CFO v0.2 delta")
    require_members(base_names, BASE_REQUIRED, "CFO base overlay")
    require_members(delta_names, DELTA_REQUIRED, "CFO v0.2 delta")

    delta_skill_docs = sorted(name for name in delta_names if name.endswith("/SKILL.md"))
    if not delta_skill_docs:
        raise SystemExit("CFO v0.2 delta contains no SKILL.md files")

    base_archive = runner_temp / "cfo-base-overlay.tar.gz"
    delta_archive = runner_temp / "cfo-v0.2-delta.tar.gz"
    base_archive.write_bytes(base_raw)
    delta_archive.write_bytes(delta_raw)

    base_digest = hashlib.sha256(base_raw).hexdigest()
    delta_digest = hashlib.sha256(delta_raw).hexdigest()
    (repo_root / ".cfo" / "overlay.sha256").write_text(
        f"{base_digest}  cfo-base-overlay.tar.gz\n"
        f"{delta_digest}  cfo-v0.2-delta.tar.gz\n",
        encoding="ascii",
    )

    append_github_env(
        github_env,
        {
            "CFO_BASE_ARCHIVE": base_archive,
            "CFO_DELTA_ARCHIVE": delta_archive,
            "CFO_BASE_SHA256": base_digest,
            "CFO_DELTA_SHA256": delta_digest,
            "CFO_BASE_PADDING": base_padding,
            "CFO_DELTA_PADDING": delta_padding,
            "PAYLOAD_PART_COUNT": len(DELTA_PARTS),
            "DELTA_SKILL_DOC_COUNT": len(delta_skill_docs),
        },
    )

    print(
        "Validated CFO payloads: "
        f"base={len(base_raw):,} bytes, delta={len(delta_raw):,} bytes, "
        f"delta_skill_docs={len(delta_skill_docs)}, "
        f"base_sha256={base_digest}, delta_sha256={delta_digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
