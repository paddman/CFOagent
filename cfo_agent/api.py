from __future__ import annotations

from typing import Any

from .analytics import budget_variance, scenario_analysis, summarize_financials
from .cashflow import forecast_cash13
from .models import BudgetLine, CashWeek, FinancialPeriod
from .policy import evaluate_action
from .router import route_task
from .skills import search_skills


def _model_list(factory: type[Any], rows: list[dict[str, Any]]) -> list[Any]:
    return [factory.from_mapping(row) for row in rows]


def create_app():
    """Create the optional FastAPI application.

    FastAPI is intentionally an optional dependency. The deterministic CFO engine
    and CLI do not require a web framework.
    """
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "FastAPI is not installed. Install the Hermes web/API extras first."
        ) from exc

    app = FastAPI(
        title="CFOAgent API",
        version="0.3.0",
        description=(
            "Read-only CFO analytics, finance skill discovery, routing, and "
            "human-approval policy checks."
        ),
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "service": "cfoagent", "version": "0.3.0"}

    @app.get("/v1/skills")
    def skills(q: str = "", limit: int = 10) -> dict[str, object]:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
        return {"items": search_skills(q, limit=limit)}

    @app.post("/v1/route")
    def route(payload: dict[str, Any]) -> dict[str, object]:
        text = str(payload.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text is required")
        return route_task(text, limit=int(payload.get("limit", 5)))

    @app.post("/v1/financials/analyze")
    def financials(payload: dict[str, Any]) -> dict[str, object]:
        try:
            periods = _model_list(FinancialPeriod, list(payload.get("periods") or []))
            result: dict[str, object] = {
                "summary": summarize_financials(periods),
            }
            budget_rows = list(payload.get("budget") or [])
            if budget_rows:
                result["budget_variance"] = budget_variance(
                    _model_list(BudgetLine, budget_rows)
                )
            return result
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/cash13")
    def cash13(payload: dict[str, Any]) -> dict[str, object]:
        try:
            weeks = _model_list(CashWeek, list(payload.get("weeks") or []))
            return forecast_cash13(weeks)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/scenarios")
    def scenarios(payload: dict[str, Any]) -> dict[str, object]:
        try:
            rows = scenario_analysis(
                payload.get("base_revenue", 0),
                payload.get("base_gross_margin_pct", 0),
                payload.get("base_opex", 0),
                dict(payload.get("scenarios") or {}),
            )
            return {"items": rows}
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/v1/policy")
    def policy(payload: dict[str, Any]) -> dict[str, object]:
        action = str(payload.get("action") or "").strip()
        if not action:
            raise HTTPException(status_code=400, detail="action is required")
        decision = evaluate_action(
            action,
            authorized=bool(payload.get("authorized", False)),
        )
        return {
            "action": decision.action,
            "allowed": decision.allowed,
            "requires_human": decision.requires_human,
            "reason": decision.reason,
        }

    return app
