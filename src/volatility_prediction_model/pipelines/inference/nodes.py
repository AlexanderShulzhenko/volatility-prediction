from typing import Any, Dict

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV

from ..feature_engineering.nodes import (
    fe_candlestick_data,
    fe_indicators,
    fe_stochastic,
    get_inv_cov,
)


def preprocess_data(klines: pd.DataFrame) -> pd.DataFrame:
    klines["open_time"] = pd.to_datetime(klines["open_time"])
    klines["open"] = klines["open"].astype(float)
    klines["high"] = klines["high"].astype(float)
    klines["low"] = klines["low"].astype(float)
    klines["close"] = klines["close"].astype(float)
    return klines


def generate_features(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    # Candlestick data
    features_candlestick_data = fe_candlestick_data(data.copy())
    features_candlestick_data = features_candlestick_data[
        ["close_time", "open_time"] + list(features_candlestick_data.columns.intersection(params["features"]))
    ]
    # Indicators
    features_indicators = fe_indicators(data.copy())
    features_indicators = features_indicators[
        ["open_time"] + list(features_indicators.columns.intersection(params["features"]))
    ]
    # Stochastic
    # TODO: change `close_time` to `open_time`
    inv_cov_dct = get_inv_cov()
    features_stochastic = fe_stochastic(data.copy(), inv_cov_dct, None)
    features_stochastic = features_stochastic[
        ["close_time"] + list(features_stochastic.columns.intersection(params["features"]))
    ]

    # Combination
    inference_master_table = features_candlestick_data.merge(features_indicators, on="open_time", how="left")
    inference_master_table = inference_master_table.merge(features_stochastic, on="close_time", how="left")

    return inference_master_table


def run_model(
    calibrated_clf: CalibratedClassifierCV,
    inference_master_table: pd.DataFrame,
    params: Dict[str, Any],
) -> pd.DataFrame:
    model_input_table = inference_master_table[params["features"]]
    y_pred = calibrated_clf.predict_proba(model_input_table)

    predictions = inference_master_table.copy()
    predictions["prediction"] = y_pred[:, 1]

    return predictions
