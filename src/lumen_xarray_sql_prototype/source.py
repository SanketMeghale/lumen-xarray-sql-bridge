from __future__ import annotations

import hashlib

from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import pandas as pd
import param

from lumen.sources.base import BaseSQLSource, cached, cached_schema
from lumen.sources.xarray import XarraySource
from lumen.transforms.sql import SQLFilter

try:
    import xarray as xr
except ImportError:
    xr = None  # type: ignore

try:
    import xarray_sql
except ImportError:
    xarray_sql = None  # type: ignore

if TYPE_CHECKING:
    import xarray as xr
    import xarray_sql


class XarraySQLSource(BaseSQLSource):
    """
    SQL-backed xarray source powered by `xarray-sql`.

    Each data variable is registered as an independent SQL table so datasets
    with heterogeneous dimensionality remain queryable through Lumen's SQL AI
    path.
    """

    dataset = param.Parameter(doc="""
        An xarray.Dataset providing the data variables exposed by the source.
    """)

    uri = param.String(default=None, doc="""
        Optional path or URI to an xarray-readable dataset. Used when no
        in-memory dataset is supplied.
    """)

    dataset_format = param.Selector(default="auto", objects=["auto", "netcdf", "zarr"], doc="""
        Dataset storage format. If set to auto, the format is inferred from the
        URI, local store markers, or load kwargs.
    """)

    load_kwargs = param.Dict(default={}, doc="""
        Additional keyword arguments forwarded to xarray.open_dataset or
        xarray.open_zarr.
    """)

    chunks = param.Dict(default={}, doc="""
        Optional chunk sizes passed to xarray-sql registration.
    """)

    filterable_coords = param.List(default=None, allow_None=True, doc="""
        Optional list of coordinate names that should be exposed in rich
        metadata for base xarray variables.
    """)

    sql_expr = param.String(default="SELECT * FROM {table}", doc="""
        The SQL expression used to query table references.
    """)

    tables = param.Parameter(default=None, doc="""
        Optional mapping of logical table names to SQL expressions or a list
        of base xarray variable names to expose.
    """)

    source_type: ClassVar[str] = "xarray_sql"
    dialect = "duckdb"

    def __init__(self, **params):
        super().__init__(**params)
        self._loaded_dataset = None
        self._context = None
        self._table_sources: dict[str, xr.Dataset] = {}
        self._validate_dataset()

    def _validate_dataset(self) -> None:
        if xr is None:
            raise ImportError("XarraySQLSource requires the 'xarray' package.")
        if xarray_sql is None:
            raise ImportError("XarraySQLSource requires the 'xarray-sql' package.")
        if self.dataset is None and not self.uri:
            raise ValueError("XarraySQLSource requires either a dataset or a uri.")
        if self.dataset is not None and not isinstance(self.dataset, xr.Dataset):
            raise TypeError("XarraySQLSource 'dataset' must be an xarray.Dataset.")
        if self.tables is not None and not isinstance(self.tables, (list, dict)):
            raise TypeError("XarraySQLSource 'tables' must be a list, dict, or None.")

    def _is_windows_path(self, uri: str) -> bool:
        parsed = urlparse(uri)
        return len(parsed.scheme) == 1 and uri[1:2] == ":"

    def _is_remote_uri(self, uri: str) -> bool:
        parsed = urlparse(uri)
        return bool(parsed.scheme and parsed.scheme not in ("file",) and not self._is_windows_path(uri))

    def _uri_to_path(self, uri: str) -> Path:
        parsed = urlparse(uri)
        if parsed.scheme == "file":
            location = f"//{parsed.netloc}{parsed.path}" if parsed.netloc else parsed.path
            local_path = url2pathname(unquote(location))
            if local_path.startswith("/") and len(local_path) > 2 and local_path[2] == ":":
                local_path = local_path[1:]
            return Path(local_path)
        return Path(uri)

    def _resolve_uri(self) -> str:
        assert self.uri is not None
        if self._is_remote_uri(self.uri):
            return self.uri
        path = self._uri_to_path(self.uri)
        if not path.is_absolute():
            path = self.root / path
        return str(path)

    def _is_local_zarr_store(self, uri: str) -> bool:
        path = Path(uri)
        if not path.exists() or not path.is_dir():
            return False
        return (path / ".zgroup").exists() or (path / "zarr.json").exists()

    def _get_dataset_format(self, uri: str) -> str:
        if self.dataset_format != "auto":
            return self.dataset_format
        if self.load_kwargs.get("engine") == "zarr":
            return "zarr"
        parsed = urlparse(uri)
        if parsed.path.endswith(".zarr"):
            return "zarr"
        if not self._is_remote_uri(uri) and self._is_local_zarr_store(uri):
            return "zarr"
        return "netcdf"

    def _open_dataset(self) -> xr.Dataset:
        uri = self._resolve_uri()
        if self._get_dataset_format(uri) == "zarr":
            return xr.open_zarr(uri, **self.load_kwargs)
        return xr.open_dataset(uri, **self.load_kwargs)

    def _get_dataset(self) -> xr.Dataset:
        if self.dataset is not None:
            return self.dataset
        if self._loaded_dataset is None:
            self._loaded_dataset = self._open_dataset()
        return self._loaded_dataset

    def _get_source_hash(self):
        sha = hashlib.sha256()
        for key, value in self.param.values().items():
            if key in ("root",):
                continue
            sha.update(key.encode("utf-8"))
            if key == "uri" and isinstance(value, str) and not self._is_remote_uri(value):
                path = Path(self._resolve_uri())
                if path.exists():
                    sha.update(str(path.stat().st_mtime_ns).encode("utf-8"))
            else:
                sha.update(str(value).encode("utf-8"))
        return sha.hexdigest()

    def _base_table_mapping(self) -> dict[str, str]:
        dataset = self._get_dataset()
        base_tables = list(dataset.data_vars)
        if self.tables is None:
            return {table: table for table in base_tables}
        if isinstance(self.tables, list):
            return {table: table for table in self.tables}
        return dict(self.tables)

    def _resolve_registration_chunks(self, ds: xr.Dataset) -> dict[str, int]:
        if self.chunks:
            return dict(self.chunks)
        return {dim: int(size) for dim, size in ds.sizes.items()}

    def _dataset_for_table(self, table: str) -> xr.Dataset:
        if table in self._table_sources:
            return self._table_sources[table]
        dataset = self._get_dataset()
        if table not in dataset.data_vars:
            raise KeyError(f"Table {table!r} is not a base xarray variable.")
        table_ds = dataset[[table]]
        self._table_sources[table] = table_ds
        return table_ds

    def _is_exact_base_table_expr(self, table_name: str, sql_expr: str) -> bool:
        normalized = " ".join(sql_expr.strip().split())
        exact_exprs = {
            table_name,
            f"SELECT * FROM {table_name}",
            f'SELECT * FROM "{table_name}"',
        }
        return normalized in exact_exprs

    def _build_context(self) -> xarray_sql.XarrayContext:
        ctx = xarray_sql.XarrayContext()
        registered = set()
        for table_name in self._get_dataset().data_vars:
            ds = self._dataset_for_table(table_name)
            ctx.from_dataset(table_name, ds, chunks=self._resolve_registration_chunks(ds))
            registered.add(table_name)

        for table_name, sql_expr in self._base_table_mapping().items():
            if table_name in registered and self._is_exact_base_table_expr(table_name, sql_expr):
                continue
            if table_name in self._get_dataset().data_vars and self._is_exact_base_table_expr(table_name, sql_expr):
                continue
            view_df = ctx.sql(sql_expr)
            ctx.register_view(table_name, view_df)

        return ctx

    @property
    def context(self) -> xarray_sql.XarrayContext:
        if self._context is None:
            self._context = self._build_context()
        return self._context

    def normalize_table(self, table: str) -> str:
        return table.strip('"')

    def get_tables(self) -> list[str]:
        return [table for table in self._base_table_mapping() if not self._is_table_excluded(table)]

    def create_sql_expr_source(
        self, tables: dict[str, str], params: dict[str, list | dict] | None = None, **kwargs
    ):
        source_params = dict(self.param.values(), **kwargs)
        all_tables = self._base_table_mapping()
        all_tables.update(tables)
        source_params["tables"] = all_tables
        if params:
            all_params = dict(self.table_params)
            all_params.update(params)
            source_params["table_params"] = all_params
        source_params.pop("name", None)
        return type(self)(**source_params)

    @cached_schema
    def get_schema(
        self, table: str | None = None, limit: int | None = None, shuffle: bool = False
    ) -> dict[str, dict[str, Any]] | dict[str, Any]:
        return super().get_schema(table=table, limit=limit, shuffle=False)

    def execute(self, sql_query: str, params: list | dict | None = None, *args, **kwargs) -> pd.DataFrame:
        if args or kwargs:
            raise TypeError("XarraySQLSource.execute does not accept additional positional or keyword arguments.")
        if params is None or params == [] or params == {}:
            return self.context.sql(sql_query).to_pandas()
        if isinstance(params, dict):
            return self.context.sql(sql_query, param_values=params).to_pandas()
        raise ValueError("XarraySQLSource only supports named SQL parameters.")

    def close(self) -> None:
        if self._loaded_dataset is not None and hasattr(self._loaded_dataset, "close"):
            self._loaded_dataset.close()
        self._loaded_dataset = None
        self._context = None
        self._table_sources = {}

    def clear_cache(self, *events: param.parameterized.Event):
        self.close()
        super().clear_cache(*events)

    def _get_table_metadata(self, tables: list[str]) -> dict[str, Any]:
        xarray_source = XarraySource(
            dataset=self._get_dataset(),
            filterable_coords=self.filterable_coords,
            root=self.root,
        )
        metadata: dict[str, Any] = {}
        for table_name in tables:
            if table_name in self._get_dataset().data_vars:
                metadata[table_name] = xarray_source.get_metadata(table_name)
                continue

            schema_result = self.execute(f'SELECT * FROM "{table_name}" LIMIT 0')
            count = self.execute(f'SELECT COUNT(*) AS count FROM "{table_name}"')
            metadata[table_name] = {
                "description": "",
                "columns": {
                    col: {"data_type": str(dtype), "description": ""}
                    for col, dtype in zip(schema_result.columns, schema_result.dtypes, strict=False)
                },
                "rows": int(count["count"].iloc[0]),
                "updated_at": None,
                "created_at": None,
            }
        return metadata

    @cached
    def get(self, table: str, **query) -> pd.DataFrame:
        query.pop("__dask", None)
        sql_expr = self.get_sql_expr(table)
        sql_transforms = query.pop("sql_transforms", [])
        conditions = list(query.items())
        if conditions:
            sql_expr = SQLFilter(conditions=conditions, read=self.dialect, write=self.dialect).apply(sql_expr)
        for sql_transform in sql_transforms:
            sql_expr = sql_transform.apply(sql_expr)
        params = self.table_params.get(table)
        return self.execute(sql_expr, params=params)
