import pytest  # noqa
import pathlib

import swmming as sw


def test_base_inp():
    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(stream=stream)

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()
