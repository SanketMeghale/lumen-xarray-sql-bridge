# PR Notes

This file is written as a maintainer-facing PR summary for the prototype.

## Summary

This prototype adds an `XarraySQLSource`-style adapter around xarray-backed datasets using `BaseSQLSource` and `xarray-sql`, so Lumen AI can write transforms through the existing SQL path instead of introducing a separate xarray-specific AI transform flow.

## Why this direction

The maintainer feedback was to move the design toward `BaseSQLSource` and [`xarray-sql`](https://github.com/alxmrs/xarray-sql) so AI can write transforms.

That is the design this prototype follows:

- xarray-backed data is exposed through a SQL-capable source contract
- the execution layer is `xarray-sql`
- derived SQL tables remain possible through `create_sql_expr_source(...)`
- the AI path stays inside Lumen's existing SQL tooling

## Key design choice

Each `Dataset.data_var` is registered as its own logical SQL table.

That is deliberate:

- xarray datasets may contain variables with different dimensions
- whole-dataset flattening is not a stable general table abstraction
- per-variable registration matches Lumen's table model more closely

## Prototype scope notes

These points are intentionally documented here rather than in code docstrings:

- accepts an in-memory `xarray.Dataset`
- exposes `Dataset.data_vars` as logical tables
- uses `xarray-sql` so AI can write SQL transforms against those tables
- returns `pandas.DataFrame` objects for downstream compatibility

Those are PR-scoping notes and prototype constraints, not API documentation.

## What this prototype demonstrates

- xarray-backed data can satisfy the `BaseSQLSource` contract
- the existing SQL-oriented AI flow is the right integration point
- mixed-dimensional datasets can still be queried through a per-variable registration strategy

## What remains for hardening

- broader live-model validation for prompt quality
- backend dialect edge-case coverage
- clearer policy for auxiliary coordinates and non-SQL-native scientific operations
