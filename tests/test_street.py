import pytest
import pathlib

from io import StringIO

import swmming as sw


@pytest.fixture
def street():
    return sw.Street(name="street1", Tcrown=0.2, Hcurb=0.1, Sx=0.1, nRoad=0.050)


@pytest.fixture
def j1():
    return sw.Junction(name="j1", elevation=100.0)


@pytest.fixture
def j2():
    return sw.Junction(name="j2", elevation=99.5)


@pytest.fixture
def out1():
    return sw.Outfall(name="out1", elevation=99.0)


@pytest.fixture
def conduit1(j1, j2):
    return sw.Conduit(
        name="conduit1", length=100.0, from_node=j1, to_node=j2, roughness=0.015
    )


@pytest.fixture
def conduit2(j2, out1):
    return sw.Conduit(
        name="conduit2", length=50.0, from_node=j2, to_node=out1, roughness=0.012
    )


@pytest.fixture
def xsection1(conduit1, street):
    return sw.XSection(conduit1, shape=sw.XShapes.Street(), street=street)


@pytest.fixture
def xsection2(conduit2, street):
    return sw.XSection(conduit2, shape=sw.XShapes.Street(), street=street)


@pytest.fixture
def inlet1():
    return sw.Inlet(
        name="inlet1", type="GRATE", length=2.0, width=0.75, type_grate="P_BAR-50"
    )


@pytest.fixture
def inlet2():
    return sw.Inlet(
        name="inlet2", type="CURB", length=1.2, height=4.8, throat="HORIZONTAL"
    )


@pytest.fixture
def inlet_use1(conduit1, inlet1, j2):
    return sw.InletUsage(conduit=conduit1, inlet=inlet1, node=j2, percent_clogged=25)


@pytest.fixture
def inlet_use2(conduit1, inlet2, j2):
    return sw.InletUsage(conduit=conduit1, inlet=inlet2, node=j2)


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
            "conduit1         j1               j2               100.00     0.01500    0.00       0.00       0.00                 \n"
            "conduit2         j2               out1             50.00      0.01200    0.00       0.00       0.00                 \n"
        )


def test_xsection(xsection1, xsection2):
    with StringIO() as stream:
        sw.XSection.make_inp(
            xsections=[xsection1, xsection2],
            stream=stream,
        )
        assert stream.getvalue() == (
            "[XSECTIONS]\n"
            ";;Link           Shape        Geom1            Geom2      Geom3      Geom4      Barrels    Culvert   \n"
            ";;-------------- ------------ ---------------- ---------- ---------- ---------- ---------- ----------\n"
            "conduit1         STREET       street1         \n"
            "conduit2         STREET       street1         \n"
        )


def test_street(street):
    with StringIO() as stream:
        sw.Street.make_inp(
            streets=[street],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[STREETS]\n"
            ";;Name           Tcrown   Hcurb    Sx       nRoad    a        W        Sides    Tback    Sback    nBack   \n"
            ";;-------------- -------- -------- -------- -------- -------- -------- -------- -------- -------- --------\n"
            "street1          0.20     0.10     0.1000   0.0500   0.00     0.00     1        0.00     0.0000   0.0000  \n"
        )


def test_inlet(inlet1, inlet2):
    with StringIO() as stream:
        sw.Inlet.make_inp(
            inlets=[inlet1, inlet2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[INLETS]\n"
            ";;Name           Type             Parameters:\n"
            ";;-------------- ---------------- -----------\n"
            "inlet1           GRATE            2.00      0.75      P_BAR-50    \n"
            "inlet2           CURB             1.20      4.80      HORIZONTAL  \n"
        )


def test_inlet_usage(inlet_use1, inlet_use2):
    with StringIO() as stream:
        sw.InletUsage.make_inp(
            inlet_usages=[inlet_use1, inlet_use2],
            stream=stream,
        )

        assert stream.getvalue() == (
            "[INLET_USAGE]\n"
            ";;Conduit        Inlet            Node             Number    %Clogged  Qmax      aLocal    wLocal    Placement\n"
            ";;-------------- ---------------- ---------------- --------- --------- --------- --------- --------- --------- ---------\n"
            "conduit1         inlet1           j2               1         25.00     0.00      0.00      0.00      AUTOMATIC          \n"
            "conduit1         inlet2           j2               1         0.00      0.00      0.00      0.00      AUTOMATIC          \n"
        )


def test_generate_inp(
    j1,
    j2,
    out1,
    conduit1,
    conduit2,
    xsection1,
    xsection2,
    street,
    inlet1,
    inlet2,
    inlet_use1,
    inlet_use2,
):
    title = sw.Title(
        header="Test Project Street",
        description=f"A test project for swmming generated by {__name__}",
    )

    options = sw.Options(
        flow_units="LPS",
        infiltration="MODIFIED_GREEN_AMPT",
        flow_routing="DYNWAVE",
    )

    junctions = [j1, j2]
    outfalls = [out1]
    conduits = [conduit1, conduit2]
    xsections = [xsection1, xsection2]
    streets = [street]
    inlets = [inlet1, inlet2]
    inlet_usages = [inlet_use1, inlet_use2]

    with open(f"./tests/inp_files/{__name__}.inp", "w") as stream:
        sw.assemble_inp(
            stream,
            title=title,
            options=options,
            junctions=junctions,
            outfalls=outfalls,
            conduits=conduits,
            xsections=xsections,
            streets=streets,
            inlets=inlets,
            inlet_usages=inlet_usages,
        )

    assert pathlib.Path(f"./tests/inp_files/{__name__}.inp").exists()
