# Xarray SQL Bridge for Lumen AI

Prototype repository for exposing `xarray.Dataset` objects through Lumen's existing SQL AI path.

[![Tests](https://github.com/SanketMeghale/lumen-xarray-sql-bridge/actions/workflows/tests.yml/badge.svg)](https://github.com/SanketMeghale/lumen-xarray-sql-bridge/actions/workflows/tests.yml)

![Architecture](assets/architecture.svg)

## One-line proposal

Adapt xarray-backed scientific data into Lumen's `BaseSQLSource` contract using [`xarray-sql`](https://github.com/alxmrs/xarray-sql), so the existing `SQLAgent` can write and execute transforms without introducing a second AI transform system.

## Why this repository exists

Lumen AI already has a strong path for SQL-capable sources:

- inspect schema
- generate SQL
- validate SQL
- create derived SQL-backed tables

Scientific datasets often live in `xarray.Dataset`, which is not directly shaped like a SQL source. The point of this prototype is to prove that xarray data can be lifted into the same AI workflow by implementing a thin `BaseSQLSource` adapter instead of building separate xarray-specific agent logic.

## Maintainer FAQ

| Question | Short answer |
| --- | --- |
| Why `BaseSQLSource`? | Because Lumen's existing AI transform flow already depends on that contract. |
| Why `xarray-sql`? | Because it gives the prototype a real SQL execution layer over xarray-backed data. |
| How does AI write transforms? | Through the existing `SQLAgent` path once the source exposes SQL tables, schema, and `execute(...)`. |
| Why one table per `data_var`? | Mixed-dimension xarray datasets break down if forced into one uniform table shape. |
| Why not keep this in `XarraySource` only? | `XarraySource` is useful for xarray-native access, but it does not satisfy the SQL AI contract on its own. |
| What is the prototype proving? | That xarray-backed data can participate in Lumen's SQL AI path with minimal AI-specific changes. |
| What does it not prove? | It does not prove that every natural-language prompt or every backend-specific SQL feature will work. |

More detail: [docs/maintainer_faq.md](docs/maintainer_faq.md)

Proposal package:

- [docs/proposal_brief.md](docs/proposal_brief.md)
- [docs/demo_script.md](docs/demo_script.md)
- [docs/evaluation_matrix.md](docs/evaluation_matrix.md)

## Design in one screen

1. Wrap an `xarray.Dataset` in `XarraySQLSource`.
2. Register each base xarray variable as its own SQL table through `xarray-sql`.
3. Reuse Lumen's `BaseSQLSource` API for schema, execution, and derived SQL tables.
4. Let Lumen's existing `SQLAgent` generate transforms against those tables.

This is the critical design choice:

- one SQL table per xarray variable

That keeps mixed-dimensional datasets queryable and matches Lumen's logical table model. It also avoids flattening unrelated variables into a single lossy table representation.

## Why this architecture is the right direction

- Reuses existing Lumen AI infrastructure instead of adding another agent path
- Makes the prototype legible to maintainers because it follows established source abstractions
- Preserves a clear separation of concerns
  - xarray remains the data model
  - `xarray-sql` handles execution
  - Lumen AI stays responsible for prompt-to-SQL behavior
- Reduces the amount of AI-specific code needed for scientific data workflows

## What works today

- `SELECT * ... LIMIT 5` style previews
- filtering on dimension coordinates such as `time`, `lat`, and `lon`
- grouping, sorting, aggregates, and derived queries
- SQL-backed derived tables via `create_sql_expr_source(...)`
- AI compatibility with Lumen's `SQLAgent` path
- mixed-dimension variables by registering each `data_var` independently

## Known constraints

- not every natural-language prompt will work
- not every DataFusion or `xarray-sql` edge case matches DuckDB exactly
- not every xarray-native scientific transform belongs naturally in SQL
- auxiliary or non-dimension coordinates are not yet modeled as general SQL columns
- this repository is a prototype proving feasibility, not a production-ready upstream package

## Concrete example

Local demo output:

```text
Tables: ['temperature']

Top 5 rows
        time   lat   lon  temperature
0 2024-01-01  10.0  70.0          1.0
1 2024-01-01  10.0  80.0          2.0
2 2024-01-01  20.0  70.0          3.0
3 2024-01-01  20.0  80.0          4.0
4 2024-02-01  10.0  70.0          5.0

Average temperature by latitude
    lat  avg_temperature
0  10.0              5.5
1  20.0              7.5
```

Prompt shape this architecture targets:

```text
Calculate the average temperature by latitude and sort by latitude.
```

Representative SQL produced or supported by the prototype:

```sql
SELECT "lat", AVG("temperature") AS avg_temperature
FROM "temperature"
GROUP BY "lat"
ORDER BY "lat"
```

## Validation

What is already verified in this repository:

- focused source tests pass
- the standalone demo runs locally
- the source behaves like a SQL-capable source for Lumen's AI path
- GitHub Actions runs the focused test suite

The proof tests live in [tests/test_source.py](tests/test_source.py).

## Repository layout

- `src/lumen_xarray_sql_prototype/source.py`: prototype `XarraySQLSource`
- `scripts/demo.py`: local non-LLM proof script
- `scripts/live_sql_agent_demo.py`: live SQL-agent demo once credentials are available
- `tests/test_source.py`: focused source and AI-path proof tests
- `docs/maintainer_faq.md`: review-oriented design answers
- `docs/proposal_brief.md`: compact proposal framing
- `docs/demo_script.md`: short standout demo narrative
- `docs/evaluation_matrix.md`: reviewer-facing evidence summary
- `PR_NOTES.md`: PR rationale and notes that should not live in docstrings

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[test]
```

## Run

Local demo:

```bash
python scripts/demo.py
```

Run tests:

```bash
pytest -q
```

Optional live AI demo:

```bash
set OPENAI_API_KEY=...
python scripts/live_sql_agent_demo.py
```

## If this moves toward upstream

The next hardening steps are straightforward:

- validate prompt quality with a live configured model
- expand coverage for backend dialect edge cases
- improve modeling of auxiliary coordinates
- decide how this should coexist with the existing `XarraySource` and `XarrayAgent`
