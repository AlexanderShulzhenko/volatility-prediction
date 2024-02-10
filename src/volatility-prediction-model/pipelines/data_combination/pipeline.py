from kedro.pipeline import Pipeline, node, pipeline

from .nodes import clean_master_list, concat_partitions


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=concat_partitions,
                inputs="candlesticks_partitioned",
                outputs="concatenated_candlestick_data",
                name="concat_partitions",
            ),
            node(
                func=clean_master_list,
                inputs="master_list",
                outputs="master_list_cleaned",
                name="clean_master_list",
            ),
        ]
    )
