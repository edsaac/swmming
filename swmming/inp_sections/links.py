from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self, Literal

from .base_topology import Node, Link
from .tabular import Curve


@dataclass
class Conduit(Link):
    """Identifies each conduit link of the drainage system.
    Conduits are pipes or channels that convey water from one node to another

    Attributes
    ----------
    name : str
        Name assigned to conduit link.
    from_node : Node
        Name of the conduit's upstream node.
    to_node : Node
        Name of the conduit's downstream node.
    length : float
        Conduit length (ft or m).
    roughness : float
        Manning's roughness coefficient (n).
    in_offset : float = 0
        Offset of the conduit's upstream end above the invert of its upstream
        node (ft or m).
    out_offset : float = 0
        Offset of the conduit's downstream end above the invert of its downstream
        node (ft or m).
    init_flow : float, optional = 0
        Flow in the conduit at the start of the simulation (flow units). Default is
        0.
    max_flow : float, optional = None
        Maximum flow allowed in the conduit (flow units). Default is no limit.
    """

    length: float
    roughness: float
    in_offset: float = 0
    out_offset: float = 0
    init_flow: float = 0
    max_flow: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.from_node, Node):
            raise ValueError(
                "from_node must be a BaseNode object, like a Junction or an Outfall"
            )

        if not isinstance(self.to_node, Node):
            raise ValueError(
                "to_node must be a BaseNode object, like a Junction or an Outfall"
            )

    @property
    def as_inp(self):
        if self.max_flow is not None:
            str_max_flow = f"{self.max_flow: <10.2f}"
        else:
            str_max_flow = " " * 10

        return f"{self.name: <16} {self.from_node.name: <16} {self.to_node.name: <16} {self.length: <10.2f} {self.roughness: <10.5f} {self.in_offset: <10.2f} {self.out_offset: <10.2f} {self.init_flow: <10.2f} {str_max_flow}"

    @classmethod
    def make_inp(cls, stream: TextIO, conduits: Iterable[Self]):
        stream.write("[CONDUITS]\n")
        stream.write(
            ";;Name           From Node        To Node          Length     Roughness  InOffset   OutOffset  InitFlow   MaxFlow   \n"
            ";;-------------- ---------------- ---------------- ---------- ---------- ---------- ---------- ---------- ----------\n"
        )
        for conduit in conduits:
            stream.write(f"{conduit.as_inp}\n")


@dataclass
class Pump(Link):
    """Identifies each pump link of the drainage system.

    Attributes
    ----------
    name : str
        Name assigned to pump link.
    from_node : Node
        Pump's inlet node.
    to_node : Node
        Pump's outlet node.
    pcurve : Curve
        Curve object containing the pump's head versus flow curve.
    status : Literal["ON", "OFF"] = "ON"
        Pump's status at the start of the simulation (either ON or OFF;
        default is ON).
    startup_depth : float = 0
        Depth at the inlet node when the pump turns on (ft or m).
    shutdown_depth : float = 0
        Depth at inlet node when the pump shuts off (ft or m) (default is 0).
    """

    pcurve: Curve
    status: Literal["ON", "OFF"] = "ON"
    startup_depth: float = 0
    shutdown_depth: float = 0

    def __post_init__(self):
        if not isinstance(self.pcurve, Curve):
            raise ValueError("pcurve must be a Curve object")


class Orifice(Link):
    """Identifies each orifice link of the drainage system. An orifice link
    serves to limit the flow exiting a node and is often used to model flow
    diversions and storage node outlets.

    The geometry of an orifice's opening must be described in the XSECTIONS
    section. The only allowable shapes are CIRCULAR and RECT_CLOSED
    (closed rectangular).

    Attributes
    ----------
    name : str
        Name assigned to orifice link.
    from_node : Node
        Orifice's inlet node.
    to_node : Node
        Orifice's outlet node.
    orifice_type : Literal["SIDE", "BOTTOM"]
        Type of orifice - either SIDE if oriented in a vertical plane or
        BOTTOM if oriented in a horizontal plane.
    offset : float
        Amount that a Side Orifice's bottom or the position of a Bottom
        Orifice is offset above the invert of inlet node (ft or m, expressed
        as either a depth or as an elevation, depending on the LINK_OFFSETS
        option setting)
    cd: float
        Discharge coefficient (unitless).
    flap_gate : Literal["NO", "YES"] = "NO"
        YES if a flap gate is present that prevents reverse flow. The default
        is NO.
    orate : float = 0
        time in decimal hours to open a fully closed orifice (or close a
        fully open one). Use 0 if the orifice can open/close instantaneously.
    """

    orifice_type: Literal["SIDE", "BOTTOM"]
    offset: float
    cd: float
    flap_gate: Literal["NO", "YES"] = "NO"
    orate: float = 0

    def __post_init__(self):
        raise NotImplementedError("Orifice is not yet implemented")


@dataclass
class Weir(Link):
    """Identifies each weir link of the drainage system. Weirs are used to
    model flow diversions and storage node outlets.

    Attributes
    ----------
    name : str
        Name assigned to weir link.
    from_node : Node
        Weir's inlet node.
    to_node : Node
        Weir's outlet node.
    weir_type: Literal["TRANSVERSE", "SIDEFLOW", "V-NOTCH", "TRAPEZOIDAL", "ROADWAY"]
        Type of weir.
    crest_height: float
        Amount that the weir's opening is offset above the invert of inlet
        node (ft or m, expressed as either a depth or as an elevation, depending
        on the LINK_OFFSETS option setting).
    cd: float
        Weir discharge coefficient (for CFS if using US flow units or CMS if
        using metric flow units).
    flap_gate : Literal["NO", "YES"] = "NO"
        YES if a flap gate is present that prevents reverse flow. The default
        is NO.
    end_contractions: int = 0
        Number of end contractions for a TRANSVERSE or TRAPEZOIDAL weir
        (default is 0).
    cd2: Optional[float] = None
        Discharge coefficient for the triangular ends of a TRAPEZOIDAL weir
        (for CFS if using US flow units or CMS if using metric flow units)
        (default is None to take on the value of cd).
    surcharge: Literal["NO", "YES"] = "YES"
        YES if the weir can surcharge (have an upstream water level higher
        than the height of the weir's opening); NO if it cannot (default is YES).
    road_width: Optional[float] = None
        Width of road lanes and shoulders for a ROADWAY weir (ft or m).
    road_surface: Optional[Literal["PAVED", "GRAVEL"]] = None
        Type of road surface for a ROADWAY weir.

    Notes
    -----
    - The geometry of a weir's opening is described in the [XSECTIONS] section.
    The following shapes must be used with each type of weir:

        - TRANSVERSE: RECT_OPEN
        - SIDEFLOW: RECT_OPEN
        - V-NOTCH: TRIANGULAR
        - TRAPEZOIDAL: TRAPEZOIDAL
        - ROADWAY: RECT_OPEN

    - The ROADWAY weir is a broad crested rectangular weir used to model roadway
    crossings usually in conjunction with culvert-type conduits. It uses the
    FHWA HDS-5 method to determine a discharge coefficient as a function of flow
    depth, roadway width and surface. If no roadway data are provided then
    the weir behaves as a TRANSVERSE weir with Cd as its discharge coefficient.
    """

    weir_type: Literal["TRANSVERSE", "SIDEFLOW", "V-NOTCH", "TRAPEZOIDAL", "ROADWAY"]
    crest_height: float
    cd: float
    flap_gate: Literal["NO", "YES"] = "NO"
    end_contractions: int = 0
    cd2: Optional[float] = None
    surcharge: Literal["NO", "YES"] = "YES"
    road_width: Optional[float] = None
    road_surface: Optional[Literal["PAVED", "GRAVEL"]] = None

    def __post_init__(self):
        if self.weir_type not in [
            "TRANSVERSE",
            "SIDEFLOW",
            "V-NOTCH",
            "TRAPEZOIDAL",
            "ROADWAY",
        ]:
            raise ValueError(
                "weir_type must be one of TRANSVERSE, SIDEFLOW, V-NOTCH, TRAPEZOIDAL, or ROADWAY"
            )

        if self.cd2 is None:
            self.cd2 = self.cd

        if self.weir_type == "ROADWAY":
            # Override default unused values if ROADWAY
            self.flap_gate = "NO"
            self.end_contractions = 0
            self.cd2 = 0
            self.surcharge = "NO"

            if not self.road_width or not self.road_surface:
                raise ValueError(
                    "Both road_width and road_surface must be specified if "
                    "weir_type is ROADWAY"
                )

            if self.road_surface not in ["PAVED", "GRAVEL"]:
                raise ValueError(
                    "road_surface must be one of PAVED or GRAVEL if weir_type is ROADWAY"
                )


@dataclass
class Outlet(Link):
    """Identifies each outlet flow control device of the drainage system.
    These are devices used to model outflows from storage units or flow
    diversions that have a user-defined relation between flow rate and
    water depth.

    Attributes
    ----------
    name : str
        Name assigned to outlet link.
    from_node : Node
        Outlet's inlet node.
    to_node : Node
        Outlet's outlet node.
    offset : float
        amount that the outlet is offset above the invert of its inlet node
        (ft or m, expressed as either a depth or as an elevation, depending
        on the LINK_OFFSETS option setting)
    outlet_type : Literal["TABULAR/DEPTH", "TABULAR/HEAD", "FUNCTIONAL/DEPTH",
        "FUNCTIONAL/HEAD"]
        Type of outlet.
    qcurve : Optional[Curve] = None
        Rating curve listed in the [CURVES] section that describes outflow
        rate (flow units) as a function of:
        - Water depth above the offset elevation at the inlet node (ft or m)
        for a TABULAR/DEPTH outlet
        - head difference (ft or m) between the inlet and outflow nodes for a
        TABULAR/HEAD outlet.
    coeffs: Optional[Tuple[float, float]] = None
        Coefficient and exponent pair for FUNCTIONAL outlet, expressed as a
        power function that relates outflow (Q) to water depth or head
        difference (H) as Q = coeffs[0] * H**coeffs[1].
    flap_gate : Literal["NO", "YES"] = "NO"
        YES if a flap gate is present that prevents reverse flow. The default
    """

    offset: float
    outlet_type: Literal[
        "TABULAR/DEPTH", "TABULAR/HEAD", "FUNCTIONAL/DEPTH", "FUNCTIONAL/HEAD"
    ]
    qcurve: Optional[Curve] = None
    coeffs: Optional[tuple[float, float]] = None
    flap_gate: Literal["NO", "YES"] = "NO"

    def __post_init__(self):
        if self.outlet_type not in [
            "TABULAR/DEPTH",
            "TABULAR/HEAD",
            "FUNCTIONAL/DEPTH",
            "FUNCTIONAL/HEAD",
        ]:
            raise ValueError(
                "outlet_type must be one of TABULAR/DEPTH, TABULAR/HEAD, FUNCTIONAL/DEPTH, or FUNCTIONAL/HEAD"
            )

        if "FUNCTIONAL" in self.outlet_type and self.coeffs is None:
            raise ValueError("coeffs must be specified if outlet_type is FUNCTIONAL/*")

        elif "TABULAR" in self.outlet_type and self.qcurve is None:
            raise ValueError("qcurve must be specified if outlet_type is TABULAR/*")
