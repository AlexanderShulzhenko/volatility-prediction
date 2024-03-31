from kedro.pipeline import Pipeline, node, pipeline

from .nodes import calibrate_model, evaluate_model, split_data, train_model
from .plotting_utils import generate_plots


def create_pipeline(**kwargs) -> Pipeline:  # type: ignore
    return pipeline(
        [
            node(
                func=split_data,
                inputs=["feature_table", "params:model_options"],
                outputs=["X_train", "X_test", "y_train", "y_test"],
                name="split_data_node",
            ),
            node(
                func=train_model,
                inputs=["X_train", "y_train", "params:model_options"],
                outputs="clf",
                name="train_model_node",
            ),
            node(
                func=calibrate_model,
                inputs=["clf", "X_train", "y_train"],
                outputs="calibrated_clf",
                name="calibrate_model_node",
            ),
            node(
                func=evaluate_model,
                inputs=["calibrated_clf", "X_train", "X_test", "y_train", "y_test"],
                outputs=["model_output_train", "model_output_test"],
                name="evaluate_model_node",
            ),
            node(
                func=generate_plots,
                inputs=[
                    "clf",
                    "X_train",
                    "model_output_train",
                    "model_output_test",
                ],
                outputs=None,
                name="generate_plots_node",
            ),
        ]
    )
