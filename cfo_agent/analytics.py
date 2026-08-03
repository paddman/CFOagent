from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from statistics import median
from typing import Iterable, Mapping, Sequence

from .models import BudgetLine, FinancialPeriod, ZERO, decimal_json, money, percent


TWO = Decimal("2")
HUNDRED = Decimal("100")


def summarize_financials(periods: Sequence[FinancialPeriod]) -> dict[str, object]:
    if not periods:
        raise ValueError("at least one financial period is required")
    ordered = sorted(periods, key=lambda row: row.period)
    latest = ordered[-1]
    prior = ordered[-2] if len(ordered) > 1 else None
    gross_profit = latest.revenue - latest.cogs
    ebitda = gross_profit - latest.opex
    working_capital = latest.receivables + latest.inventory - latest.payables
    net_debt = latest.debt - latest.cash
    revenue_growth = (
        percent(latest.revenue - prior.revenue, prior.revenue) if prior else None
    )
    return decimal_json(
        {
            "latest_period": latest.period,
            "revenue": latest.revenue,
            "gross_profit": gross_profit,
            "gross_margin_pct": percent(gross_profit, latest.revenue),
            "ebitda": ebitda,
            "ebitda_margin_pct": percent(ebitda, latest.revenue),
            "cash": latest.cash,
            "debt": latest.debt,
            "net_debt": net_debt,
            "working_capital": working_capital,
            "revenue_growth_pct": revenue_growth,
            "period_count": len(ordered),
        }
    )


def budget_variance(
    lines: Iterable[BudgetLine],
    *,
    materiality_pct: Decimal = Decimal("10"),
    materiality_amount: Decimal = Decimal("100000"),
) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"actual": ZERO, "budget": ZERO}
    )
    for line in lines:
        grouped[line.account]["actual"] += line.actual
        grouped[line.account]["budget"] += line.budget

    result = []
    for account, values in grouped.items():
        variance = values["actual"] - values["budget"]
        variance_pct = percent(variance, abs(values["budget"]))
        material = abs(variance) >= materiality_amount or (
            variance_pct is not None and abs(variance_pct) >= materiality_pct
        )
        result.append(
            decimal_json(
                {
                    "account": account,
                    "actual": values["actual"],
                    "budget": values["budget"],
                    "variance": variance,
                    "variance_pct": variance_pct,
                    "material": material,
                }
            )
        )
    return sorted(result, key=lambda row: abs(row["variance"]), reverse=True)


def detect_anomalies(
    values: Sequence[Decimal | int | float | str],
    *,
    threshold: Decimal = Decimal("3.5"),
) -> list[dict[str, object]]:
    series = [money(value) for value in values]
    if len(series) < 3:
        return []
    center = median(series)
    deviations = [abs(value - center) for value in series]
    mad = median(deviations)
    if mad == ZERO:
        return [
            decimal_json(
                {
                    "index": index,
                    "value": value,
                    "score": None,
                    "reason": "value differs while median absolute deviation is zero",
                }
            )
            for index, value in enumerate(series)
            if value != center
        ]

    anomalies = []
    scale = Decimal("0.6745")
    for index, value in enumerate(series):
        score = scale * (value - center) / mad
        if abs(score) >= threshold:
            anomalies.append(
                decimal_json(
                    {
                        "index": index,
                        "value": value,
                        "score": score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                        "reason": "robust z-score exceeded threshold",
                    }
                )
            )
    return anomalies


def scenario_analysis(
    base_revenue: Decimal | int | float | str,
    base_gross_margin_pct: Decimal | int | float | str,
    base_opex: Decimal | int | float | str,
    scenarios: Mapping[str, Mapping[str, Decimal | int | float | str]],
) -> list[dict[str, object]]:
    revenue = money(base_revenue)
    margin = money(base_gross_margin_pct)
    opex = money(base_opex)
    output = []
    for name, assumptions in scenarios.items():
        revenue_growth = money(assumptions.get("revenue_growth_pct", ZERO))
        margin_delta = money(assumptions.get("gross_margin_delta_pct", ZERO))
        opex_growth = money(assumptions.get("opex_growth_pct", ZERO))
        scenario_revenue = revenue * (Decimal("1") + revenue_growth / HUNDRED)
        scenario_margin = margin + margin_delta
        gross_profit = scenario_revenue * scenario_margin / HUNDRED
        scenario_opex = opex * (Decimal("1") + opex_growth / HUNDRED)
        ebitda = gross_profit - scenario_opex
        output.append(
            decimal_json(
                {
                    "scenario": name,
                    "revenue": scenario_revenue,
                    "gross_margin_pct": scenario_margin,
                    "gross_profit": gross_profit,
                    "opex": scenario_opex,
                    "ebitda": ebitda,
                    "ebitda_margin_pct": percent(ebitda, scenario_revenue),
                }
            )
        )
    return output
