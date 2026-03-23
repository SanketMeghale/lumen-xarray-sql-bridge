import asyncio
import os

import numpy as np
import xarray as xr

from lumen.ai.agents.sql import SQLAgent
from lumen.ai.config import SOURCE_TABLE_SEPARATOR
from lumen.ai.llm import OpenAI
from lumen.ai.schemas import get_metaset

from lumen_xarray_sql_prototype import XarraySQLSource


async def main():
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("Set OPENAI_API_KEY before running this demo.")

    model = os.environ.get("LUMEN_LIVE_SQL_MODEL", "gpt-4o-mini")
    dataset = xr.Dataset(
        data_vars={
            "temperature": (
                ("time", "lat", "lon"),
                np.array([
                    [[1.0, 2.0], [3.0, 4.0]],
                    [[5.0, 6.0], [7.0, 8.0]],
                    [[9.0, 10.0], [11.0, 12.0]],
                ]),
            ),
        },
        coords={
            "time": np.array(["2024-01-01", "2024-02-01", "2024-03-01"], dtype="datetime64[ns]"),
            "lat": np.array([10.0, 20.0]),
            "lon": np.array([70.0, 80.0]),
        },
    )
    source = XarraySQLSource(name="weather", dataset=dataset)
    slug = f"weather{SOURCE_TABLE_SEPARATOR}temperature"
    metaset = await get_metaset([source], [slug])
    llm = OpenAI(model_kwargs={"default": {"model": model}, "sql": {"model": model}})
    agent = SQLAgent(llm=llm, exploration_enabled=False)

    outputs, out_context = await agent.respond(
        [{"role": "user", "content": "Calculate the average temperature by latitude and sort by latitude."}],
        {
            "source": source,
            "sources": [source],
            "metaset": metaset,
            "visible_slugs": {slug},
        },
    )

    print("Generated SQL:")
    print(outputs[0].spec)
    print()
    print("Pipeline result:")
    print(out_context["pipeline"].data)


asyncio.run(main())
