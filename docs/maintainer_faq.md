# Maintainer FAQ

## Why build this on `BaseSQLSource`?

Because that is the contract Lumen's SQL AI flow already understands.

If the goal is "AI should write the transforms", the source needs to expose the behaviors that `SQLAgent` expects:

- `execute(...)`
- schema discovery
- SQL-backed derived tables

This prototype follows that path directly rather than trying to extend xarray support through a separate AI abstraction.

## Why use `xarray-sql`?

Because the prototype needs a real execution layer, not just a fake SQL facade.

`xarray-sql` provides a concrete bridge from `xarray.Dataset` to SQL execution. That lets the prototype answer the important architectural question:

"Can xarray-backed data participate in Lumen's existing SQL AI flow?"

This repository is meant to answer that with working code.

## How does AI write transforms here?

It does not rely on custom xarray prompt logic.

Instead:

1. `XarraySQLSource` exposes xarray-backed variables as SQL tables.
2. Lumen sees a `BaseSQLSource`.
3. The existing `SQLAgent` can inspect schema and generate SQL.
4. The source executes that SQL through `xarray-sql`.

That is the main value of the prototype.

## Why register one SQL table per xarray variable?

Because real xarray datasets often contain variables with different dimensionality.

If the prototype tried to flatten the entire dataset into one uniform table, it would either:

- break on incompatible shapes
- or lose the structure that makes the data meaningful

Registering one `Dataset.data_var` per logical SQL table is the cleanest way to preserve mixed-dimensional datasets while still fitting Lumen's table-oriented AI model.

## Why not keep this only as an `XarraySource` feature?

Because `XarraySource` alone does not satisfy the SQL source contract the AI path expects.

`XarraySource` is useful for direct xarray-style access, but the maintainer request is specifically about enabling AI-written transforms. That pushes the design toward `BaseSQLSource`.

## What exactly is the prototype proving?

It proves that:

- xarray-backed data can be exposed as a SQL-capable Lumen source
- Lumen AI can reuse the existing SQL path instead of a second transform path
- mixed-dimension variables can still be handled sensibly

It does not prove full production readiness.

## What edge cases are already known?

- some backend SQL syntax may differ from DuckDB expectations
- not all natural-language prompts will map cleanly to SQL
- auxiliary or non-dimension coordinates are not yet represented as general SQL columns
- some scientific operations are more natural in xarray than in SQL

Those are hardening questions, not feasibility blockers.

## Why are prototype-scope notes kept out of the source docstring?

Because source docstrings should describe behavior and API expectations.

Statements like:

- "this first draft is intentionally conservative"
- "accepts an in-memory dataset"
- "returns pandas DataFrames for downstream compatibility"

are review and PR-scoping notes, not API documentation. They belong in a PR description or prototype notes, which is why this repository keeps them here and in [PR_NOTES.md](../PR_NOTES.md).
