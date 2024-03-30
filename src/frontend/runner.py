from typing import List

from kedro.framework.session.session import KedroSession
from kedro.framework.startup import bootstrap_project


def run_kedro_pipeline(
    path: str,
    pipeline_name: str,
    nodel_names: List[str] = None,
) -> None:
    bootstrap_project(path)
    with KedroSession.create() as session:
        session.run(pipeline_name=pipeline_name, node_names=nodel_names)


# run_kedro_pipeline("/Users/alexshulzhenko/PycharmProjects/model/", "inference")
