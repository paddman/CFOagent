from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from .analytics import budget_variance, summarize_financials
from .cashflow import forecast_cash13
from .models import BudgetLine, CashWeek, FinancialPeriod


def _fmt(value: object, suffix: str = "") -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}{suffix}"
    return str(value)


def render_board_pack(
    company: str,
    periods: Sequence[FinancialPeriod],
    *,
    budget: Sequence[BudgetLine] = (),
    cash_weeks: Sequence[CashWeek] | None = None,
) -> str:
    summary = summarize_financials(periods)
    variances = budget_variance(budget) if budget else []
    cash = forecast_cash13(cash_weeks) if cash_weeks else None
    generated = datetime.now(timezone.utc).isoformat()

    lines = [
        f"# {company} — CFO Board Pack",
        "",
        f"Generated: {generated}",
        "",
        "## Executive dashboard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Reporting period | {summary['latest_period']} |",
        f"| Revenue | {_fmt(summary['revenue'])} |",
        f"| Revenue growth | {_fmt(summary['revenue_growth_pct'], '%')} |",
        f"| Gross margin | {_fmt(summary['gross_margin_pct'], '%')} |",
        f"| EBITDA | {_fmt(summary['ebitda'])} |",
        f"| EBITDA margin | {_fmt(summary['ebitda_margin_pct'], '%')} |",
        f"| Cash | {_fmt(summary['cash'])} |",
        f"| Net debt | {_fmt(summary['net_debt'])} |",
        f"| Cash conversion cycle | {_fmt(summary['cash_conversion_cycle_days'], ' days')} |",
        f"| Cash runway | {_fmt(summary['cash_runway_months'], ' months')} |",
        "",
    ]

    if variances:
        lines.extend(
            [
                "## Budget variance",
                "",
                "| Account | Actual | Budget | Variance | Variance % | Material |",
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for row in variances:
            lines.append(
                f"| {row['account']} | {_fmt(row['actual'])} | {_fmt(row['budget'])} | "
                f"{_fmt(row['variance'])} | {_fmt(row['variance_pct'], '%')} | "
                f"{'Yes' if row['material'] else 'No'} |"
            )
        lines.append("")

    if cash:
        lines.extend(
            [
                "## Liquidity",
                "",
                f"- Status: **{cash['liquidity_status']}**",
                f"- Ending cash: {_fmt(cash['ending_cash'])}",
                f"- Lowest cash: {_fmt(cash['lowest_cash'])}",
                f"- Breach weeks: {', '.join(cash['breach_weeks']) or 'none'}",
                "",
            ]
        )

    risks = []
    if (summary.get("ebitda") or 0) < 0:
        risks.append("EBITDA is negative; validate cost actions and liquidity runway.")
    if cash and cash["breach_weeks"]:
        risks.append("The cash forecast breaches minimum liquidity; funding action is required.")
    material = [row for row in variances if row["material"]]
    if material:
        risks.append(f"{len(material)} budget accounts exceed the 10% materiality threshold.")
    if not risks:
        risks.append("No deterministic threshold breach was identified in the supplied data.")

    lines.extend(["## Risks and actions", ""])
    for risk in risks:
        lines.append(f"- {risk}")
    lines.extend(
        [
            "",
            "## Governance note",
            "",
            "This pack is analytical and read-only. Payment release, journal posting, tax "
            "submission, payroll release, bank-detail changes, trade execution, and final "
            "external publication require authorized human approval.",
            "",
        ]
    )
    return "\n".join(lines)
