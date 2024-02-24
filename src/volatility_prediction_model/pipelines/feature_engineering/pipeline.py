from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    fe_candlestick_data,
    fe_indicators,
    fe_stochastic,
    fe_trades,
    get_inv_cov,
    master_list_merge,
)


def create_pipeline(**kwargs) -> Pipeline: # type: ignore
    return pipeline(
        [
            node(
                func=fe_candlestick_data,
                inputs="concatenated_candlestick_data",
                outputs="features_candlestick_data",
                name="fe_candlestick_data_node",
            ),
            node(
                func=fe_indicators,
                inputs="concatenated_candlestick_data",
                outputs="features_indicators",
                name="fe_indicators_node",
            ),
            node(
                func=get_inv_cov,
                inputs=None,
                outputs="inversed_covaricance_dict",
                name="get_inversed_covariance_node",
            ),
            node(
                func=fe_stochastic,
                inputs=[
                    "master_list_cleaned",
                    "concatenated_candlestick_data",
                    "inversed_covaricance_dict",
                ],
                outputs="features_stochastic",
                name="fe_stochastic_node",
            ),
            node(
                func=fe_trades,
                inputs=["master_list_cleaned", "trades_partitioned"],
                outputs="features_trades",
                name="fe_trades_node",
            ),
            node(
                func=master_list_merge,
                inputs=[
                    "master_list_cleaned",
                    "features_candlestick_data",
                    "features_indicators",
                    "features_stochastic",
                    "features_trades",
                ],
                outputs="feature_table",
                name="merge_with_masterlist_node",
            ),
        ]
    )
