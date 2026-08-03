---
name: capital-allocation
description: Prioritize investment, debt reduction, dividends, repurchases, and liquidity using explicit hurdle rates.
version: 1.0.0
author: CFOAgent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["finance", "corporate-finance", "valuation", "investment", "m&a", "capital", "allocation"]
    related_skills: ["business-case", "wacc-cost-of-capital", "dcf-review", "comparable-companies"]
---

# Capital Allocation

Prioritize investment, debt reduction, dividends, repurchases, and liquidity using explicit hurdle rates.

## When to use

Use this skill for governed Corporate Finance and M&A work when the user requests
analysis, a workpaper, a forecast, a model review, a reconciliation, or a
decision pack related to **Capital Allocation**.

## Required inputs

- historical financials, forecast, capital structure, and transaction assumptions
- market data with source and retrieval date
- strategic objectives, hurdle rates, constraints, and approval authority

If a required input is missing, label it explicitly. Do not invent balances,
rates, contractual terms, approvals, evidence, or current regulatory facts.

## Procedure

1. Validate historicals, forecast logic, net debt, shares, and transaction perimeter.
2. Build transparent formulas for cash flow, valuation, financing, and returns.
3. Triangulate results using appropriate methods and sourced benchmarks.
4. Run sensitivities, downside cases, break-even points, and key risk analysis.
5. Present recommendation, valuation range, conditions, and unresolved diligence.

## Output contract

- auditable model or review workpaper
- valuation and returns range
- investment recommendation with conditions and approval gates

Every output must separate **facts**, **calculations**, **assumptions**,
**estimates**, and **management judgment**. Include source, as-of date, entity,
currency, units, materiality, preparer status, and reviewer status.

## Verification

- enterprise-to-equity bridge and cash/debt signs are correct
- market data, transaction assumptions, and dates are sourced
- model integrity and sensitivity center cases are verified

Stop and report the exception when a control total, reconciliation, formula,
period, entity, currency, or source cannot be verified.

## Control boundary

This skill is read-only by default. It may draft, analyze, reconcile, simulate,
and prepare decision material. It must not release payments, post journals,
submit tax, release payroll, change bank details, execute trades, sign
contracts, or publish final external statements without authorized human approval.

## Reference classes

- board-approved investment and capital allocation policy
- issuer filings and authoritative market-data sources

For accounting standards, tax, law, market data, and filing requirements,
verify the current authoritative source at execution time and record the date.
