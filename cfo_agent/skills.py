from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class FinanceSkill:
    slug: str
    title: str
    category: str
    description: str
    tags: tuple[str, ...]


_SKILL_ROWS = [('annual-operating-plan', 'Annual Operating Plan', 'fpna', 'Build an integrated annual operating plan with drivers, owners, scenarios, and approval gates.'),
 ('rolling-forecast', 'Rolling Forecast', 'fpna', 'Maintain a driver-based rolling forecast with monthly actuals, reforecast logic, and decision triggers.'),
 ('budget-variance-analysis', 'Budget Variance Analysis', 'fpna', 'Analyze actual versus budget, isolate rate-volume-mix drivers, and produce accountable actions.'),
 ('management-reporting-pack', 'Management Reporting Pack', 'fpna', 'Produce a concise monthly management pack with KPI trends, material variances, risks, and actions.'),
 ('board-pack', 'Board Finance Pack', 'fpna', 'Create decision-ready board finance materials with performance, liquidity, outlook, risks, and asks.'),
 ('driver-based-planning', 'Driver-Based Planning', 'fpna', 'Translate operational drivers into revenue, cost, headcount, cash, and capacity forecasts.'),
 ('scenario-stress-testing', 'Scenario and Stress Testing', 'fpna', 'Build bear, base, and bull scenarios and quantify financial resilience under explicit shocks.'),
 ('headcount-workforce-planning', 'Headcount and Workforce Planning', 'fpna', 'Model workforce demand, hiring timing, compensation, productivity, and vacancy impacts.'),
 ('unit-economics', 'Unit Economics', 'fpna', 'Measure contribution margin, CAC, LTV, payback, retention, and scalable growth economics.'),
 ('pricing-profitability', 'Pricing and Profitability', 'fpna', 'Evaluate pricing, discounting, mix, customer profitability, and margin leakage.'),
 ('cost-optimization', 'Cost Optimization', 'fpna', 'Identify sustainable cost actions using spend, activity, service level, and risk trade-offs.'),
 ('kpi-tree-design', 'KPI Tree Design', 'fpna', 'Design a traceable KPI tree linking operational drivers to P&L, cash flow, and enterprise value.'),
 ('break-even-analysis', 'Break-Even Analysis', 'fpna', 'Calculate contribution margin, break-even volume, margin of safety, and sensitivity.'),
 ('forecast-accuracy', 'Forecast Accuracy', 'fpna', 'Measure forecast bias, error, volatility, and corrective actions by horizon and owner.'),
 ('profitability-by-customer-product', 'Customer and Product Profitability', 'fpna', 'Allocate direct and support costs to reveal profitability by customer, product, channel, or contract.'),
 ('month-end-close', 'Month-End Close', 'accounting', 'Run a controlled period-end close with dependencies, evidence, reviews, and final lock.'),
 ('account-reconciliation', 'Account Reconciliation', 'accounting', 'Reconcile general ledger balances to independent evidence and resolve aged differences.'),
 ('journal-entry-review', 'Journal Entry Review', 'accounting', 'Validate journal support, accounting logic, balance, period, entity, and approval.'),
 ('trial-balance-review', 'Trial Balance Review', 'accounting', 'Perform analytical and structural review of a trial balance before reporting.'),
 ('financial-statement-preparation', 'Financial Statement Preparation', 'accounting', 'Prepare internally consistent primary statements with tie-outs, classifications, and disclosures.'),
 ('consolidation', 'Group Consolidation', 'accounting', 'Consolidate entities with mapping, ownership, foreign currency, eliminations, and control checks.'),
 ('intercompany-reconciliation', 'Intercompany Reconciliation', 'accounting', 'Match intercompany balances and transactions and resolve timing, FX, and coding differences.'),
 ('revenue-recognition-ifrs15', 'IFRS 15 Revenue Recognition', 'accounting', 'Apply the five-step revenue model and document performance obligations, timing, and judgments.'),
 ('lease-accounting-ifrs16', 'IFRS 16 Lease Accounting', 'accounting', 'Build lease schedules and account for right-of-use assets, liabilities, modifications, and disclosures.'),
 ('financial-instruments-ifrs9', 'IFRS 9 Financial Instruments', 'accounting', 'Classify and measure financial instruments and support impairment and hedge-accounting analysis.'),
 ('expected-credit-loss', 'Expected Credit Loss', 'accounting', 'Develop governed ECL staging, PD, LGD, EAD, forward-looking overlays, and disclosures.'),
 ('impairment-ias36', 'IAS 36 Impairment Testing', 'accounting', 'Test assets and cash-generating units for impairment using supportable cash flows and discount rates.'),
 ('provisions-ias37', 'IAS 37 Provisions and Contingencies', 'accounting', 'Assess present obligations, probability, measurement, uncertainty, and disclosure.'),
 ('income-taxes-ias12', 'IAS 12 Income Taxes', 'accounting', 'Prepare current and deferred tax accounting with temporary differences and recoverability evidence.'),
 ('foreign-currency-ias21', 'IAS 21 Foreign Currency', 'accounting', 'Determine functional currency and account for transactions, translation, and exchange differences.'),
 ('business-combinations-ifrs3', 'IFRS 3 Business Combinations', 'accounting', 'Apply acquisition accounting, purchase price allocation, goodwill, and measurement-period controls.'),
 ('segment-reporting-ifrs8', 'IFRS 8 Segment Reporting', 'accounting', 'Identify operating segments from management reporting and prepare consistent disclosures.'),
 ('cash-flow-statement', 'Cash Flow Statement', 'accounting', 'Build and reconcile operating, investing, and financing cash flows with non-cash disclosures.'),
 ('accounting-policy-memo', 'Accounting Policy Memo', 'accounting', 'Write evidence-based accounting memos separating facts, guidance, analysis, judgment, and conclusion.'),
 ('disclosure-checklist', 'Financial Statement Disclosure Checklist', 'accounting', 'Run a governed disclosure checklist with applicability, evidence, preparer, and reviewer sign-off.'),
 ('chart-of-accounts-governance', 'Chart of Accounts Governance', 'accounting', 'Govern account creation, hierarchy, mappings, ownership, usage rules, and change control.'),
 ('fixed-assets-accounting', 'Fixed Assets Accounting', 'accounting', 'Control capitalization, useful lives, depreciation, transfers, disposals, and physical verification.'),
 ('cash-position', 'Daily Cash Position', 'treasury', 'Produce an entity and bank-level cash position with availability, restrictions, and concentration.'),
 ('thirteen-week-cash-flow', '13-Week Cash Flow Forecast', 'treasury', 'Build a rolling direct-method cash forecast with weekly liquidity and breach alerts.'),
 ('liquidity-risk', 'Liquidity Risk Management', 'treasury', 'Set liquidity buffers, stress scenarios, contingency actions, and escalation thresholds.'),
 ('working-capital', 'Working Capital Management', 'treasury', 'Improve DSO, DIO, DPO, cash conversion cycle, and cross-functional cash accountability.'),
 ('bank-reconciliation', 'Bank Reconciliation', 'treasury', 'Reconcile bank statements to the ledger and investigate timing, fees, errors, and fraud indicators.'),
 ('bank-account-governance', 'Bank Account Governance', 'treasury', 'Govern bank accounts, signatories, access, mandates, confirmations, and dormant-account closure.'),
 ('payment-controls', 'Payment Controls', 'treasury', 'Design maker-checker payment controls, validation, duplicate detection, and release evidence.'),
 ('debt-covenant-monitoring', 'Debt and Covenant Monitoring', 'treasury', 'Maintain debt schedules, covenant calculations, headroom forecasts, and early-warning escalation.'),
 ('debt-capacity', 'Debt Capacity', 'treasury', 'Assess sustainable leverage, debt service, downside headroom, and refinancing risk.'),
 ('fx-exposure', 'Foreign Exchange Exposure', 'treasury', 'Identify transaction, translation, and economic FX exposures with natural offsets.'),
 ('fx-hedging', 'FX Hedging', 'treasury', 'Design governed FX hedge strategies, instruments, effectiveness measures, and controls.'),
 ('interest-rate-risk', 'Interest Rate Risk', 'treasury', 'Measure fixed-floating exposure, duration, repricing gaps, and rate-shock sensitivity.'),
 ('cash-pooling', 'Cash Pooling and Intercompany Funding', 'treasury', 'Design cash concentration and intercompany funding with legal, tax, liquidity, and accounting controls.'),
 ('treasury-policy', 'Treasury Policy', 'treasury', 'Create a treasury policy covering liquidity, investments, funding, FX, counterparties, and approvals.'),
 ('capital-allocation', 'Capital Allocation', 'corporate-finance', 'Prioritize investment, debt reduction, dividends, repurchases, and liquidity using explicit hurdle rates.'),
 ('business-case', 'Investment Business Case', 'corporate-finance', 'Build an auditable business case with cash flows, NPV, IRR, payback, scenarios, and benefits ownership.'),
 ('wacc-cost-of-capital', 'WACC and Cost of Capital', 'corporate-finance', 'Estimate cost of equity, debt, capital structure, and sensitivity with sourced market inputs.'),
 ('dcf-review', 'DCF Model Review', 'corporate-finance', 'Review DCF architecture, forecast logic, terminal value, discounting, bridge, and sensitivities.'),
 ('comparable-companies', 'Comparable Company Analysis', 'corporate-finance', 'Select peers, normalize metrics, calculate trading multiples, and interpret valuation ranges.'),
 ('precedent-transactions', 'Precedent Transaction Analysis', 'corporate-finance', 'Analyze comparable deals, premiums, synergies, cycle effects, and valuation ranges.'),
 ('lbo-review', 'LBO Model Review', 'corporate-finance', 'Review sources and uses, debt paydown, cash sweeps, covenants, returns, and downside cases.'),
 ('ma-screening', 'M&A Target Screening', 'corporate-finance', 'Score acquisition targets against strategy, economics, capabilities, risk, and integration feasibility.'),
 ('ma-due-diligence', 'M&A Financial Due Diligence', 'corporate-finance', 'Assess quality of earnings, working capital, debt-like items, tax, controls, and forecast credibility.'),
 ('quality-of-earnings', 'Quality of Earnings', 'corporate-finance', 'Normalize EBITDA and cash conversion by separating recurring performance from one-offs and policy effects.'),
 ('purchase-price-allocation', 'Purchase Price Allocation', 'corporate-finance', 'Support fair-value allocation to identifiable assets and liabilities and derive goodwill.'),
 ('merger-model-review', 'Merger Model Review', 'corporate-finance', 'Review transaction mechanics, financing, synergies, purchase accounting, and accretion or dilution.'),
 ('post-merger-integration-finance', 'Post-Merger Finance Integration', 'corporate-finance', 'Plan Day 1 controls, close, treasury, reporting, systems, synergy tracking, and governance.'),
 ('ipo-readiness', 'IPO Readiness', 'corporate-finance', 'Assess reporting, controls, governance, forecast, data, audit, and public-company readiness.'),
 ('internal-control-framework', 'Internal Control Framework', 'risk-controls', 'Design entity, process, and technology controls using objectives, risks, ownership, and evidence.'),
 ('risk-control-matrix', 'Risk and Control Matrix', 'risk-controls', 'Map process risks to control objectives, activities, owners, frequency, evidence, and testing.'),
 ('segregation-of-duties', 'Segregation of Duties', 'risk-controls', 'Identify incompatible finance access and design preventive or compensating controls.'),
 ('access-review-finance', 'Finance Access Review', 'risk-controls', 'Perform periodic access certification for ERP, banking, payroll, tax, and reporting systems.'),
 ('fraud-risk-assessment', 'Fraud Risk Assessment', 'risk-controls', 'Assess fraud schemes, incentives, opportunities, controls, indicators, and response plans.'),
 ('journal-entry-testing', 'Journal Entry Testing', 'risk-controls', 'Risk-rank journals and test unusual users, times, accounts, amounts, and descriptions.'),
 ('duplicate-payment-detection', 'Duplicate Payment Detection', 'risk-controls', 'Detect likely duplicate invoices and payments with explainable matching rules.'),
 ('vendor-master-controls', 'Vendor Master Controls', 'risk-controls', 'Control vendor onboarding, changes, bank validation, duplicates, conflicts, and periodic review.'),
 ('expense-analytics', 'Expense and T&E Analytics', 'risk-controls', 'Detect policy exceptions, duplicate claims, split transactions, outliers, and suspicious patterns.'),
 ('continuous-controls-monitoring', 'Continuous Controls Monitoring', 'risk-controls', 'Run scheduled control analytics with evidence, case management, aging, and remediation.'),
 ('audit-planning', 'Risk-Based Audit Planning', 'risk-controls', 'Prioritize audit coverage using impact, likelihood, change, control maturity, and prior findings.'),
 ('audit-pbc-management', 'Audit PBC Management', 'risk-controls', 'Manage audit requests, owners, evidence quality, due dates, and secure delivery.'),
 ('control-testing', 'Control Design and Operating Effectiveness Testing', 'risk-controls', 'Test control design, population completeness, sample execution, evidence, and exceptions.'),
 ('financial-close-controls', 'Financial Close Controls', 'risk-controls', 'Design and monitor controls over close, consolidation, review, disclosures, and period lock.'),
 ('going-concern', 'Going Concern Assessment', 'risk-controls', 'Assess liquidity, forecasts, covenants, mitigating actions, uncertainty, and disclosure needs.'),
 ('thai-corporate-income-tax', 'Thailand Corporate Income Tax', 'tax-thailand', 'Prepare a governed Thai corporate income tax bridge, adjustments, evidence, and filing review.'),
 ('thai-vat', 'Thailand VAT', 'tax-thailand', 'Reconcile output and input VAT, assess documentation, exceptions, and filing readiness.'),
 ('thai-withholding-tax', 'Thailand Withholding Tax', 'tax-thailand', 'Determine withholding categories, rates, certificates, remittance, and reconciliation.'),
 ('thai-transfer-pricing', 'Thailand Transfer Pricing', 'tax-thailand', 'Support related-party pricing, documentation, benchmarking, disclosure, and adjustment review.'),
 ('thai-tax-provision', 'Thailand Tax Provision', 'tax-thailand', 'Prepare current and deferred Thai tax provision with uncertain positions and effective-tax-rate analysis.'),
 ('thai-e-tax-invoice', 'Thailand e-Tax Invoice and e-Receipt', 'tax-thailand', 'Assess e-tax document process, master data, signatures, transmission, archive, and reconciliation.'),
 ('thai-e-withholding-tax', 'Thailand e-Withholding Tax', 'tax-thailand', 'Reconcile e-withholding records to payments, certificates, ledger, and tax submissions.'),
 ('thai-customs-duty', 'Thailand Customs and Import Duty', 'tax-thailand', 'Review tariff classification, customs value, origin, exemptions, brokers, and reconciliations.'),
 ('thai-boi-incentives', 'Thailand BOI Incentives', 'tax-thailand', 'Track promoted activities, conditions, privileges, segregated results, and compliance evidence.'),
 ('thai-tax-calendar', 'Thailand Tax Compliance Calendar', 'tax-thailand', 'Maintain tax obligations, data cutoffs, owners, reviews, submissions, payments, and evidence.'),
 ('saas-metrics', 'SaaS Metrics', 'industry-data', 'Calculate ARR, MRR, churn, retention, expansion, CAC, LTV, payback, and Rule of 40.'),
 ('telecom-metrics', 'Telecom Metrics', 'industry-data', 'Analyze subscribers, ARPU, churn, traffic, network costs, capex intensity, and service margin.'),
 ('idc-cloud-unit-economics', 'IDC and Cloud Unit Economics', 'industry-data', 'Measure rack, power, bandwidth, VM, storage, occupancy, utilization, and contribution margin economics.'),
 ('project-profitability', 'Project and Contract Profitability', 'industry-data', 'Track contract revenue, cost-to-complete, margin, change orders, billing, and cash exposure.'),
 ('data-quality-finance', 'Finance Data Quality', 'industry-data', 'Profile completeness, validity, consistency, uniqueness, timeliness, lineage, and reconciliation.'),
 ('finance-metric-layer', 'Finance Metric Layer', 'industry-data', 'Define governed finance metrics with formulas, grain, dimensions, owners, and tests.'),
 ('erp-ledger-ingestion', 'ERP and Ledger Ingestion', 'industry-data', 'Ingest finance data with schema mapping, control totals, lineage, and incremental load controls.'),
 ('financial-document-extraction', 'Financial Document Extraction', 'industry-data', 'Extract structured fields from invoices, statements, contracts, and reports with confidence and review.'),
 ('finance-anomaly-detection', 'Finance Anomaly Detection', 'industry-data', 'Detect explainable transaction and KPI anomalies with baselines, thresholds, and case workflow.')]

CATEGORY_TEMPLATES = {
    "fpna": {
        "name": "FP&A",
        "tags": ("planning", "forecasting", "performance"),
        "inputs": (
            "governed actuals with entity, period, currency, and account mapping",
            "approved planning assumptions and operational drivers",
            "owners, materiality thresholds, and decision horizon",
        ),
        "procedure": (
            "Validate scope, period, currency, units, source lineage, and control totals.",
            "Separate historical facts, management assumptions, and model-derived estimates.",
            "Build the driver bridge and calculate outputs with reproducible formulas.",
            "Run base, downside, and upside sensitivity where the decision is material.",
            "Explain the largest movements, accountable owners, actions, and expected dates.",
        ),
        "outputs": (
            "machine-readable calculations and assumptions",
            "management summary with material drivers",
            "risk, opportunity, action, owner, and due-date table",
        ),
        "checks": (
            "totals reconcile to the approved source",
            "formulas, units, signs, periods, and scenario links are consistent",
            "material conclusions are traceable to data or explicit assumptions",
        ),
        "references": (
            "company-approved planning policy and management reporting definitions",
            "source ERP, billing, CRM, workforce, and operational systems",
        ),
    },
    "accounting": {
        "name": "Accounting and Reporting",
        "tags": ("accounting", "close", "ifrs"),
        "inputs": (
            "ledger, subledger, contracts, schedules, and supporting documents",
            "applicable reporting framework, policy, entity, and reporting period",
            "materiality, preparer, reviewer, and approval requirements",
        ),
        "procedure": (
            "Establish facts, transaction flow, entities, dates, currency, and source evidence.",
            "Identify applicable accounting guidance and company policy before calculation.",
            "Prepare calculations, entries, reconciliations, and disclosure impacts.",
            "Document alternatives, judgments, estimates, uncertainty, and conclusion.",
            "Obtain preparer and reviewer sign-off before posting or external reporting.",
        ),
        "outputs": (
            "accounting workpaper or memo",
            "proposed journal or reconciliation marked DRAFT",
            "financial statement and disclosure impact",
        ),
        "checks": (
            "debits equal credits and schedules tie to the ledger",
            "period, entity, currency, classification, and sign are correct",
            "citations and judgments are documented and reviewer-ready",
        ),
        "references": (
            "IFRS Foundation issued standards: https://www.ifrs.org/issued-standards/list-of-standards/",
            "company accounting policies, chart of accounts, and close calendar",
        ),
    },
    "treasury": {
        "name": "Treasury",
        "tags": ("treasury", "cash", "liquidity"),
        "inputs": (
            "bank, ledger, debt, forecast, covenant, and counterparty data",
            "availability restrictions, value dates, currencies, and legal entities",
            "treasury policy, limits, signatories, and approval matrix",
        ),
        "procedure": (
            "Reconcile source balances and establish available versus restricted liquidity.",
            "Model timing, currencies, facilities, covenants, and downside shocks.",
            "Identify concentration, funding, market, counterparty, and operational risks.",
            "Recommend actions with amount, timing, owner, approval, and fallback.",
            "Record evidence and maintain maker-checker separation for execution.",
        ),
        "outputs": (
            "liquidity or exposure schedule",
            "threshold and covenant alerts",
            "action plan requiring authorized release where consequential",
        ),
        "checks": (
            "bank, debt, and ledger control totals reconcile",
            "value date, currency, legal entity, facility, and sign are correct",
            "no payment, transfer, hedge, or borrowing is executed automatically",
        ),
        "references": (
            "approved treasury policy, bank mandates, and facility agreements",
            "authoritative bank confirmations and sourced market data",
        ),
    },
    "corporate-finance": {
        "name": "Corporate Finance and M&A",
        "tags": ("valuation", "investment", "m&a"),
        "inputs": (
            "historical financials, forecast, capital structure, and transaction assumptions",
            "market data with source and retrieval date",
            "strategic objectives, hurdle rates, constraints, and approval authority",
        ),
        "procedure": (
            "Validate historicals, forecast logic, net debt, shares, and transaction perimeter.",
            "Build transparent formulas for cash flow, valuation, financing, and returns.",
            "Triangulate results using appropriate methods and sourced benchmarks.",
            "Run sensitivities, downside cases, break-even points, and key risk analysis.",
            "Present recommendation, valuation range, conditions, and unresolved diligence.",
        ),
        "outputs": (
            "auditable model or review workpaper",
            "valuation and returns range",
            "investment recommendation with conditions and approval gates",
        ),
        "checks": (
            "enterprise-to-equity bridge and cash/debt signs are correct",
            "market data, transaction assumptions, and dates are sourced",
            "model integrity and sensitivity center cases are verified",
        ),
        "references": (
            "board-approved investment and capital allocation policy",
            "issuer filings and authoritative market-data sources",
        ),
    },
    "risk-controls": {
        "name": "Risk, Audit, and Controls",
        "tags": ("controls", "audit", "risk"),
        "inputs": (
            "process narrative, systems, roles, transactions, risks, and prior findings",
            "control population, evidence, frequency, owner, and reviewer",
            "materiality, risk appetite, policy, and regulatory obligations",
        ),
        "procedure": (
            "Define process objective, scope, systems, handoffs, and failure modes.",
            "Map inherent risks to preventive, detective, and compensating controls.",
            "Test design and operating evidence using a complete population and documented sample.",
            "Classify exceptions by impact, root cause, ownership, and remediation date.",
            "Retest remediation and preserve an immutable evidence trail.",
        ),
        "outputs": (
            "risk-control matrix or test workpaper",
            "exception and remediation register",
            "control conclusion with evidence references",
        ),
        "checks": (
            "population completeness and evidence authenticity are established",
            "preparer, operator, approver, and reviewer roles are separated",
            "exceptions are not silently overwritten or closed without evidence",
        ),
        "references": (
            "COSO Internal Control framework: https://www.coso.org/internal-control",
            "company policies, authority matrix, audit methodology, and risk appetite",
        ),
    },
    "tax-thailand": {
        "name": "Thailand Tax and Regulation",
        "tags": ("thailand", "tax", "compliance"),
        "inputs": (
            "transaction, invoice, payment, entity, counterparty, and tax master data",
            "tax period, filing status, certificates, contracts, and reconciliations",
            "current official rule, effective date, interpretation, and reviewer",
        ),
        "procedure": (
            "Determine transaction facts, parties, dates, source jurisdiction, and documentation.",
            "Verify the current official Thai rule and effective date from an authoritative source.",
            "Calculate tax treatment and reconcile tax records to ledger and payments.",
            "List exceptions, missing evidence, uncertain positions, penalties, and corrective action.",
            "Prepare a review package; an authorized human submits and pays.",
        ),
        "outputs": (
            "tax workpaper and reconciliation",
            "draft filing support and exception register",
            "evidence index and reviewer sign-off request",
        ),
        "checks": (
            "official current rules are verified at execution time",
            "tax base, rate, period, counterparty, certificate, and ledger tie-out are checked",
            "the agent does not submit a return or release a tax payment",
        ),
        "references": (
            "Thai Revenue Department official site: https://www.rd.go.th/english/",
            "applicable official notifications, forms, rulings, and company tax policy",
        ),
    },
    "industry-data": {
        "name": "Industry and Finance Data",
        "tags": ("data", "analytics", "metrics"),
        "inputs": (
            "source schemas, data dictionary, grain, keys, lineage, and refresh schedule",
            "finance metric definitions, owner, dimensions, and reconciliation target",
            "quality thresholds, access classification, and exception workflow",
        ),
        "procedure": (
            "Profile schema, completeness, uniqueness, validity, consistency, and timeliness.",
            "Map source fields to governed finance definitions and transformation rules.",
            "Reconcile row counts, control totals, balances, and period coverage.",
            "Calculate metrics or anomalies with reproducible code and explainable thresholds.",
            "Publish lineage, tests, exceptions, confidence, and reviewer status.",
        ),
        "outputs": (
            "validated dataset or metric table",
            "quality and reconciliation report",
            "lineage, confidence, exceptions, and remediation owners",
        ),
        "checks": (
            "source-to-output row counts and control totals reconcile",
            "metric grain, formula, unit, sign, currency, and time zone are explicit",
            "sensitive data is minimized, redacted, and access-controlled",
        ),
        "references": (
            "approved finance data dictionary and metric layer",
            "source-system documentation, lineage records, and data quality policy",
        ),
    },
}


def _tokens(*values: str) -> tuple[str, ...]:
    output: list[str] = []
    for value in values:
        for token in re.findall(r"[a-z0-9]+", value.lower()):
            if token not in output:
                output.append(token)
    return tuple(output)


SKILLS: tuple[FinanceSkill, ...] = tuple(
    FinanceSkill(
        slug=slug,
        title=title,
        category=category,
        description=description,
        tags=tuple(
            dict.fromkeys(
                (
                    "finance",
                    category,
                    *CATEGORY_TEMPLATES[category]["tags"],
                    *_tokens(slug, title),
                )
            )
        ),
    )
    for slug, title, category, description in _SKILL_ROWS
)

if len(SKILLS) != 99 or len({skill.slug for skill in SKILLS}) != 99:
    raise RuntimeError("CFO skill catalog must contain exactly 99 unique skills")


SKILL_BY_SLUG = {skill.slug: skill for skill in SKILLS}


def _row(skill: FinanceSkill) -> dict[str, object]:
    template = CATEGORY_TEMPLATES[skill.category]
    return {
        **asdict(skill),
        "domain": template["name"],
    }


def search_skills(query: str, *, limit: int = 10) -> list[dict[str, object]]:
    if limit < 1:
        return []
    terms = set(_tokens(query))
    if not terms:
        return [_row(skill) for skill in SKILLS[:limit]]
    ranked: list[tuple[int, str, FinanceSkill]] = []
    for skill in SKILLS:
        slug_tokens = set(_tokens(skill.slug))
        title_tokens = set(_tokens(skill.title))
        desc_tokens = set(_tokens(skill.description))
        tag_tokens = set(skill.tags)
        score = (
            len(terms & slug_tokens) * 8
            + len(terms & title_tokens) * 6
            + len(terms & tag_tokens) * 4
            + len(terms & desc_tokens) * 2
        )
        phrase = query.strip().lower()
        if phrase and (
            phrase in skill.slug.lower()
            or phrase in skill.title.lower()
            or phrase in skill.description.lower()
        ):
            score += 12
        if score:
            ranked.append((score, skill.slug, skill))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    output = []
    for score, _, skill in ranked[:limit]:
        item = _row(skill)
        item["score"] = score
        output.append(item)
    return output


def related_skills(skill: FinanceSkill, *, limit: int = 4) -> list[str]:
    peers = [
        candidate.slug
        for candidate in SKILLS
        if candidate.category == skill.category and candidate.slug != skill.slug
    ]
    return peers[:limit]


def _markdown_list(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def render_skill_md(skill: FinanceSkill) -> str:
    template = CATEGORY_TEMPLATES[skill.category]
    tags = ", ".join(json.dumps(tag, ensure_ascii=False) for tag in skill.tags)
    related = ", ".join(
        json.dumps(slug, ensure_ascii=False) for slug in related_skills(skill)
    )
    return f"""---
name: {skill.slug}
description: {skill.description}
version: 1.0.0
author: CFOAgent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [{tags}]
    related_skills: [{related}]
---

# {skill.title}

{skill.description}

## When to use

Use this skill for governed {template['name']} work when the user requests
analysis, a workpaper, a forecast, a model review, a reconciliation, or a
decision pack related to **{skill.title}**.

## Required inputs

{_markdown_list(template['inputs'])}

If a required input is missing, label it explicitly. Do not invent balances,
rates, contractual terms, approvals, evidence, or current regulatory facts.

## Procedure

{chr(10).join(f'{index}. {step}' for index, step in enumerate(template['procedure'], start=1))}

## Output contract

{_markdown_list(template['outputs'])}

Every output must separate **facts**, **calculations**, **assumptions**,
**estimates**, and **management judgment**. Include source, as-of date, entity,
currency, units, materiality, preparer status, and reviewer status.

## Verification

{_markdown_list(template['checks'])}

Stop and report the exception when a control total, reconciliation, formula,
period, entity, currency, or source cannot be verified.

## Control boundary

This skill is read-only by default. It may draft, analyze, reconcile, simulate,
and prepare decision material. It must not release payments, post journals,
submit tax, release payroll, change bank details, execute trades, sign
contracts, or publish final external statements without authorized human approval.

## Reference classes

{_markdown_list(template['references'])}

For accounting standards, tax, law, market data, and filing requirements,
verify the current authoritative source at execution time and record the date.
"""


def catalog_json() -> str:
    return json.dumps([_row(skill) for skill in SKILLS], ensure_ascii=False, indent=2) + "\n"


def generate_skill_tree(destination: str | Path) -> list[Path]:
    root = Path(destination)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for skill in SKILLS:
        path = root / skill.slug / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_skill_md(skill), encoding="utf-8")
        written.append(path)
    (root / "catalog.json").write_text(catalog_json(), encoding="utf-8")
    return written
