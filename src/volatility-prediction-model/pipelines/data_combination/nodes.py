import typing as t

import numpy as np
import pandas as pd
from pandera import Column, DataFrameSchema, check_output

schema = DataFrameSchema(
    {
        "open_time": Column(np.dtype("datetime64[ns]"), required=False),
        "open": Column(float, required=True),
        "high": Column(float, required=True),
        "low": Column(float, required=True),
        "close": Column(float, required=True),
        "volume": Column(float, required=True),
        "close_time": Column(np.dtype("datetime64[ns]"), required=True),
        "qav": Column(float, required=False),
        "num_trades": Column(int, required=True),
        "taker_base_vol": Column(float, required=False),
        "taker_quote_vol": Column(float, required=False),
    }
)


def _convert_to_date(x: pd.Series) -> pd.Series:
    return pd.to_datetime(x)


def _replace_value(x: pd.Series) -> pd.Series:
    return x.replace(-1, 1)


@check_output(schema)
def concat_partitions(
    partitioned_input: t.Dict[str, t.Callable[[], t.Any]]
) -> pd.DataFrame:
    result = pd.DataFrame()
    for _partition_key, partition_load_func in sorted(partitioned_input.items()):
        partition_data = partition_load_func()
        partition_data["open_time"] = _convert_to_date(partition_data["open_time"])
        partition_data["close_time"] = _convert_to_date(partition_data["close_time"])
        result = pd.concat([result, partition_data], ignore_index=True, sort=True)

    return result


def clean_master_list(master_list: pd.DataFrame) -> pd.DataFrame:
    master_list["close_time"] = _convert_to_date(master_list["close_time"])
    master_list["target"] = _replace_value(master_list["target"])
    return master_list
