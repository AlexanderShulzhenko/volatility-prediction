from kedro.pipeline import Pipeline, node, pipeline

from .nodes import clean_master_list, get_candlestick_data, get_trades_data


def create_pipeline(**kwargs) -> Pipeline:  # type: ignore
    return pipeline(
        [
            node(
                func=clean_master_list,
                inputs="master_list",
                outputs="master_list_cleaned",
                name="clean_master_list",
            ),
            node(
                func=get_candlestick_data,
                inputs=None,
                outputs="candlesticks_partitioned",
                name="candlestick_data_collection",
            ),
            node(
                func=get_trades_data,
                inputs="master_list_cleaned",
                outputs="trades_partitioned",
                name="trades_data_collection",
            ),
        ]
    )
