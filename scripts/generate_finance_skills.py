from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfo_agent.skills import SKILLS, catalog_json, generate_skill_tree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("skills/finance-cfo"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    written = generate_skill_tree(args.destination)
    (args.destination / "catalog.json").write_text(
        catalog_json(),
        encoding="utf-8",
    )
    if len(written) != len(SKILLS):
        raise SystemExit(
            f"skill generation mismatch: expected {len(SKILLS)}, wrote {len(written)}"
        )
    print(f"generated {len(written)} CFO finance skills in {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
