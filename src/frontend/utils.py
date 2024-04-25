"""Util functions for frontend"""
import datetime as dt
from typing import Any, Dict

import pandas as pd
from binance import Client
from runner import run_kedro_pipeline

client = Client()


KLINES_COLS = [
    "open_time",
    "close_time",
    "symbol",
    "interval",
    "ft_id",
    "lt_id",
    "open",
    "close",
    "high",
    "low",
    "bav",
    "num_trades",
    "close_flag",
    "qav",
    "taker1",
    "taker2",
    "ignore",
]


def populate_data(num_records: int, symbol: str, interval: str) -> pd.DataFrame:
    """Populate klines data from now with num_records rows.

    Args:
        num_records: number of records to be fetched
        symbol: trading symbol to fetch records for, e.g. BTCUSDT
        interval: interval to fetch records for, e.g. 15m
    Returns:
        data: dataframe with klines data
    """
    interval_mins = int(interval[:-1])
    time = dt.datetime.now() - dt.timedelta(hours=4)
    print(str(time - dt.timedelta(minutes=num_records * interval_mins)))
    klines = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=str(time - dt.timedelta(minutes=num_records * interval_mins)),
        end_str=str(time),
    )
    data = pd.DataFrame(klines)
    data.columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "bav",
        "close_time",
        "qav",
        "num_trades",
        "taker1",
        "taker2",
        "ignore",
    ]
    data["close_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in data.close_time]
    data["open_time"] = [dt.datetime.fromtimestamp(x / 1000.0) for x in data.open_time]
    data["close"] = data["close"].astype("float")
    data["open"] = data["open"].astype("float")
    data["high"] = data["high"].astype("float")
    data["low"] = data["low"].astype("float")
    data["bav"] = data["bav"].astype("float")
    return data


def get_metrics(live_data: pd.DataFrame) -> Dict[str, Any]:
    """Get metrics from the klines data.

    Args:
        live_data: dataframe with live klines data
    Returns:
        metrics: dictionary with needed metrics
    """
    metrics = {}
    last_price = live_data["close"].iloc[-1]
    last_volume = live_data["bav"].iloc[-1]
    last_numt = live_data["num_trades"].iloc[-1]
    if len(live_data) > 1:
        prev_price = live_data["close"].iloc[-2]
        prev_volume = live_data["bav"].iloc[-2]
        prev_numt = live_data["num_trades"].iloc[-2]
    else:
        prev_price = last_price
        prev_volume = last_volume
        prev_numt = last_numt
    price_diff = last_price - prev_price
    volume_diff = last_volume - prev_volume
    numt_diff = last_numt - prev_numt

    metrics["last_price"] = last_price
    metrics["price_diff"] = price_diff
    metrics["last_volume"] = last_volume
    metrics["volume_diff"] = volume_diff
    metrics["last_numt"] = last_numt
    metrics["numt_diff"] = numt_diff

    return metrics


async def get_model_stats(live_data: pd.DataFrame) -> Dict[str, Any]:
    """Get stats after the model run.

    Args:
        live_data: dataframe with live klines data
    Returns:
        stats: dictionary with needed stats
    """
    project_path = "/Users/alexshulzhenko/PycharmProjects/model/"

    # Save newest data to dir
    live_data.to_csv("data/02_intermediate/klines.csv")
    # Run kedro pipeline
    run_kedro_pipeline(project_path, "inference")

    # Reprting
    stats = {}
    stats["time"] = live_data["open_time"].iloc[-1]

    inference_pipeline_output = pd.read_csv("data/07_model_output/model_output_inference.csv")
    stats["prediction"] = inference_pipeline_output["prediction"].iloc[-1]
    stats["prev_prediction"] = inference_pipeline_output["prediction"].iloc[-2]

    stats["data"] = inference_pipeline_output[["open_time", "prediction"]]

    stats["GKHV"] = inference_pipeline_output["Garman_Klass_HV_4"].iloc[-1]
    stats["prev_GKHV"] = inference_pipeline_output["Garman_Klass_HV_4"].iloc[-2]
    stats["bbw"] = inference_pipeline_output["bbw%"].iloc[-1]
    stats["prev_bbw"] = inference_pipeline_output["bbw%"].iloc[-2]
    stats["coef"] = inference_pipeline_output["coefs"].iloc[-1]
    stats["prev_coef"] = inference_pipeline_output["coefs"].iloc[-2]
    return stats
