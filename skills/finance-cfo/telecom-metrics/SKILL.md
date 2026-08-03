---
name: telecom-metrics
description: Analyze subscribers, ARPU, churn, traffic, network costs, capex intensity, and service margin.
version: 1.0.0
author: CFOAgent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: ["finance", "industry-data", "data", "analytics", "metrics", "telecom"]
    related_skills: ["saas-metrics", "idc-cloud-unit-economics", "project-profitability", "data-quality-finance"]
---

# Telecom Metrics

Analyze subscribers, ARPU, churn, traffic, network costs, capex intensity, and service margin.

## When to use

Use this skill for governed Industry and Finance Data work when the user requests
analysis, a workpaper, a forecast, a model review, a reconciliation, or a
decision pack related to **Telecom Metrics**.

## Required inputs

- source schemas, data dictionary, grain, keys, lineage, and refresh schedule
- finance metric definitions, owner, dimensions, and reconciliation target
- quality thresholds, access classification, and exception workflow

If a required input is missing, label it explicitly. Do not invent balances,
rates, contractual terms, approvals, evidence, or current regulatory facts.

## Procedure

1. Profile schema, completeness, uniqueness, validity, consistency, and timeliness.
2. Map source fields to governed finance definitions and transformation rules.
3. Reconcile row counts, control totals, balances, and period coverage.
4. Calculate metrics or anomalies with reproducible code and explainable thresholds.
5. Publish lineage, tests, exceptions, confidence, and reviewer status.

## Output contract

- validated dataset or metric table
- quality and reconciliation report
- lineage, confidence, exceptions, and remediation owners

Every output must separate **facts**, **calculations**, **assumptions**,
**estimates**, and **management judgment**. Include source, as-of date, entity,
currency, units, materiality, preparer status, and reviewer status.

## Verification

- source-to-output row counts and control totals reconcile
- metric grain, formula, unit, sign, currency, and time zone are explicit
- sensitive data is minimized, redacted, and access-controlled

Stop and report the exception when a control total, reconciliation, formula,
period, entity, currency, or source cannot be verified.

## Control boundary

This skill is read-only by default. It may draft, analyze, reconcile, simulate,
and prepare decision material. It must not release payments, post journals,
submit tax, release payroll, change bank details, execute trades, sign
contracts, or publish final external statements without authorized human approval.

## Reference classes

- approved finance data dictionary and metric layer
- source-system documentation, lineage records, and data quality policy

For accounting standards, tax, law, market data, and filing requirements,
verify the current authoritative source at execution time and record the date.
