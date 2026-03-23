import numpy as np
import xarray as xr

from lumen_xarray_sql_prototype import XarraySQLSource


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

print("Tables:", source.get_tables())
print()
print("Top 5 rows")
print(source.execute('SELECT * FROM "temperature" LIMIT 5'))
print()
print("Average temperature by latitude")
print(
    source.execute(
        """
        SELECT "lat", AVG("temperature") AS avg_temperature
        FROM "temperature"
        GROUP BY "lat"
        ORDER BY "lat"
        """
    )
)
