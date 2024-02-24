from kedro.pipeline import Pipeline, node, pipeline

from .nodes import evaluate_model, split_data, train_model


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
                func=evaluate_model,
                inputs=["clf", "X_train", "X_test", "y_train", "y_test"],
                outputs="model_output_test",
                name="evaluate_model_node",
            ),
        ]
    )
