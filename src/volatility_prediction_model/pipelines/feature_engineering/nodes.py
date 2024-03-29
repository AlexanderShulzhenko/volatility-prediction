import logging
import math
from typing import Any, Callable, Dict, List, Tuple

import gpflow
import numpy as np
import pandas as pd
import scipy
import tensorflow as tf
from numba import float64, jit, vectorize
from pandera import check_output
from tqdm import tqdm

from ..schemas.trades_data_schema import trades_data_schema

logger = logging.getLogger(__name__)


class Ornstein_Uhlenbeck(gpflow.kernels.IsotropicStationary):  # type: ignore
    def K_r2(self, r2: float) -> Any:
        return self.variance * tf.exp(-tf.sqrt(r2))


@jit(nopython=True)  # type: ignore
def line_fit(target_values: np.array, window_size: int) -> Tuple[List[float], List[float]]:
    coefs = [np.nan] * window_size
    r2s = [np.nan] * window_size

    X = np.arange(window_size).reshape(-1, 1).astype("float")
    X_pad = np.hstack((np.ones_like(X), X))
    for i in range(window_size, len(target_values)):
        y = target_values[i - window_size : i]
        X_pad_t = X_pad.T
        intercept, slope = np.dot(np.dot(np.linalg.inv(np.dot(X_pad_t, X_pad)), X_pad_t), y)
        pred = X * slope + intercept

        ss_t = (pred.ravel() - y) ** 2
        ss_r = (y - y.mean()) ** 2
        r2 = 1 - (ss_t.sum() / ss_r.sum())
        coefs.append(slope)
        r2s.append(r2)
    return coefs, r2s


def fe_candlestick_data(candlestick_data: pd.DataFrame) -> pd.DataFrame:
    # Date/Time
    candlestick_data["week_day"] = candlestick_data["open_time"].dt.dayofweek
    candlestick_data["hour"] = candlestick_data["open_time"].dt.hour

    # Price change
    candlestick_data["returns_1"] = np.log(candlestick_data["close"].pct_change(1) + 1)
    candlestick_data["returns_4"] = np.log(candlestick_data["close"].pct_change(4) + 1)

    # Garman-Klass Historical Volatility
    c = 2 * np.log(2) - 1
    candlestick_data["GK_HV_inner"] = (
        0.5 * (np.log(candlestick_data["high"] / candlestick_data["low"])) ** 2
        - c * (np.log(candlestick_data["close"] / candlestick_data["open"])) ** 2
    )
    candlestick_data["Garman_Klass_HV_4"] = np.sqrt(candlestick_data["GK_HV_inner"].rolling(4).mean())

    return candlestick_data


def fe_indicators(candlestick_data: pd.DataFrame) -> pd.DataFrame:
    # MA
    candlestick_data["MA_5"] = candlestick_data["close"].rolling(5).mean()
    candlestick_data["MA_40"] = candlestick_data["close"].rolling(40).mean()
    candlestick_data["MA_100"] = candlestick_data["close"].rolling(100).mean()

    candlestick_data["MA_5_under_MA_40"] = np.where(candlestick_data["MA_5"] < candlestick_data["MA_40"], 1, 0)
    candlestick_data["MA_5_under_MA_100"] = np.where(candlestick_data["MA_5"] < candlestick_data["MA_100"], 1, 0)

    candlestick_data["MA_5_MA_100_ratio"] = candlestick_data["MA_5"] / candlestick_data["MA_40"]

    # Bollinger Bands
    candlestick_data["std_10"] = candlestick_data["close"].rolling(10).std()
    candlestick_data["bbh"] = candlestick_data["MA_5"] + 2 * candlestick_data["std_10"]
    candlestick_data["bbl"] = candlestick_data["MA_5"] - 2 * candlestick_data["std_10"]

    candlestick_data["bbw%"] = (candlestick_data["bbh"] - candlestick_data["bbl"]) / candlestick_data["MA_5"]

    # Rolling Linear Regression
    logger.info("Running Linear Regression")
    coefs, r2s = line_fit(candlestick_data["close"].values, 10)
    candlestick_data["coefs"] = coefs
    candlestick_data["r2s"] = r2s

    return candlestick_data


def get_inv_cov() -> Dict[str, Any]:
    inv_cov_dct = {}
    Xplot = np.arange(0, 96, 1).astype(float)[:, None]
    X = np.zeros((0, 1))
    Y = np.zeros((0, 1))

    kernels = {
        "Matern": gpflow.kernels.Matern32,
        "Ornstein_Uhlenbeck": Ornstein_Uhlenbeck,
    }

    for k_type in kernels.keys():
        inv_cov_dct_k = {}
        for ls in range(5, 110, 5):
            k = kernels[k_type](lengthscales=ls, variance=1)
            model = gpflow.models.GPR((X, Y), kernel=k)
            _, cov = model.predict_f(Xplot, full_cov=True)

            cov = cov[0, :, :].numpy()
            inv_cov_dct_k[ls] = scipy.linalg.fractional_matrix_power(cov, -0.5)
        inv_cov_dct[k_type] = inv_cov_dct_k

    return inv_cov_dct


@vectorize([float64(float64)])  # type: ignore
def vec_erf(x: float):
    return math.erf(x)


@jit(nopython=True)  # type: ignore
def kolmogorov_smirnov_test(price_path: np.ndarray, inv_cov: np.ndarray, k_type: str, ls: int) -> Any:
    standardized_path = inv_cov @ price_path
    sorted_path = np.sort(standardized_path.ravel())
    normal_cdf = vec_erf(sorted_path)
    edf = np.arange(1, len(price_path) + 1) / len(price_path)

    p_value = np.exp(-(max(np.abs(edf - normal_cdf)) ** 2) * len(sorted_path))

    return p_value


def fe_stochastic(
    candlestick_data: pd.DataFrame,
    inv_cov_dct: Dict[str, Any],
    master_list: pd.DataFrame = None,
) -> pd.DataFrame:
    if master_list is not None:
        combined = candlestick_data.merge(master_list, how="left", on="close_time")
        idx = combined[combined["target"].notna()].index
    else:
        combined = candlestick_data
        idx = candlestick_data.index[95:]

    test_res = []
    for i in tqdm(idx):
        # Get data for last 24 hours and scale it
        raw_path = combined["close"][i - 95 : i + 1].values
        raw_path_mean = raw_path.mean()
        raw_path_std = raw_path.std()
        price_path = (raw_path - raw_path_mean) / raw_path_std

        # Check for Matern and Ornstein-Uhlenbeck kernels
        res = [combined["close_time"][i]]

        for k_type in inv_cov_dct.keys():
            # Find p_value of Kolmogorov-Smirnov test for each lengthscale
            p_vals = []
            for ls in range(5, 110, 5):
                inv_cov = inv_cov_dct[k_type][ls]
                p_value = kolmogorov_smirnov_test(price_path, inv_cov, k_type, ls)
                p_vals.append(p_value)

            # Shapiro-Wilk second test on found lengthscale to verify
            lengthscale = (np.argmax(p_vals) + 1) * 5
            standardized_path = inv_cov_dct[k_type][lengthscale] @ price_path
            p_value_shapiro = scipy.stats.shapiro(standardized_path).pvalue
            res += [lengthscale, max(p_vals), p_value_shapiro]

        test_res.append(res)

    stochastic_features = pd.DataFrame(test_res)
    stochastic_features.columns = [
        "close_time",
        "lengthscale_Matern32",
        "p_value_KS_Matern32",
        "p_value_SW_Matern32",
        "lengthscale_OU",
        "p_value_KS_OU",
        "p_value_SW_OU",
    ]
    return stochastic_features


def fe_trades(master_list: pd.DataFrame, partitioned_input: Dict[str, Callable[[], Any]]) -> pd.DataFrame:
    trades_features = master_list.drop(columns="target")

    skews = []
    kurtosises = []
    percentile90 = []

    for _partition_key, partition_load_func in tqdm(sorted(partitioned_input.items())):
        # Unwrap the decorator to check the output, increases runtime: might be removed
        trades_data = check_output(trades_data_schema)(partition_load_func)()
        trades_data["returns"] = trades_data["Price"].pct_change()
        trades_data["dolAmount"] = trades_data["Price"] * trades_data["Quantity"]

        # Stats calculated for each trades data frame
        skews.append(trades_data["returns"].skew())
        kurtosises.append(trades_data["returns"].kurtosis())
        percentile90.append(trades_data["dolAmount"].quantile(0.9))

    trades_features["skews"] = skews
    trades_features["kurtosises"] = kurtosises
    trades_features["percentile90"] = percentile90

    return trades_features


def master_list_merge(
    master_list: pd.DataFrame,
    features_candlestick_data: pd.DataFrame,
    features_indicators: pd.DataFrame,
    features_stochastic: pd.DataFrame,
    features_trades: pd.DataFrame,
) -> pd.DataFrame:
    combined_features = master_list
    combined_features = combined_features.merge(features_candlestick_data, how="left", on="close_time")
    combined_features = combined_features.merge(features_indicators, how="left", on="close_time")
    combined_features = combined_features.merge(features_stochastic, how="left", on="close_time")
    combined_features = combined_features.merge(features_trades, how="left", on="close_time")

    return combined_features
