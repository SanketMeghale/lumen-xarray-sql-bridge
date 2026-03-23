import asyncio

import numpy as np
import pytest

xr = pytest.importorskip("xarray")
pytest.importorskip("xarray_sql")

from lumen.ai.agents.sql import SQLAgent
from lumen.ai.config import SOURCE_TABLE_SEPARATOR
from lumen.ai.schemas import get_metaset

from lumen_xarray_sql_prototype import XarraySQLSource


@pytest.fixture
def xr_dataset():
    return xr.Dataset(
        data_vars={
            "temperature": (
                ("time", "lat", "lon"),
                np.array([
                    [[1.0, 2.0], [3.0, 4.0]],
                    [[5.0, 6.0], [7.0, 8.0]],
                ]),
            ),
            "station_bias": (
                ("lat", "lon"),
                np.array([
                    [0.1, 0.2],
                    [0.3, 0.4],
                ]),
            ),
        },
        coords={
            "time": np.array(["2024-01-01", "2024-01-02"], dtype="datetime64[ns]"),
            "lat": np.array([10.0, 20.0]),
            "lon": np.array([70.0, 80.0]),
        },
    )


def test_get_tables_and_base_query(xr_dataset):
    source = XarraySQLSource(name="weather", dataset=xr_dataset)

    assert set(source.get_tables()) == {"temperature", "station_bias"}
    result = source.get("temperature")
    assert list(result.columns) == ["time", "lat", "lon", "temperature"]
    assert len(result) == 8


def test_mixed_dimension_variables_work(xr_dataset):
    source = XarraySQLSource(name="weather", dataset=xr_dataset)

    result = source.get("station_bias")

    assert list(result.columns) == ["lat", "lon", "station_bias"]
    assert len(result) == 4


def test_create_sql_expr_source_registers_derived_table(xr_dataset):
    source = XarraySQLSource(name="weather", dataset=xr_dataset)

    derived = source.create_sql_expr_source(
        {
            "hot_temperature": """
                SELECT "time", "lat", "lon", "temperature"
                FROM "temperature"
                WHERE "temperature" >= 6
            """
        }
    )

    result = derived.get("hot_temperature")

    assert len(result) == 3
    assert result["temperature"].min() >= 6


def test_sql_agent_applies_to_source(xr_dataset):
    source = XarraySQLSource(name="weather", dataset=xr_dataset)
    slug = f"weather{SOURCE_TABLE_SEPARATOR}temperature"

    applies = asyncio.run(SQLAgent.applies({"source": source, "sources": [source]}))
    metaset = asyncio.run(get_metaset([source], [slug]))

    assert applies is True
    assert slug in metaset.catalog
    assert metaset.catalog[slug].sql_expr is not None
