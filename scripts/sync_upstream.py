from __future__ import annotations

import argparse
import shutil
from pathlib import Path


PRESERVED_PREFIXES = (
    ".cfo/",
    ".github/workflows/bootstrap-hermes.yml",
    ".github/workflows/cfo-ci.yml",
    "cfo_agent/",
    "tests/cfo_agent/",
    "skills/finance-cfo/",
    "skills/finance-official/",
    "examples/sample_",
    "scripts/patch_upstream.py",
    "scripts/sync_upstream.py",
    "scripts/generate_finance_skills.py",
    "README_CFO.md",
    "THIRD_PARTY_NOTICES.md",
    ".hermes.md",
)


def is_preserved(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix)
        for prefix in PRESERVED_PREFIXES
    )


def copy_upstream(source: Path, destination: Path) -> int:
    copied = 0
    for path in source.rglob("*"):
        relative = path.relative_to(source).as_posix()
        if relative.startswith(".git/") or is_preserved(relative):
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, nargs="?", default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    count = copy_upstream(args.source.resolve(), args.destination.resolve())
    print(f"copied {count} upstream files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
