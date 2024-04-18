import logging
from typing import Any, Dict, Tuple

import pandas as pd
import shap
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score

logger = logging.getLogger(__name__)


def split_data(feature_table: pd.DataFrame, parameters: Dict[str, Any]) -> Tuple[pd.DataFrame, ...]:
    X = feature_table[parameters["features"]]
    y = feature_table["target"]
    X_train = X[: parameters["train_size"]]
    X_test = X[parameters["train_size"] :]
    y_train = y[: parameters["train_size"]]
    y_test = y[parameters["train_size"] :]

    return X_train, X_test, y_train, y_test


def train_model(X_train: pd.DataFrame, y_train: pd.Series, parameters: Dict[str, Any]) -> LGBMClassifier:
    clf = LGBMClassifier(
        n_estimators=parameters["n_estimators"],
        max_depth=parameters["max_depth"],
        min_child_samples=parameters["min_child_samples"],
        random_state=parameters["random_state"],
        verbose=-1,
    )
    clf.fit(X_train, y_train)
    return clf


def explain_model(model: LGBMClassifier, data: pd.DataFrame) -> shap.TreeExplainer:
    explainer = shap.TreeExplainer(
        model=model,
        data=data,
        feature_perturbation="interventional",
        model_output="probability",
    )
    return explainer


def calibrate_model(clf: LGBMClassifier, X_train: pd.DataFrame, y_train: pd.Series) -> CalibratedClassifierCV:
    calibrated_clf = CalibratedClassifierCV(clf, method="sigmoid", cv=None)
    calibrated_clf.fit(X_train, y_train)
    return calibrated_clf


def evaluate_model(
    calibrated_clf: CalibratedClassifierCV,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> pd.DataFrame:
    predictions_dct = {}
    for mode, datasets in zip(["train", "test"], [(X_train, y_train), (X_test, y_test)]):
        X = datasets[0]
        y = datasets[1]
        y_pred = calibrated_clf.predict_proba(X)
        score = roc_auc_score(y, y_pred[:, 1])
        logger.info("ROC-AUC score on %s: %.3f", mode, score)

        predictions = X.copy()
        predictions["target"] = y
        predictions["prediction"] = y_pred[:, 1]
        predictions_dct[mode] = predictions
    return predictions_dct["train"], predictions_dct["test"]
