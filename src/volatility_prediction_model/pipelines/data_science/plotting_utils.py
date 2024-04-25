# TODO: check if plt.close() are needed
import logging
from typing import Any, Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    auc,
    roc_curve,
)

logger = logging.getLogger(__name__)


PATH = "data/08_reporting/"


def save_fig(fig: plt.figure, name: str) -> None:
    fig.savefig(PATH + name + ".png")


def plot_roc_auc(model_output_train: pd.DataFrame, model_output_test: pd.DataFrame) -> plt.figure:
    """Plot ROC curve for the given feature.

    Args:
        features_data: features data frame
        column_name: name of the selected feature
    Outputs:
        None
    """
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    labels = ["Train", "Test"]
    for i, dataset in enumerate([model_output_train, model_output_test]):
        dataset = dataset.sort_values(by="prediction").reset_index(drop=True)
        fprs, tprs, _ = roc_curve(dataset["target"], dataset["prediction"])
        ax[i].plot(1 - tprs, 1 - fprs, color="black")
        ax[i].plot([0, 1], [0, 1], color="gray", linestyle="--")

        ax[i].title.set_text(f"{labels[i]} \n AUC: " + str(round(100 * auc(1 - tprs, 1 - fprs), 1)))
    plt.close()
    return fig


def plot_feature_importances(clf: LGBMClassifier) -> plt.figure:
    fig, ax = plt.subplots(figsize=(7, 5), dpi=100)

    ax.barh(
        np.array(clf.booster_.feature_name())[np.argsort(clf.feature_importances_)[::-1]],
        sorted(clf.feature_importances_, reverse=True),
        align="center",
        linewidth=0,
    )
    for i, v in enumerate(sorted(clf.feature_importances_, reverse=True)):
        ax.text(v + 2, i + 0.2, str(round(v, 3)), color="black")

    for d in ["left", "right", "top", "bottom"]:
        ax.spines[d].set_visible(False)

    ax.axes.get_xaxis().set_visible(False)
    ax.invert_yaxis()

    fig.tight_layout()
    plt.close()
    return fig


def plot_buckets(model_output_train: pd.DataFrame, model_output_test: pd.DataFrame) -> plt.figure:
    fig, ax = plt.subplots(1, 2, figsize=(15, 5))
    labels = ["Train", "Test"]
    for i, dataset in enumerate([model_output_train, model_output_test]):
        dataset = dataset.sort_values(by="prediction").reset_index(drop=True)
        bad_rate = []
        bad_num = []
        for bucket in np.array_split(dataset, 20):
            bad_rate.append(bucket["target"].mean())
            bad_num.append(bucket["target"].sum())
        logger.info(
            f"Last bucket on {labels[i]} captures "
            + str(round(100 * sum(bad_num[-1:]) / sum(bad_num), 2))
            + "% of total positives.",
        )

        ax[i].plot(bad_rate)
        ax[i].set_xlabel("bucket number")
        ax[i].set_ylabel("bad rate")
        ax[i].title.set_text(labels[i])
    plt.close()
    return fig


def plot_calibration_curve(
    clf: CalibratedClassifierCV,
    X_train: pd.DataFrame,
    model_output_train: pd.DataFrame,
    model_output_test: pd.DataFrame,
) -> plt.figure:
    y_pred_uncalibrated = clf.predict_proba(X_train)
    model_output_train["prediction_uncalibrated"] = y_pred_uncalibrated[:, 1]

    fig, ax = plt.subplots(1, 1)
    fop_calibrated, mpv_calibrated = calibration_curve(
        model_output_train["target"],
        model_output_train["prediction"],
        n_bins=10,
    )
    fop_uncalibrated, mpv_uncalibrated = calibration_curve(
        model_output_train["target"],
        model_output_train["prediction_uncalibrated"],
        n_bins=10,
    )
    # plot perfectly calibrated
    ax.plot([0, 1], [0, 1], linestyle="--")
    # plot model reliability
    ax.plot(mpv_calibrated, fop_calibrated, marker=".", label="calibrated")
    ax.plot(mpv_uncalibrated, fop_uncalibrated, marker=".", label="uncalibrated")
    ax.legend()
    ax.set_xlabel("predicted probability")
    ax.set_ylabel("true probability")
    plt.close()
    return fig


def plot_partial_dependencies(model: LGBMClassifier, data: pd.DataFrame, feature: str) -> plt.figure:
    fig, ax = shap.partial_dependence_plot(
        ind=feature,
        model=model.predict,
        data=data,
        model_expected_value=True,
        feature_expected_value=True,
        show=False,
        ice=False,
    )
    plt.close()
    return fig


def plot_summary(explainer: shap.TreeExplainer, data: pd.DataFrame) -> plt.figure:
    shap_values = explainer(data)

    fig, ax = plt.subplots()
    shap.summary_plot(shap_values=shap_values, show=False)
    fig.tight_layout()
    plt.close()
    return fig


def generate_plots(
    clf: LGBMClassifier,
    explainer: shap.TreeExplainer,
    X_train: pd.DataFrame,
    model_output_train: pd.DataFrame,
    model_output_test: pd.DataFrame,
    parameters: Dict[str, Any],
) -> None:
    # ROC-curve
    fig = plot_roc_auc(model_output_train, model_output_test)
    save_fig(fig, "roc_curve")
    logger.info("ROC-curve plot created")
    # Feature importances
    fig = plot_feature_importances(clf)
    save_fig(fig, "feature_importances")
    logger.info("Feature importances plot created")
    # Buckets
    fig = plot_buckets(model_output_train, model_output_test)
    save_fig(fig, "buckets")
    logger.info("Bucket plot created")
    # Calibration curve
    fig = plot_calibration_curve(clf, X_train, model_output_train, model_output_test)
    save_fig(fig, "calibration_curve")
    logger.info("Calibration curve plot created")
    # SHAP
    for feature in parameters["features"]:
        fig = plot_partial_dependencies(clf, X_train, feature)
        save_fig(fig, f"pdp/{feature}")
    logger.info("PDPs created")
    fig = plot_summary(explainer, X_train)
    save_fig(fig, "summary")
    logger.info("Summary plot created")
