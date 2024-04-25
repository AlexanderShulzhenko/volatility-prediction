"""Call Kedro pipeline from other module"""
from typing import List

from kedro.framework.session.session import KedroSession
from kedro.framework.startup import bootstrap_project


def run_kedro_pipeline(
    path: str,
    pipeline_name: str,
    node_names: List[str] = None,
) -> None:
    """Calls Kedro pipeline.

    Args:
        path: project directory
        pipeline_name: name of the pipeline to be ran
        node_names: node names to be ran
    Returns:
    """
    bootstrap_project(path)
    with KedroSession.create() as session:
        session.run(pipeline_name=pipeline_name, node_names=node_names)


# run_kedro_pipeline("/Users/alexshulzhenko/PycharmProjects/model/", "inference")
