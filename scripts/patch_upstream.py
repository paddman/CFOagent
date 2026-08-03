from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_readme(root: Path, upstream_sha: str) -> str:
    cfo_readme = (root / "README_CFO.md").read_text(encoding="utf-8")
    upstream_notice = f"""
## Upstream foundation

CFOAgent is built on the MIT-licensed `NousResearch/hermes-agent` runtime.
The bootstrap used upstream commit `{upstream_sha}`. The untouched upstream
README is preserved as `UPSTREAM_README.md`; upstream license and attribution
files remain in this repository.

Official optional finance skills copied from Hermes retain the author and
Apache-2.0 metadata embedded in each `SKILL.md`.
""".strip()
    return cfo_readme.rstrip() + "\n\n" + upstream_notice + "\n"


def patch(root: Path, upstream_sha: str) -> None:
    if not upstream_sha or len(upstream_sha) < 7:
        raise ValueError("a valid upstream commit SHA is required")

    metadata = {
        "upstream_repository": "https://github.com/NousResearch/hermes-agent",
        "upstream_commit": upstream_sha,
        "runtime_license": "MIT",
        "official_finance_skills_license": "Apache-2.0",
        "cfoagent_version": "0.3.0",
    }
    cfo_dir = root / ".cfo"
    cfo_dir.mkdir(parents=True, exist_ok=True)
    (cfo_dir / "upstream.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        build_readme(root, upstream_sha),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-sha", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    patch(args.root.resolve(), args.upstream_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
