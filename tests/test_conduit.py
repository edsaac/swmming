import pytest
import pathlib
from io import StringIO

import swmming as sw


@pytest.fixture
def project_map():
    return sw.Map(dimensions=[-50.0, -50.0, 300.0, 150.0], units="METERS")


@pytest.fixture
def circle():
    return sw.XShapes.Circular(diameter=10.0)


@pytest.fixture
def trapezoid():
    return sw.XShapes.Trapezoidal(
        full_height=10.0,
        base_width=5.0,
        left_slope=2.0,
        right_slope=2.5,
    )


@pytest.fixture
def j1():
    return sw.Junction(name="j1", elevation=10.0)


@pytest.fixture
def j1_coord(j1):
    return sw.Coordinate(node=j1, coord=(0.0, 0.0))


@pytest.fixture
def j2():
    return sw.Junction(name="j2", elevation=9.0)


@pytest.fixture
def j2_coord(j2):
    return sw.Coordinate(node=j2, coord=(100.0, 0.0))


@pytest.fixture
def out1():
    return sw.Outfall(name="out1", elevation=8.0, type_of_outfall="FREE")


@pytest.fixture
def out1_coord(out1):
    return sw.Coordinate(node=out1, coord=(250.0, 100.0))


@pytest.fixture
def conduit1(j1, j2):
    return sw.Conduit(
        name="c1", from_node=j1, to_node=j2, length=100.0, roughness=0.015
    )


@pytest.fixture
def conduit1_vertices(conduit1):
    x = range(10, 100, 10)
    y = (0.50 * (-((xi - 50) ** 2) / 50 + 50) for xi in x)

    return [sw.LinkVertex(link=conduit1, coord=[x, y]) for x, y in zip(x, y)]


@pytest.fixture
def conduit2(j2, out1):
    return sw.Conduit(
        name="c2", from_node=j2, to_node=out1, length=200.0, roughness=0.012
    )


@pytest.fixture
def conduit2_vertices(conduit2):
    return [sw.LinkVertex(link=conduit2, coord=[150, 50])]


@pytest.fixture
def xsection1(conduit1, circle):
    return sw.XSection(link=conduit1, shape=circle)


@pytest.fixture
def xsection2(conduit2, trapezoid):
    return sw.XSection(link=conduit2, shape=trapezoid)


def test_junction(j1, j2):
    with StringIO() as stream:
        sw.Junction.make_inp(
            junctions=[j1, j2],
            stream=stream,
        )

        print(stream.getvalue())
        assert stream.getvalue() == (
            "[JUNCTIONS]\n"
            ";;Name           Elevation  MaxDepth   InitDepth  SurDepth   Aponded    \n"
            ";;-------------- ---------- ---------- ---------- ---------- ---------- \n"
            "j1               10.000     0.00       0.00       0.00       0          \n"
            "j2               9.000      0.00       0.00       0.00       0          \n"
        )


def test_outfall(out1):
    with StringIO() as stream:
        sw.Outfall.make_inp(
            outfalls=[out1],
            stream=stream,
        )
        assert stream.getvalue() == (
            "[OUTFALLS]\n"
            ";;Name           Elevation  Type       Stage Data       Gated    Route To        \n"
            ";;-------------- ---------- ---------- ---------------- -------- ----------------\n"
            "out1             8.000      FREE                        NO       \n"
        )


def test_conduit(conduit1, conduit2):
    with StringIO() as stream:
        sw.Conduit.make_inp(
            conduits=[conduit1, conduit2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[CONDUITS]\n"
            ";;Name           From Node        To Node          Length     Roughness  InOffset   OutOffset  InitFlow   MaxFlow   \n"
            ";;-------------- ---------------- ---------------- ---------- ---------- ---------- ---------- ---------- ----------\n"
            "c1               j1               j2               100.00     0.01500    0.00       0.00       0.00                 \n"
            "c2               j2               out1             200.00     0.01200    0.00       0.00       0.00                 \n"
        )


def test_coordinate(j1_coord, j2_coord, out1_coord):
    with StringIO() as stream:
        sw.Coordinate.make_inp(
            coordinates=[j1_coord, j2_coord, out1_coord],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[COORDINATES]\n"
            ";;Node           X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
            "j1               0.000              0.000             \n"
            "j2               100.000            0.000             \n"
            "out1             250.000            100.000           \n"
        )


def test_vertices(conduit1_vertices, conduit2_vertices):
    with StringIO() as stream:
        all_vertices = conduit1_vertices + conduit2_vertices

        sw.LinkVertex.make_inp(
            vertices=all_vertices,
            stream=stream,
        )

        assert stream.getvalue() == (
            "[VERTICES]\n"
            ";;Link           X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
            "c1               10.000             9.000             \n"
            "c1               20.000             16.000            \n"
            "c1               30.000             21.000            \n"
            "c1               40.000             24.000            \n"
            "c1               50.000             25.000            \n"
            "c1               60.000             24.000            \n"
            "c1               70.000             21.000            \n"
            "c1               80.000             16.000            \n"
            "c1               90.000             9.000             \n"
            "c2               150.000            50.000            \n"
        )


def test_map(project_map):
    with StringIO() as stream:
        project_map.make_inp(stream=stream)

        assert stream.getvalue() == (
            "[MAP]\n" "DIMENSIONS -50.00 -50.00 300.00 150.00\n" "UNITS     METERS\n"
        )


def test_generate_inp(
    j1,
    j1_coord,
    j2,
    j2_coord,
    out1,
    out1_coord,
    conduit1,
    conduit1_vertices,
    conduit2,
    conduit2_vertices,
    xsection1,
    xsection2,
    project_map,
):
    title = sw.Title(
        header="Test Project Conduit",
        description=f"A test project for swmming generated by {__name__}",
    )

    options = sw.Options(
        flow_units="CFS",
        infiltration="MODIFIED_GREEN_AMPT",
        flow_routing="DYNWAVE",
    )

    junctions = [j1, j2]
    outfalls = [out1]
    conduits = [conduit1, conduit2]
    xsections = [xsection1, xsection2]

    coordinates = [j1_coord, j2_coord, out1_coord]
    vertices = [*conduit1_vertices, *conduit2_vertices]

    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(
            stream,
            title=title,
            options=options,
            junctions=junctions,
            outfalls=outfalls,
            conduits=conduits,
            xsections=xsections,
            coordinates=coordinates,
            vertices=vertices,
            map=project_map,
        )

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()
