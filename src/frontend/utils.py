KLINES_COLS = [
    "start_time",
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


def get_metrics(live_data):
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
