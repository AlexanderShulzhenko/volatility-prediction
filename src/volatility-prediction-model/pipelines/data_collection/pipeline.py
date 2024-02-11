from kedro.pipeline import Pipeline, node, pipeline

from .nodes import get_candlestick_data, save_candlestick_data


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=get_candlestick_data,
            inputs=None,
            outputs="data_collection"
        ),
        node(
            func=save_candlestick_data,
            inputs="data_collection",
            outputs="temp_candlesticks_partitioned"
        )
    ])
