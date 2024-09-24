import pytest  # noqa
import pathlib

import swmming as sw
import swmming.api.wrappers as swio


def test_base_inp():
    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(stream=stream)

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()


def test_open_swmm():
    rtn = swio.open_swmm(
        input_file=f"./tests/inp_files/{__name__}.inp",
        report_file=f"./tests/inp_files/{__name__}.rpt",
        output_file=f"./tests/inp_files/{__name__}.out",
    )

    assert rtn == 0

    swio.close_swmm()
