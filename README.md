# Lumen Xarray SQL Prototype

Prototype repository for exposing `xarray.Dataset` objects through Lumen's SQL AI path.

## Why this exists

Lumen's AI transform flow is strongest on `BaseSQLSource` implementations because the SQL agent already knows how to:

- inspect schemas
- generate SQL
- validate queries
- create derived SQL-backed tables

Scientific datasets are often stored as `xarray.Dataset`, not in a database. This prototype bridges that gap by implementing an `XarraySQLSource` on top of `xarray-sql`, so Lumen can reuse the existing SQL agent instead of introducing a second AI transform stack.

## Prototype highlights

- Subclasses `BaseSQLSource`
- Uses `xarray-sql` / DataFusion as the execution backend
- Registers each `data_var` as an independent SQL table
- Preserves mixed-dimension xarray variables by avoiding whole-dataset flattening
- Works for SQL-shaped prompts such as previews, filters, grouping, sorting, and derived queries
- Includes a live SQL-agent demo script once `OPENAI_API_KEY` is configured

## Limitations

- This is a prototype, not a production-ready Lumen extension
- It depends on Lumen internals, so upstream changes may require adjustment
- It is strongest for SQL-shaped prompts, not arbitrary xarray-native analysis
- Auxiliary or non-dimension coordinates are not modeled as fully general SQL columns

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[test]
```

## Quick demo

```bash
python scripts/demo.py
```

Optional live AI demo:

```bash
set OPENAI_API_KEY=...
python scripts/live_sql_agent_demo.py
```

## Repository layout

- `src/lumen_xarray_sql_prototype/source.py`: prototype `XarraySQLSource`
- `scripts/demo.py`: local query demo without an LLM
- `scripts/live_sql_agent_demo.py`: live SQL-agent demo
- `tests/test_source.py`: focused source behavior tests

## Design note

The key design choice is one SQL table per xarray variable. That keeps mixed-dimension datasets usable and aligns with Lumen's logical table model while still letting the SQL agent reason over familiar table schemas.
