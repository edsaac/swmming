import pytest
import pathlib

from io import StringIO

import swmming as sw


@pytest.fixture
def transect1():
    return sw.Transect(
        name="transect1",
        station=list(range(11)),
        elevation=list(range(10, 5, -1)) + list(range(5, 11, 1)),
        nleft=0.020,
        nright=0.020,
        nchannel=0.010,
        xleft=1.0,
        xright=3.0,
        station_modifier=0.80,
        elev_offset=0.0,
    )


@pytest.fixture
def transect2():
    return sw.Transect(
        name="transect2",
        station=list(range(11)),
        elevation=list(range(10, 0, -2)) + list(range(0, 12, 2)),
        nleft=0.025,
        nright=0.025,
        nchannel=0,
        xleft=1.0,
        xright=3.0,
    )


@pytest.fixture
def j1():
    return sw.Junction(
        name="j1",
        elevation=5.0,
    )


@pytest.fixture
def j2():
    return sw.Junction(
        name="j2",
        elevation=0.0,
    )


@pytest.fixture
def out1():
    return sw.Outfall(name="out1", elevation=-1.0, type_of_outfall="FREE")


@pytest.fixture
def s1(j1, raingage_1):
    return s1.Subcatchment(
        name="s1",
        rain_gage=raingage_1,
        outlet=j1,
        area=100.0,
        percent_imperv=100,
        width=100,
        slope=0.15,
    )


@pytest.fixture
def sa1(s1):
    return sw.Subarea(
        subcatchment=s1,
        nimp=0.015,
        nperv=0.123,
        simp=0,
        sperv=0,
        percent_zero=0,
    )


@pytest.fixture
def c1(j1, j2):
    return sw.Conduit("c1", j1, j2, length=100.0, roughness=0.015)


@pytest.fixture
def c2(j1, out1):
    return sw.Conduit("c2", j1, out1, length=120.0, roughness=0.010)


@pytest.fixture
def xs1(c1, transect1):
    return sw.XSection(link=c1, shape=sw.XShapes.Irregular(), tsect=transect1)


@pytest.fixture
def xs2(c2, transect2):
    return sw.XSection(link=c2, shape=sw.XShapes.Irregular(), tsect=transect2)


def test_transect(transect1, transect2):
    with StringIO() as stream:
        sw.Transect.make_inp(
            stream=stream,
            transects=[transect1, transect2],
        )

        transect_lines = stream.getvalue().splitlines()

        # Test header
        assert transect_lines[0] == "[TRANSECTS]"

        # Test first transect n Manning's roughness
        assert transect_lines[3].strip() == "NC 0.0200      0.0200     0.0100"

        # Test first transect modifiers
        assert transect_lines[4].strip() == (
            "X1 transect1         11       1.00     3.00     0.0      0.0      0.00     0.80     0.0"
        )

        # Test second transect elevation/station pairs
        assert transect_lines[11].strip() == (
            "GR 10.00    0.00     8.00     1.00     6.00     2.00     4.00     3.00     2.00     4.00"
        )


def test_xsection(xs1, xs2):
    with StringIO() as stream:
        sw.XSection.make_inp(
            stream=stream,
            xsections=[xs1, xs2],
        )

        assert stream.getvalue() == (
            "[XSECTIONS]\n"
            ";;Link           Shape        Geom1            Geom2      Geom3      Geom4      Barrels    Culvert   \n"
            ";;-------------- ------------ ---------------- ---------- ---------- ---------- ---------- ----------\n"
            "c1               IRREGULAR    transect1       \n"
            "c2               IRREGULAR    transect2       \n"
        )


def test_generate_inp(
    j1,
    j2,
    out1,
    c1,
    c2,
    xs1,
    xs2,
    transect1,
    transect2,
):
    title = sw.Title(
        header="Test Project Transects",
        description=f"A test project for swmming generated by {__name__}",
    )

    options = sw.Options(
        flow_units="LPS",
        flow_routing="DYNWAVE",
    )

    junctions = [j1, j2]
    outfalls = [out1]
    conduits = [c1, c2]
    xsections = [xs1, xs2]
    transects = [transect1, transect2]

    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(
            stream,
            title=title,
            options=options,
            junctions=junctions,
            outfalls=outfalls,
            conduits=conduits,
            xsections=xsections,
            transects=transects,
        )

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()
