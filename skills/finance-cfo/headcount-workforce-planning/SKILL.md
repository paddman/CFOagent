---
name: headcount-workforce-planning
description: Model workforce demand, hiring timing, compensation, productivity, and vacancy impacts.
version: 1.0.0
author: CFOAgent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["finance", "fpna", "planning", "forecasting", "performance", "headcount", "workforce", "and"]
    related_skills: ["annual-operating-plan", "rolling-forecast", "budget-variance-analysis", "management-reporting-pack"]
---

# Headcount and Workforce Planning

Model workforce demand, hiring timing, compensation, productivity, and vacancy impacts.

## When to use

Use this skill for governed FP&A work when the user requests
analysis, a workpaper, a forecast, a model review, a reconciliation, or a
decision pack related to **Headcount and Workforce Planning**.

## Required inputs

- governed actuals with entity, period, currency, and account mapping
- approved planning assumptions and operational drivers
- owners, materiality thresholds, and decision horizon

If a required input is missing, label it explicitly. Do not invent balances,
rates, contractual terms, approvals, evidence, or current regulatory facts.

## Procedure

1. Validate scope, period, currency, units, source lineage, and control totals.
2. Separate historical facts, management assumptions, and model-derived estimates.
3. Build the driver bridge and calculate outputs with reproducible formulas.
4. Run base, downside, and upside sensitivity where the decision is material.
5. Explain the largest movements, accountable owners, actions, and expected dates.

## Output contract

- machine-readable calculations and assumptions
- management summary with material drivers
- risk, opportunity, action, owner, and due-date table

Every output must separate **facts**, **calculations**, **assumptions**,
**estimates**, and **management judgment**. Include source, as-of date, entity,
currency, units, materiality, preparer status, and reviewer status.

## Verification

- totals reconcile to the approved source
- formulas, units, signs, periods, and scenario links are consistent
- material conclusions are traceable to data or explicit assumptions

Stop and report the exception when a control total, reconciliation, formula,
period, entity, currency, or source cannot be verified.

## Control boundary

This skill is read-only by default. It may draft, analyze, reconcile, simulate,
and prepare decision material. It must not release payments, post journals,
submit tax, release payroll, change bank details, execute trades, sign
contracts, or publish final external statements without authorized human approval.

## Reference classes

- company-approved planning policy and management reporting definitions
- source ERP, billing, CRM, workforce, and operational systems

For accounting standards, tax, law, market data, and filing requirements,
verify the current authoritative source at execution time and record the date.
