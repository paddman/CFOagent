from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from statistics import median
from typing import Iterable, Sequence

from .models import BudgetLine, FinancialPeriod, HUNDRED, ZERO, decimal_json, money


def safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return numerator / denominator


def _percent(value: Decimal | None) -> Decimal | None:
    return None if value is None else value * HUNDRED


def summarize_financials(periods: Sequence[FinancialPeriod]) -> dict[str, object]:
    if not periods:
        raise ValueError("at least one financial period is required")
    latest = periods[-1]
    prior = periods[-2] if len(periods) > 1 else None

    gross_profit = latest.revenue - latest.cogs
    ebitda = gross_profit - latest.opex
    net_debt = latest.debt - latest.cash
    revenue_growth = (
        safe_ratio(latest.revenue - prior.revenue, prior.revenue)
        if prior is not None
        else None
    )

    annualized_revenue = latest.revenue * Decimal("12")
    dso = (
        safe_ratio(latest.receivables, annualized_revenue) * Decimal("365")
        if annualized_revenue
        else None
    )
    annualized_cogs = latest.cogs * Decimal("12")
    dpo = (
        safe_ratio(latest.payables, annualized_cogs) * Decimal("365")
        if annualized_cogs
        else None
    )
    dio = (
        safe_ratio(latest.inventory, annualized_cogs) * Decimal("365")
        if annualized_cogs
        else None
    )
    ccc = None
    if dso is not None and dpo is not None and dio is not None:
        ccc = dso + dio - dpo

    monthly_burn = -ebitda if ebitda < ZERO else ZERO
    cash_runway = safe_ratio(latest.cash, monthly_burn) if monthly_burn else None

    result = {
        "latest_period": latest.period,
        "revenue": latest.revenue,
        "revenue_growth_pct": _percent(revenue_growth),
        "gross_profit": gross_profit,
        "gross_margin_pct": _percent(safe_ratio(gross_profit, latest.revenue)),
        "ebitda": ebitda,
        "ebitda_margin_pct": _percent(safe_ratio(ebitda, latest.revenue)),
        "cash": latest.cash,
        "debt": latest.debt,
        "net_debt": net_debt,
        "receivables": latest.receivables,
        "payables": latest.payables,
        "inventory": latest.inventory,
        "dso_days": dso,
        "dpo_days": dpo,
        "dio_days": dio,
        "cash_conversion_cycle_days": ccc,
        "cash_runway_months": cash_runway,
    }
    return decimal_json(result)


def budget_variance(lines: Iterable[BudgetLine]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"actual": ZERO, "budget": ZERO}
    )
    for line in lines:
        grouped[line.account]["actual"] += line.actual
        grouped[line.account]["budget"] += line.budget

    output = []
    for account in sorted(grouped):
        actual = grouped[account]["actual"]
        budget = grouped[account]["budget"]
        variance = actual - budget
        variance_pct = safe_ratio(variance, abs(budget))
        output.append(
            decimal_json(
                {
                    "account": account,
                    "actual": actual,
                    "budget": budget,
                    "variance": variance,
                    "variance_pct": _percent(variance_pct),
                    "material": abs(variance_pct or ZERO) >= Decimal("0.10"),
                }
            )
        )
    return output


def detect_anomalies(
    values: Sequence[Decimal | int | float],
    *,
    threshold: Decimal | int | float = Decimal("3.5"),
) -> list[dict[str, object]]:
    if len(values) < 3:
        return []
    points = [money(value) for value in values]
    center = Decimal(str(median(points)))
    deviations = [abs(value - center) for value in points]
    mad = Decimal(str(median(deviations)))
    limit = money(threshold)

    findings = []
    for index, value in enumerate(points):
        if mad == ZERO:
            score = ZERO if value == center else Decimal("999")
        else:
            score = Decimal("0.6745") * (value - center) / mad
        if abs(score) >= limit:
            findings.append(
                decimal_json(
                    {
                        "index": index,
                        "value": value,
                        "robust_z_score": score,
                        "median": center,
                        "mad": mad,
                    }
                )
            )
    return findings


def scenario_analysis(
    base_revenue: Decimal | int | float,
    base_gross_margin_pct: Decimal | int | float,
    base_opex: Decimal | int | float,
    scenarios: dict[str, dict[str, Decimal | int | float]],
) -> list[dict[str, object]]:
    revenue = money(base_revenue)
    margin = money(base_gross_margin_pct) / HUNDRED
    opex = money(base_opex)
    results = []
    for name, assumptions in scenarios.items():
        growth = money(assumptions.get("revenue_growth_pct", 0)) / HUNDRED
        margin_delta = money(assumptions.get("gross_margin_delta_pct", 0)) / HUNDRED
        opex_growth = money(assumptions.get("opex_growth_pct", 0)) / HUNDRED
        projected_revenue = revenue * (Decimal("1") + growth)
        projected_gross_profit = projected_revenue * (margin + margin_delta)
        projected_opex = opex * (Decimal("1") + opex_growth)
        projected_ebitda = projected_gross_profit - projected_opex
        results.append(
            decimal_json(
                {
                    "scenario": name,
                    "revenue": projected_revenue,
                    "gross_profit": projected_gross_profit,
                    "opex": projected_opex,
                    "ebitda": projected_ebitda,
                    "ebitda_margin_pct": _percent(
                        safe_ratio(projected_ebitda, projected_revenue)
                    ),
                }
            )
        )
    return results
