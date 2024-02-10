from typing import Any, Callable, Dict

import pandas as pd
from pandera import check_output

from ..schemas.candlestick_data_schema import candlestick_data_schema


def _convert_to_date(x: pd.Series) -> pd.Series:
    return pd.to_datetime(x)


def _replace_value(x: pd.Series) -> pd.Series:
    return x.replace(-1, 1)


@check_output(candlestick_data_schema)
def concat_partitions(
    partitioned_input: Dict[str, Callable[[], Any]]
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
