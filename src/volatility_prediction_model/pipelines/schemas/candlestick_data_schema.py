"""Data schema for klines data"""
import numpy as np
from pandera import Column, DataFrameSchema

candlestick_data_schema = DataFrameSchema(
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
