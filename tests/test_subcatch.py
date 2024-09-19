import pytest
import pathlib

from io import StringIO

import swmming as sw


@pytest.fixture
def j1():
    return sw.Junction(name="j1", elevation=150.0)


@pytest.fixture
def timeseries1():
    return sw.Timeseries(
        name="timeseries1",
        time_ts=[0, 1, 2, 3],
        value_ts=[0, 0.5, 1.0, 0.15],
        date_ts="1/1/2022",
        hour_ts="00:00",
        description="A short description of timeseries1",
    )


@pytest.fixture
def timeseries2():
    return sw.Timeseries(
        name="timeseries2",
        time_ts=[0, 1, 2, 3],
        value_ts=[0, 0, 0, 0],
        date_ts="1/1/2022",
        hour_ts="00:00",
    )


@pytest.fixture
def timeseries3():
    return sw.Timeseries(
        name="timeseries3",
        time_ts=[0, 1, 2],
        value_ts=[10, 20, 50],
        date_ts="1/1/2022",
        hour_ts="00:10",
        description="A loong description " * 5,
    )


@pytest.fixture
def raingage1(timeseries1):
    return sw.Raingage(
        name="rg1", form="INTENSITY", interval="1:00", tseries=timeseries1
    )


@pytest.fixture
def raingage2(timeseries3):
    return sw.Raingage(name="rg2", form="VOLUME", interval="1:00", tseries=timeseries3)


@pytest.fixture
def s1(j1, raingage1):
    return sw.Subcatchment(
        name="s1",
        rain_gage=raingage1,
        outlet=j1,
        area=100.0,
        percent_imperv=100,
        width=100,
        slope=0.15,
    )


@pytest.fixture
def s2(j1, raingage2):
    return sw.Subcatchment(
        name="s2",
        rain_gage=raingage2,
        outlet=j1,
        area=200.0,
        percent_imperv=25,
        width=123,
        slope=0.9,
    )


@pytest.fixture
def subarea1(s1):
    return sw.Subarea(
        subcatchment=s1,
        nimp=0.015,
        nperv=0.123,
        simp=0.010,
        sperv=0.011,
        percent_zero=50,
    )


@pytest.fixture
def subarea2(s2):
    return sw.Subarea(
        subcatchment=s2,
        nimp=0.015,
        nperv=0.123,
        simp=0.109,
        sperv=0.1,
        percent_zero=10,
    )


@pytest.fixture
def infiltration1(s1):
    return sw.Infiltration(
        subcatchment=s1,
        method="HORTON",
        parameters=[1, 2, 3, 4, 5],
    )


@pytest.fixture
def infiltration2(s2):
    return sw.Infiltration(
        subcatchment=s2,
        method="MODIFIED_GREEN_AMPT",
        parameters=[10, 20, 30],
    )


@pytest.fixture
def node_vertices1(j1):
    return [sw.Coordinate(node=j1, coord=(5, 15))]


@pytest.fixture
def polygon_vertices1(s1, s2):
    s1_polygon = [
        sw.PolygonVertex(subcatchment=s1, coord=(x, y))
        for x, y in [
            (0, 0),
            (10, 0),
            (10, 10),
            (6, 10),
            (6, 4),
            (0, 4),
            (0, 0),
        ]
    ]

    s2_polygon = [
        sw.PolygonVertex(subcatchment=s2, coord=(x, y))
        for x, y in [
            (20, 20),
            (15, 18),
            (21, 14),
        ]
    ]

    return s1_polygon + s2_polygon


def test_timeseries(timeseries1, timeseries2, timeseries3):
    with StringIO() as stream:
        sw.Timeseries.make_inp(
            timeseries=[timeseries1, timeseries2, timeseries3],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[TIMESERIES]\n"
            ";;Name           Date       Time       Value     \n"
            ";;-------------- ---------- ---------- ----------\n"
            "; A short description of timeseries1             \n"
            "timeseries1      1/1/2022   0.00       0.000     \n"
            "timeseries1                 1.00       0.500     \n"
            "timeseries1                 2.00       1.000     \n"
            "timeseries1                 3.00       0.150     \n"
            ";                                                \n"
            "timeseries2      1/1/2022   0.00       0.000     \n"
            "timeseries2                 1.00       0.000     \n"
            "timeseries2                 2.00       0.000     \n"
            "timeseries2                 3.00       0.000     \n"
            "; A loong description A loong description A loong\n"
            "; description A loong description A loong        \n"
            "; description                                    \n"
            "timeseries3      1/1/2022   0.00       10.000    \n"
            "timeseries3                 1.00       20.000    \n"
            "timeseries3                 2.00       50.000    \n"
        )


def test_raingage(raingage1, raingage2):
    with StringIO() as stream:
        sw.Raingage.make_inp(
            raingages=[raingage1, raingage2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[RAINGAGES]\n"
            ";;Name           Format    Interval  SCF    Source    \n"
            ";;-------------- --------- --------- ------ ----------\n"
            "rg1              INTENSITY 1:00      1.00   TIMESERIES timeseries1 \n"
            "rg2              VOLUME    1:00      1.00   TIMESERIES timeseries3 \n"
        )


def test_subcatchments(s1, s2):
    with StringIO() as stream:
        sw.Subcatchment.make_inp(
            stream=stream,
            subcatchments=[s1, s2],
        )

        assert stream.getvalue() == (
            "[SUBCATCHMENTS]\n"
            ";;Name           Rain Gage        Outlet           Area     %Imperv  Width    %Slope   CurbLen  SnowPack        \n"
            ";;-------------- ---------------- ---------------- -------- -------- -------- -------- -------- ----------------\n"
            "s1               rg1              j1               100.00   100.00   100.00   0.1500   0.00                     \n"
            "s2               rg2              j1               200.00   25.00    123.00   0.9000   0.00                     \n"
        )


def test_subarea(subarea1, subarea2):
    with StringIO() as stream:
        sw.Subarea.make_inp(
            subareas=[subarea1, subarea2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[SUBAREAS]\n"
            ";;Subcatchment   N-Imperv   N-Perv     S-Imperv   S-Perv     PctZero    RouteTo    PctRouted \n"
            ";;-------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------\n"
            "s1               0.0150     0.1230     0.0100     0.0110     50.00      OUTLET     100.00    \n"
            "s2               0.0150     0.1230     0.1090     0.1000     10.00      OUTLET     100.00    \n"
        )


def test_infiltration(infiltration1, infiltration2):
    with StringIO() as stream:
        sw.Infiltration.make_inp(
            infiltrations=[infiltration1, infiltration2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[INFILTRATION]\n"
            ";;Subcatchment   Param1     Param2     Param3     Param4     Param5    \n"
            ";;-------------- ---------- ---------- ---------- ---------- ----------\n"
            "s1               1.00       2.00       3.00       4.00       5.00       HORTON\n"
            "s2               10.00      20.00      30.00                            MODIFIED_GREEN_AMPT\n"
        )


def test_node_vertices(node_vertices1):
    with StringIO() as stream:
        sw.Coordinate.make_inp(
            stream=stream,
            coordinates=node_vertices1,
        )

        assert stream.getvalue() == (
            "[COORDINATES]\n"
            ";;Node           X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
            "j1               5.000              15.000            \n"
        )


def test_polygon(polygon_vertices1):
    with StringIO() as stream:
        sw.PolygonVertex.make_inp(
            stream=stream,
            vertices=polygon_vertices1,
        )

        assert stream.getvalue() == (
            "[POLYGONS]\n"
            ";;Subcatchment   X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
            "s1               0.000              0.000             \n"
            "s1               10.000             0.000             \n"
            "s1               10.000             10.000            \n"
            "s1               6.000              10.000            \n"
            "s1               6.000              4.000             \n"
            "s1               0.000              4.000             \n"
            "s1               0.000              0.000             \n"
            "s2               20.000             20.000            \n"
            "s2               15.000             18.000            \n"
            "s2               21.000             14.000            \n"
        )


def test_generate_inp(
    j1,
    s1,
    s2,
    timeseries1,
    timeseries2,
    timeseries3,
    subarea1,
    subarea2,
    infiltration1,
    infiltration2,
    node_vertices1,
    polygon_vertices1,
):
    title = sw.Title(
        header="Test Project Subcatchments",
        description=f"A test project for swmming generated by {__name__}",
    )

    options = sw.Options(
        flow_units="LPS",
        flow_routing="KINWAVE",
    )

    junctions = [j1]
    subcatchments = [s1, s2]
    subareas = [subarea1, subarea2]
    infiltration = [infiltration1, infiltration2]
    timeseries = [timeseries1, timeseries2, timeseries3]
    coordinates = node_vertices1
    polygons = polygon_vertices1

    map = sw.Map(dimensions=[-10.0, -10.0, 30.0, 20.0], units="METERS")

    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(
            stream,
            title=title,
            options=options,
            junctions=junctions,
            subcatchments=subcatchments,
            subareas=subareas,
            infiltration=infiltration,
            timeseries=timeseries,
            coordinates=coordinates,
            polygons=polygons,
            map=map,
        )

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()
