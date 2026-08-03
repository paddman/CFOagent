---
name: payment-controls
description: Design maker-checker payment controls, validation, duplicate detection, and release evidence.
version: 1.0.0
author: CFOAgent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["finance", "treasury", "cash", "liquidity", "payment", "controls"]
    related_skills: ["cash-position", "thirteen-week-cash-flow", "liquidity-risk", "working-capital"]
---

# Payment Controls

Design maker-checker payment controls, validation, duplicate detection, and release evidence.

## When to use

Use this skill for governed Treasury work when the user requests
analysis, a workpaper, a forecast, a model review, a reconciliation, or a
decision pack related to **Payment Controls**.

## Required inputs

- bank, ledger, debt, forecast, covenant, and counterparty data
- availability restrictions, value dates, currencies, and legal entities
- treasury policy, limits, signatories, and approval matrix

If a required input is missing, label it explicitly. Do not invent balances,
rates, contractual terms, approvals, evidence, or current regulatory facts.

## Procedure

1. Reconcile source balances and establish available versus restricted liquidity.
2. Model timing, currencies, facilities, covenants, and downside shocks.
3. Identify concentration, funding, market, counterparty, and operational risks.
4. Recommend actions with amount, timing, owner, approval, and fallback.
5. Record evidence and maintain maker-checker separation for execution.

## Output contract

- liquidity or exposure schedule
- threshold and covenant alerts
- action plan requiring authorized release where consequential

Every output must separate **facts**, **calculations**, **assumptions**,
**estimates**, and **management judgment**. Include source, as-of date, entity,
currency, units, materiality, preparer status, and reviewer status.

## Verification

- bank, debt, and ledger control totals reconcile
- value date, currency, legal entity, facility, and sign are correct
- no payment, transfer, hedge, or borrowing is executed automatically

Stop and report the exception when a control total, reconciliation, formula,
period, entity, currency, or source cannot be verified.

## Control boundary

This skill is read-only by default. It may draft, analyze, reconcile, simulate,
and prepare decision material. It must not release payments, post journals,
submit tax, release payroll, change bank details, execute trades, sign
contracts, or publish final external statements without authorized human approval.

## Reference classes

- approved treasury policy, bank mandates, and facility agreements
- authoritative bank confirmations and sourced market data

For accounting standards, tax, law, market data, and filing requirements,
verify the current authoritative source at execution time and record the date.
