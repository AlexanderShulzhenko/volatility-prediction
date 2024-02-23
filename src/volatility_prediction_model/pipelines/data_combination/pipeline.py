from kedro.pipeline import Pipeline, node, pipeline

from .nodes import concat_partitions


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=concat_partitions,
                inputs="candlesticks_partitioned",
                outputs="concatenated_candlestick_data",
                name="concat_partitions",
            )
        ]
    )
