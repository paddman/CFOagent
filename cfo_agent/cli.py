from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Sequence

from .analytics import (
    budget_variance,
    detect_anomalies,
    scenario_analysis,
    summarize_financials,
)
from .api import create_app
from .audit import AuditLog
from .board import render_board_pack
from .cashflow import forecast_cash13, render_cash13_markdown
from .io import read_budget, read_cash13, read_financials, write_json
from .models import BudgetLine, CashWeek, FinancialPeriod, decimal_json
from .policy import evaluate_action
from .router import route_task
from .skills import SKILLS, catalog_json, generate_skill_tree, search_skills
from .sqlite import query_read_only


VERSION = "0.3.0"


def _json_text(value: Any) -> str:
    return json.dumps(
        decimal_json(value),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _write_or_print(text: str, output: str | Path | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        print(path)
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _sample_financials() -> list[FinancialPeriod]:
    return [
        FinancialPeriod.from_mapping(
            {
                "period": "2026-05",
                "revenue": "9200000",
                "cogs": "4300000",
                "opex": "3900000",
                "cash": "6800000",
                "receivables": "2400000",
                "payables": "1700000",
                "inventory": "800000",
                "debt": "3100000",
            }
        ),
        FinancialPeriod.from_mapping(
            {
                "period": "2026-06",
                "revenue": "10100000",
                "cogs": "4550000",
                "opex": "4000000",
                "cash": "7200000",
                "receivables": "2600000",
                "payables": "1800000",
                "inventory": "840000",
                "debt": "3000000",
            }
        ),
    ]


def _sample_budget() -> list[BudgetLine]:
    return [
        BudgetLine.from_mapping(
            {"period": "2026-06", "account": "Revenue", "actual": 10100000, "budget": 9800000}
        ),
        BudgetLine.from_mapping(
            {"period": "2026-06", "account": "COGS", "actual": 4550000, "budget": 4410000}
        ),
        BudgetLine.from_mapping(
            {"period": "2026-06", "account": "Operating Expense", "actual": 4000000, "budget": 3850000}
        ),
    ]


def _sample_cash() -> list[CashWeek]:
    rows: list[CashWeek] = []
    for index in range(1, 14):
        rows.append(
            CashWeek.from_mapping(
                {
                    "week": f"W{index:02d}",
                    "opening_cash": "5000000" if index == 1 else "",
                    "inflows": str(1250000 + (index % 3) * 90000),
                    "outflows": str(1180000 + (index % 4) * 120000),
                    "minimum_cash": "2000000",
                }
            )
        )
    return rows


def command_demo(args: argparse.Namespace) -> int:
    home = Path(args.home)
    home.mkdir(parents=True, exist_ok=True)
    text = render_board_pack(
        args.company,
        _sample_financials(),
        budget=_sample_budget(),
        cash_weeks=_sample_cash(),
    )
    _write_or_print(text, args.output)
    AuditLog(home / "audit.jsonl").append(
        "demo-board-pack",
        actor="cli",
        payload={"company": args.company, "output": str(args.output or "stdout")},
    )
    return 0


def command_analyze(args: argparse.Namespace) -> int:
    financials = read_financials(args.financials)
    result: dict[str, object] = {"summary": summarize_financials(financials)}
    budget = read_budget(args.budget) if args.budget else []
    cash = read_cash13(args.cash) if args.cash else []
    if budget:
        result["budget_variance"] = budget_variance(budget)
    if cash:
        result["cash13"] = forecast_cash13(cash)

    if args.format == "markdown":
        text = render_board_pack(
            args.company,
            financials,
            budget=budget,
            cash_weeks=cash or None,
        )
    else:
        text = _json_text(result)
    _write_or_print(text, args.output)
    return 0


def command_cash13(args: argparse.Namespace) -> int:
    result = forecast_cash13(read_cash13(args.csv))
    text = _json_text(result) if args.format == "json" else render_cash13_markdown(result)
    _write_or_print(text, args.output)
    return 0


def command_skills(args: argparse.Namespace) -> int:
    if args.install:
        written = generate_skill_tree(args.install)
        catalog_path = Path(args.install) / "catalog.json"
        catalog_path.write_text(catalog_json(), encoding="utf-8")
        _write_or_print(
            _json_text(
                {
                    "installed": len(written),
                    "destination": str(Path(args.install).resolve()),
                    "catalog": str(catalog_path.resolve()),
                }
            ),
            args.output,
        )
        return 0

    items = search_skills(args.query or "", limit=args.limit)
    if args.json:
        _write_or_print(_json_text({"count": len(SKILLS), "items": items}), args.output)
        return 0

    lines = [f"CFOAgent finance skills: {len(SKILLS)}", ""]
    for item in items:
        score = f" score={item['score']}" if "score" in item else ""
        lines.append(
            f"- {item['slug']}: {item['title']} [{item['category']}]{score}\n"
            f"  {item['description']}"
        )
    _write_or_print("\n".join(lines) + "\n", args.output)
    return 0


def command_route(args: argparse.Namespace) -> int:
    _write_or_print(_json_text(route_task(args.text, limit=args.limit)), args.output)
    return 0


def command_policy(args: argparse.Namespace) -> int:
    decision = evaluate_action(args.action, authorized=args.authorized)
    _write_or_print(_json_text(asdict(decision)), args.output)
    return 0 if decision.allowed else 2


def command_anomalies(args: argparse.Namespace) -> int:
    values = [Decimal(item.strip()) for item in args.values.split(",") if item.strip()]
    result = detect_anomalies(values, threshold=Decimal(str(args.threshold)))
    _write_or_print(_json_text({"items": result}), args.output)
    return 0


def command_scenario(args: argparse.Namespace) -> int:
    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    result = scenario_analysis(
        args.base_revenue,
        args.base_gross_margin,
        args.base_opex,
        scenarios,
    )
    _write_or_print(_json_text({"items": result}), args.output)
    return 0


def command_sqlite(args: argparse.Namespace) -> int:
    result = query_read_only(
        args.database,
        args.sql,
        row_limit=args.limit,
    )
    _write_or_print(_json_text({"items": result}), args.output)
    return 0


def command_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("uvicorn is required for the serve command") from exc
    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cfo",
        description="CFOAgent deterministic finance operating system",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument(
        "--home",
        default=str(Path.home() / ".cfoagent"),
        help="state directory for audit logs and generated artifacts",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="generate a deterministic sample board pack")
    demo.add_argument("--company", default="CFOAgent Demo Company")
    demo.add_argument("--output")
    demo.set_defaults(func=command_demo)

    analyze = subparsers.add_parser("analyze", help="analyze financial CSV files")
    analyze.add_argument("financials")
    analyze.add_argument("--budget")
    analyze.add_argument("--cash")
    analyze.add_argument("--company", default="Company")
    analyze.add_argument("--format", choices=("json", "markdown"), default="json")
    analyze.add_argument("--output")
    analyze.set_defaults(func=command_analyze)

    cash13 = subparsers.add_parser("cash13", help="build a 13-week cash forecast")
    cash13.add_argument("csv")
    cash13.add_argument("--format", choices=("json", "markdown"), default="markdown")
    cash13.add_argument("--output")
    cash13.set_defaults(func=command_cash13)

    skills = subparsers.add_parser("skills", help="search or install finance skills")
    skills.add_argument("query", nargs="?", default="")
    skills.add_argument("--limit", type=int, default=10)
    skills.add_argument("--json", action="store_true")
    skills.add_argument("--install")
    skills.add_argument("--output")
    skills.set_defaults(func=command_skills)

    route = subparsers.add_parser("route", help="route a task to a CFO specialist")
    route.add_argument("text")
    route.add_argument("--limit", type=int, default=5)
    route.add_argument("--output")
    route.set_defaults(func=command_route)

    policy = subparsers.add_parser("policy", help="evaluate an action control boundary")
    policy.add_argument("action")
    policy.add_argument("--authorized", action="store_true")
    policy.add_argument("--output")
    policy.set_defaults(func=command_policy)

    anomalies = subparsers.add_parser("anomalies", help="detect robust-z anomalies")
    anomalies.add_argument("values", help="comma-separated numeric values")
    anomalies.add_argument("--threshold", type=float, default=3.5)
    anomalies.add_argument("--output")
    anomalies.set_defaults(func=command_anomalies)

    scenario = subparsers.add_parser("scenario", help="run finance scenarios from JSON")
    scenario.add_argument("scenarios", help="JSON file keyed by scenario name")
    scenario.add_argument("--base-revenue", required=True)
    scenario.add_argument("--base-gross-margin", required=True)
    scenario.add_argument("--base-opex", required=True)
    scenario.add_argument("--output")
    scenario.set_defaults(func=command_scenario)

    sqlite_cmd = subparsers.add_parser("sqlite", help="run a read-only SQLite query")
    sqlite_cmd.add_argument("database")
    sqlite_cmd.add_argument("sql")
    sqlite_cmd.add_argument("--limit", type=int, default=1000)
    sqlite_cmd.add_argument("--output")
    sqlite_cmd.set_defaults(func=command_sqlite)

    serve = subparsers.add_parser("serve", help="start the optional FastAPI service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.set_defaults(func=command_serve)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"cfo: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
