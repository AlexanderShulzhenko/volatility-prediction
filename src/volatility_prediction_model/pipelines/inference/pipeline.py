from kedro.pipeline import Pipeline, node, pipeline

from .nodes import generate_features, preprocess_data, run_model


def create_pipeline(**kwargs) -> Pipeline:  # type: ignore
    return pipeline(
        [
            node(
                func=preprocess_data,
                inputs="klines",
                outputs="klines_preprocessed",
                name="preprocess_data",
            ),
            node(
                func=generate_features,
                inputs=["klines_preprocessed", "params:model_options"],
                outputs="inference_master_table",
                name="generate_features",
            ),
            node(
                func=run_model,
                inputs=["calibrated_clf", "inference_master_table", "params:model_options"],
                outputs="model_output_inference",
                name="run_model_inference",
            ),
        ]
    )
