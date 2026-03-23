# Demo Script

## Goal

Show in under two minutes that xarray-backed scientific data can participate in Lumen's existing SQL AI workflow.

## Setup

Run:

```bash
python scripts/demo.py
```

Optional live model demo:

```bash
set OPENAI_API_KEY=...
python scripts/live_sql_agent_demo.py
```

## Narrative

1. Start with the problem.

   "Lumen AI already works well with SQL-capable sources, but scientific datasets often live in xarray."

2. State the prototype insight.

   "Instead of inventing a separate AI transform stack, this prototype adapts xarray into the `BaseSQLSource` contract using `xarray-sql`."

3. Show the base proof.

   "The xarray variable is visible as a SQL table, and a simple row preview works immediately."

4. Show the value.

   "Now the same dataset supports SQL-style aggregation like average temperature by latitude."

5. State the architectural payoff.

   "That means Lumen's existing SQL agent can write transforms against scientific array data."

## What to emphasize

- The novelty is architectural reuse, not just query execution.
- The hard part solved is mixed-dimensional datasets through one-table-per-variable registration.
- The remaining work is hardening, not feasibility.
