from kedro.pipeline import Pipeline, node, pipeline

from .nodes import get_candlestick_data


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline([
        node(
            func=get_candlestick_data,
            inputs=None,
            outputs="candlesticks_partitioned"
        ),
    ])
