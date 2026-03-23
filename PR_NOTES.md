# PR Notes

This repository is structured to match the maintainer direction for the Lumen prototype.

## Architectural direction

The implementation is centered on `BaseSQLSource` and `xarray-sql` so that Lumen AI can write and execute SQL transforms through the existing SQL agent path instead of introducing a separate xarray-specific transform system.

The important point is not just exposing xarray data, but exposing it in a form that Lumen AI already understands:

- `execute(...)`
- schema discovery
- derived SQL-backed tables via `create_sql_expr_source(...)`

## Why each xarray variable becomes a SQL table

`xarray-sql` works naturally with table-like registrations, while real `xarray.Dataset` objects can contain variables with different dimensionality. Registering each `Dataset.data_var` independently keeps mixed-dimension datasets queryable and matches Lumen's logical table model.

## Prototype scope

The following points are intentionally kept here, not in source docstrings:

- accepts an in-memory `xarray.Dataset`
- exposes `Dataset.data_vars` as logical tables
- uses `xarray-sql` so AI can write SQL transforms against those tables
- returns `pandas.DataFrame` objects for downstream compatibility

Those are prototype and PR-scoping notes, not API documentation.
