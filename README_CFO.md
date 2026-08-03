# CFOAgent

CFOAgent is a CFO-specialized agent and deterministic finance operating system
built on the Hermes Agent runtime. It combines a searchable finance skill
catalog, repeatable calculations, board reporting, 13-week cash forecasting,
read-only data access, audit evidence, and human approval controls.

## What is included

- **99 CFO-native finance skills** across FP&A, accounting and reporting,
  treasury, corporate finance and M&A, risk and controls, Thailand tax, and
  finance data analytics.
- **Official Hermes finance skills** for stock research, Excel and PowerPoint
  authoring, DCF, comparable-company analysis, three-statement, LBO, and merger
  modeling. Original author and license metadata are preserved.
- Deterministic financial summaries, budget variance analysis, scenario
  analysis, robust anomaly detection, journal validation, reconciliations, and
  13-week liquidity forecasting.
- Specialist routing to FP&A, Controller, Treasury, Corporate Finance, Internal
  Controls, Thailand Tax, or Finance Data leads.
- Read-only SQLite queries, append-only hash-chained audit records, redaction,
  and explicit approval gates for consequential actions.
- Optional FastAPI endpoints, while the core engine remains dependency-light.

## Safety and control boundary

CFOAgent is analytical and read-only by default. It may draft, analyze,
forecast, reconcile, classify, query, simulate, and prepare decision material.
It does not autonomously release payments, post journals, submit tax returns,
release payroll, change vendor bank details, execute trades, sign contracts, or
publish final external statements. Those actions require an authorized human
and the organization's normal control workflow.

## Quick start

```bash
python -m cfo_agent.cli --version
python -m cfo_agent.cli demo --output board-pack.md
python -m cfo_agent.cli cash13 examples/sample_cash_13_week.csv --output cash13.md
python -m cfo_agent.cli analyze examples/sample_financials.csv \
  --budget examples/sample_budget.csv \
  --cash examples/sample_cash_13_week.csv \
  --format markdown --output management-pack.md
python -m cfo_agent.cli skills "IFRS 15 revenue recognition" --json
python -m cfo_agent.cli route "build a covenant and liquidity forecast"
python -m cfo_agent.cli policy payment-release
```

Generate or refresh the CFO-native skills:

```bash
python scripts/generate_finance_skills.py
```

Run the deterministic test suite:

```bash
python -m compileall -q cfo_agent scripts
python -m unittest discover -s tests/cfo_agent -v
```

## CSV schemas

`sample_financials.csv`:

```text
period,revenue,cogs,opex,cash,receivables,payables,inventory,debt
```

`sample_budget.csv`:

```text
period,account,actual,budget
```

`sample_cash_13_week.csv`:

```text
week,opening_cash,inflows,outflows,minimum_cash
```

Only the first cash week must provide `opening_cash`; later weeks roll forward
from the preceding closing balance unless an explicit override is supplied.

## Skill domains

| Domain | CFO-native skills |
|---|---:|
| FP&A | 15 |
| Accounting and reporting | 22 |
| Treasury | 14 |
| Corporate finance and M&A | 14 |
| Risk, audit, and controls | 15 |
| Thailand tax and regulation | 10 |
| Industry and finance data | 9 |
| **Total** | **99** |

Use `python -m cfo_agent.cli skills --json` for the machine-readable catalog.

## Architecture

```text
Hermes Agent runtime
├── CFOAgent deterministic engine
│   ├── analytics, cash flow, accounting, policy, audit, SQLite
│   ├── board pack and specialist router
│   └── optional FastAPI service
├── skills/finance-cfo          # 99 CFO-native skills
├── skills/finance-official     # official Hermes finance skills
└── tests/cfo_agent             # deterministic regression tests
```

## License and attribution

The Hermes Agent runtime is imported under its MIT license. Official optional
finance skills retain their own Apache-2.0 metadata. CFOAgent-specific source
files and generated CFO-native skills are MIT licensed. See
`THIRD_PARTY_NOTICES.md`, `UPSTREAM_README.md`, and the repository license files.
