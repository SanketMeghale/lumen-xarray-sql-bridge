# Evaluation Matrix

| Question | Prototype answer | Evidence |
| --- | --- | --- |
| Can xarray-backed data look like a SQL-capable Lumen source? | Yes | `XarraySQLSource` implements the `BaseSQLSource` shape |
| Can AI write transforms against it? | Yes, for SQL-shaped prompts | Existing SQL-agent-oriented design and live demo path |
| Does it work for mixed-dimensional datasets? | Yes | One logical SQL table per `data_var` |
| Is this just a mock? | No | Uses `xarray-sql` as a real execution backend |
| Is the scope honest? | Yes | Known constraints are documented explicitly |
| Is there a path to upstream hardening? | Yes | Dialect, prompt, and metadata follow-up items are identified |
