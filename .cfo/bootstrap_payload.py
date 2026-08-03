#!/usr/bin/env python3
"""Recover the legacy CFO base and resolve the verified CFOAgent v0.2 overlay."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import shutil
import tarfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

# Later commits replaced selected chunks with verified split chunks. Evaluate
# the plausible deterministic sequences and select the first valid archive.
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
DELTA_REQUIRED = {"cfo_agent/__init__.py"}
RECOVERY_REQUIRED = {
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


@dataclass(frozen=True)
class RecoveryResult:
    directory: Path
    members: frozenset[str]
    decompressed_bytes: int
    compressed_error_offset: int
    gzip_error: str
    tar_error: str


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


def validate_member(member: tarfile.TarInfo, label: str) -> str:
    path = PurePosixPath(member.name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe path in {label}: {member.name}")
    if not (member.isdir() or member.isfile()):
        raise ValueError(
            f"unsupported tar member in {label}: {member.name} ({member.type!r})"
        )

    normalized = normalize_member_name(member.name)
    if normalized in {"", "."}:
        return ""
    if normalized in {".git", ".github/workflows/bootstrap-hermes.yml"}:
        raise ValueError(f"protected path in {label}: {member.name}")
    if normalized.startswith(".git/"):
        raise ValueError(f"protected path in {label}: {member.name}")
    if (
        normalized.startswith(".github/workflows/")
        and normalized not in ALLOWED_WORKFLOWS
    ):
        raise ValueError(f"protected workflow in {label}: {member.name}")
    return normalized


def inspect_archive(raw: bytes, label: str) -> frozenset[str]:
    names: set[str] = set()
    try:
        archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    except (tarfile.TarError, OSError, EOFError, zlib.error) as exc:
        raise ValueError(f"invalid tar.gz: {exc}") from exc

    try:
        with archive:
            for member in archive.getmembers():
                normalized = validate_member(member, label)
                if normalized:
                    names.add(normalized)
    except (tarfile.TarError, OSError, EOFError, zlib.error) as exc:
        raise ValueError(f"corrupt tar stream: {exc}") from exc

    return frozenset(names)


def missing_members(names: Iterable[str], required: set[str]) -> tuple[str, ...]:
    return tuple(sorted(required - set(names)))


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
    missing = missing_members(members, DELTA_REQUIRED)
    if missing:
        preview = ", ".join(sorted(members)[:15])
        raise ValueError(
            "missing required members: "
            + ", ".join(missing)
            + f"; archive preview: {preview}"
        )

    skill_docs = tuple(sorted(name for name in members if name.endswith("/SKILL.md")))

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


def decompress_gzip_prefix(raw: bytes) -> tuple[bytes, int, str]:
    decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
    output = bytearray()
    error_offset = len(raw)
    error_message = ""

    # Byte-wise input preserves the longest safe prefix when the old gzip
    # stream contains a corrupt compressed block.
    for offset, value in enumerate(raw):
        try:
            output.extend(decompressor.decompress(bytes((value,))))
        except zlib.error as exc:
            error_offset = offset
            error_message = str(exc)
            break
    else:
        try:
            output.extend(decompressor.flush())
        except zlib.error as exc:
            error_message = str(exc)

    return bytes(output), error_offset, error_message


def recover_tar_prefix(tar_bytes: bytes, destination: Path) -> RecoveryResult:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    recovered: set[str] = set()
    tar_error = ""
    archive: tarfile.TarFile | None = None

    try:
        archive = tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:")
        while True:
            try:
                member = archive.next()
            except (tarfile.TarError, OSError, EOFError) as exc:
                tar_error = str(exc)
                break
            if member is None:
                break

            try:
                normalized = validate_member(member, "legacy CFO base")
            except ValueError as exc:
                raise SystemExit(str(exc)) from exc
            if not normalized:
                continue

            target = destination / PurePosixPath(normalized)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                recovered.add(normalized)
                continue

            extracted = archive.extractfile(member)
            if extracted is None:
                tar_error = f"unable to read {normalized}"
                break
            try:
                data = extracted.read()
            except (tarfile.TarError, OSError, EOFError) as exc:
                tar_error = f"{normalized}: {exc}"
                break
            if len(data) != member.size:
                tar_error = (
                    f"{normalized}: expected {member.size} bytes, recovered {len(data)}"
                )
                break

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            recovered.add(normalized)
    except (tarfile.TarError, OSError, EOFError) as exc:
        tar_error = str(exc)
    finally:
        if archive is not None:
            archive.close()

    return RecoveryResult(
        directory=destination,
        members=frozenset(recovered),
        decompressed_bytes=len(tar_bytes),
        compressed_error_offset=0,
        gzip_error="",
        tar_error=tar_error,
    )


def recover_legacy_base(base_raw: bytes, destination: Path) -> RecoveryResult:
    tar_prefix, error_offset, gzip_error = decompress_gzip_prefix(base_raw)
    partial = recover_tar_prefix(tar_prefix, destination)
    return RecoveryResult(
        directory=partial.directory,
        members=partial.members,
        decompressed_bytes=len(tar_prefix),
        compressed_error_offset=error_offset,
        gzip_error=gzip_error,
        tar_error=partial.tar_error,
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

    legacy_path = repo_root / ".cfo" / "overlay.tar.gz.b64"
    if not legacy_path.is_file() or legacy_path.stat().st_size == 0:
        raise SystemExit(f"Missing legacy CFO base payload: {legacy_path}")
    try:
        legacy_raw, legacy_padding = decode_payload(
            legacy_path.read_text(encoding="ascii"), "legacy CFO base"
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    recovery = recover_legacy_base(
        legacy_raw, runner_temp / "cfo-recovered-base"
    )
    missing_recovery = missing_members(recovery.members, RECOVERY_REQUIRED)
    print(
        "Legacy base recovery: "
        f"compressed={len(legacy_raw):,} bytes, "
        f"decompressed_prefix={recovery.decompressed_bytes:,} bytes, "
        f"files={len(recovery.members)}, "
        f"gzip_error_offset={recovery.compressed_error_offset}, "
        f"gzip_error={recovery.gzip_error or 'none'}, "
        f"tar_error={recovery.tar_error or 'none'}"
    )
    if missing_recovery:
        preview = ", ".join(sorted(recovery.members)[:40])
        raise SystemExit(
            "Legacy CFO base recovery is incomplete; missing: "
            + ", ".join(missing_recovery)
            + f". Recovered preview: {preview}"
        )

    overlay_archive = runner_temp / "cfo-v0.2-delta.tar.gz"
    overlay_archive.write_bytes(candidate.raw)

    overlay_digest = hashlib.sha256(candidate.raw).hexdigest()
    legacy_digest = hashlib.sha256(legacy_raw).hexdigest()
    (repo_root / ".cfo" / "overlay.sha256").write_text(
        f"{legacy_digest}  legacy-cfo-base-corrupt.tar.gz\n"
        f"{overlay_digest}  cfo-v0.2-delta.tar.gz\n",
        encoding="ascii",
    )

    append_github_env(
        github_env,
        {
            "CFO_RECOVERY_DIR": recovery.directory,
            "CFO_RECOVERED_FILE_COUNT": len(recovery.members),
            "CFO_RECOVERED_BYTES": recovery.decompressed_bytes,
            "CFO_LEGACY_SHA256": legacy_digest,
            "CFO_LEGACY_PADDING": legacy_padding,
            "CFO_OVERLAY_ARCHIVE": overlay_archive,
            "CFO_OVERLAY_SHA256": overlay_digest,
            "CFO_OVERLAY_PADDING": candidate.padding,
            "CFO_OVERLAY_VARIANT": candidate.variant,
            "PAYLOAD_PART_COUNT": len(candidate.parts),
            "PAYLOAD_SKILL_DOC_COUNT": len(candidate.skill_docs),
        },
    )

    print(
        "Validated CFO v0.2 delta: "
        f"variant={candidate.variant}, bytes={len(candidate.raw):,}, "
        f"parts={len(candidate.parts)}, skills={len(candidate.skill_docs)}, "
        f"padding_added={candidate.padding}, sha256={overlay_digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
