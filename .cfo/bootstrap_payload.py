#!/usr/bin/env python3
"""Resolve, validate, and materialize the verified CFOAgent v0.2 overlay."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

# Some payload chunks were later replaced with verified split chunks. Try the
# verified sequence first, while retaining deterministic fallbacks for recovery.
PAYLOAD_VARIANTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "verified-split",
        (
            "part-00",
            "part-01a",
            "part-02",
            "part-03a",
            "part-03b",
            "part-04a",
            "part-04b",
            "part-05a",
            "part-05b",
            "part-06",
        ),
    ),
    (
        "verified-01-original-03",
        (
            "part-00",
            "part-01a",
            "part-02",
            "part-03",
            "part-04a",
            "part-04b",
            "part-05a",
            "part-05b",
            "part-06",
        ),
    ),
    (
        "original-01-verified-03",
        (
            "part-00",
            "part-01",
            "part-02",
            "part-03a",
            "part-03b",
            "part-04a",
            "part-04b",
            "part-05a",
            "part-05b",
            "part-06",
        ),
    ),
    (
        "original",
        (
            "part-00",
            "part-01",
            "part-02",
            "part-03",
            "part-04a",
            "part-04b",
            "part-05a",
            "part-05b",
            "part-06",
        ),
    ),
)

ALLOWED_WORKFLOWS = {".github/workflows/cfo-ci.yml"}
REQUIRED_MEMBERS = {
    "cfo_agent/__init__.py",
    "cfo_agent/cli.py",
    "scripts/patch_upstream.py",
    "scripts/sync_upstream.py",
}


@dataclass(frozen=True)
class PayloadCandidate:
    variant: str
    parts: tuple[str, ...]
    raw: bytes
    padding: int
    members: frozenset[str]
    skill_docs: tuple[str, ...]


def clean_base64(text: str) -> str:
    return "".join(text.split())


def decode_payload(encoded: str, label: str) -> tuple[bytes, int]:
    encoded = clean_base64(encoded)
    if not encoded:
        raise ValueError(f"{label} is empty")
    if "=" in encoded.rstrip("="):
        raise ValueError(f"{label} contains embedded base64 padding")

    padding = (-len(encoded)) % 4
    encoded += "=" * padding
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError(f"invalid base64: {exc}") from exc

    if raw[:2] != b"\x1f\x8b":
        raise ValueError("decoded data is not gzip")
    return raw, padding


def normalize_member_name(name: str) -> str:
    normalized = name[2:] if name.startswith("./") else name
    return normalized.rstrip("/")


def inspect_archive(raw: bytes, label: str) -> frozenset[str]:
    names: set[str] = set()
    try:
        archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ValueError(f"invalid tar.gz: {exc}") from exc

    try:
        with archive:
            for member in archive.getmembers():
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError(f"unsafe path: {member.name}")
                if not (member.isdir() or member.isfile()):
                    raise ValueError(
                        f"unsupported tar member: {member.name} ({member.type!r})"
                    )

                normalized = normalize_member_name(member.name)
                if normalized in {"", "."}:
                    continue
                if normalized in {".git", ".github/workflows/bootstrap-hermes.yml"}:
                    raise ValueError(f"protected path: {member.name}")
                if normalized.startswith(".git/"):
                    raise ValueError(f"protected path: {member.name}")
                if (
                    normalized.startswith(".github/workflows/")
                    and normalized not in ALLOWED_WORKFLOWS
                ):
                    raise ValueError(f"protected workflow: {member.name}")
                names.add(normalized)
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise ValueError(f"corrupt tar stream: {exc}") from exc

    return frozenset(names)


def missing_members(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(REQUIRED_MEMBERS - set(names)))


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


def assemble_variant(
    delta_dir: Path,
    variant: str,
    parts: tuple[str, ...],
) -> PayloadCandidate:
    missing_files = [
        part
        for part in parts
        if not (delta_dir / part).is_file()
        or (delta_dir / part).stat().st_size == 0
    ]
    if missing_files:
        raise ValueError("missing parts: " + ", ".join(missing_files))

    encoded = "".join(
        clean_base64((delta_dir / part).read_text(encoding="ascii"))
        for part in parts
    )
    raw, padding = decode_payload(encoded, variant)
    members = inspect_archive(raw, variant)
    missing = missing_members(members)
    if missing:
        preview = ", ".join(sorted(members)[:15])
        raise ValueError(
            "missing required members: "
            + ", ".join(missing)
            + f"; archive preview: {preview}"
        )

    skill_docs = tuple(sorted(name for name in members if name.endswith("/SKILL.md")))
    if not skill_docs:
        raise ValueError("archive contains no SKILL.md files")

    return PayloadCandidate(
        variant=variant,
        parts=parts,
        raw=raw,
        padding=padding,
        members=members,
        skill_docs=skill_docs,
    )


def resolve_payload(delta_dir: Path) -> PayloadCandidate:
    failures: list[str] = []
    for variant, parts in PAYLOAD_VARIANTS:
        try:
            candidate = assemble_variant(delta_dir, variant, parts)
        except ValueError as exc:
            failures.append(f"{variant}: {exc}")
            print(f"Rejected payload variant {variant}: {exc}")
            continue

        print(
            f"Selected payload variant {candidate.variant}: "
            f"{len(candidate.raw):,} bytes, {len(candidate.members)} members, "
            f"{len(candidate.skill_docs)} skill documents"
        )
        return candidate

    details = "\n  - ".join(failures)
    raise SystemExit(
        "No CFO v0.2 payload variant passed validation.\n  - " + details
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runner_temp = args.runner_temp.resolve()
    github_env = args.github_env.resolve()
    runner_temp.mkdir(parents=True, exist_ok=True)
    github_env.parent.mkdir(parents=True, exist_ok=True)

    delta_dir = repo_root / ".cfo" / "delta-v0.2.0"
    if not delta_dir.is_dir():
        raise SystemExit(f"Missing CFO payload directory: {delta_dir}")

    candidate = resolve_payload(delta_dir)
    overlay_archive = runner_temp / "cfo-v0.2-overlay.tar.gz"
    overlay_archive.write_bytes(candidate.raw)

    digest = hashlib.sha256(candidate.raw).hexdigest()
    (repo_root / ".cfo" / "overlay.sha256").write_text(
        f"{digest}  cfo-v0.2-overlay.tar.gz\n",
        encoding="ascii",
    )

    append_github_env(
        github_env,
        {
            "CFO_OVERLAY_ARCHIVE": overlay_archive,
            "CFO_OVERLAY_SHA256": digest,
            "CFO_OVERLAY_PADDING": candidate.padding,
            "CFO_OVERLAY_VARIANT": candidate.variant,
            "PAYLOAD_PART_COUNT": len(candidate.parts),
            "PAYLOAD_SKILL_DOC_COUNT": len(candidate.skill_docs),
        },
    )

    print(
        "Validated CFO v0.2 overlay: "
        f"variant={candidate.variant}, bytes={len(candidate.raw):,}, "
        f"parts={len(candidate.parts)}, skills={len(candidate.skill_docs)}, "
        f"padding_added={candidate.padding}, sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
