import typing
from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self, Literal

from .base_topology import Node, Area, Link
from .tabular import Curve, Timeseries

from .type_helpers import OutfallTypeType


@dataclass
class Junction(Node):
    """Identifies each junction node of the drainage system. Junctions are
    points in space where channels and pipes connect together. For sewer
    systems they can be either connection points in space where fittings or
    manholes.

    Attributes
    ----------
    name : str
        Name assigned to the junction.
    elevation : float
        Elevation of the junction's invert (ft or m).
    max_depth : float = 0
        Depth from ground to invert elevation (ft or m) (default is 0).
    init_depth : float = 0
        Water depth at the start of the simulation (ft or m) (default is 0).
    sur_depth : float = 0
        Maximum additional pressure head above the ground elevation that the
        junction can sustain under surcharge conditions (ft or m)
        (default is 0).
    aponded : float = 0
        Area subjected to surface ponding once water depth exceeds
        max_depth + sur_depth (ft² or m²) (default is 0).
    xcoord : Optional[float] = None
        X-coordinate of the junction (ft or m).
    ycoord : Optional[float] = None
        Y-coordinate of the junction (ft or m).

    Remarks
    -------
    - If max_depth is 0 then SWMM sets the junction’s maximum depth to the
    distance from its invert to the top of the highest connecting link.

    - If the junction is part of a force main section of the system then set
    sur_depth to the maximum pressure that the system can sustain.

    - Surface ponding can only occur when apond is non-zero and the
    ALLOW_PONDING analysis option is turned on.

    - xcoord and ycoord are additional optional attributes.
    """

    name: str
    elevation: float
    max_depth: float = 0
    init_depth: float = 0
    sur_depth: float = 0
    aponded: float = 0
    xcoord: Optional[float] = None
    ycoord: Optional[float] = None

    @property
    def as_inp(self):
        return f"{self.name: <16} {self.elevation: <10.3f} {self.max_depth: <10.2f} {self.init_depth: <10.2f} {self.sur_depth: <10.2f} {self.aponded: <11}"

    @classmethod
    def make_inp(cls, stream: TextIO, junctions: Iterable[Self]):
        stream.write(
            "[JUNCTIONS]\n"
            ";;Name           Elevation  MaxDepth   InitDepth  SurDepth   Aponded    \n"
            ";;-------------- ---------- ---------- ---------- ---------- ---------- \n"
        )

        for junction in junctions:
            stream.write(f"{junction.as_inp}\n")


@dataclass
class Outfall(Node):
    """Identifies each outfall node (i.e., final downstream boundary) of the drainage system and the
    corresponding water stage elevation. Only one link can be incident on an outfall node.

    Attributes
    ----------
    name : str
        Name assigned to outfall node.
    elevation : float
        Node's invert elevation (ft or m).
    type_of_outfall : OutfallTypeType = "FREE"
        FREE, NORMAL, FIXED, TIDAL, or TIMESERIES. The default is FREE.
        If type_of_outfall is set to TIDAL or TIMESERIES, a Curve or a Timeseries
        object must be specified to the stage_data parameter.
    stage_data : float | Curve | Timeseries, optional = None
        Elevation data for stage outfall. It can be either a
        - Elevation of a fixed stage outfall (ft or m), or
        - Curve object containing tidal height (i.e., outfall stage) versus hour
        of day over a complete tidal cycle.
        - Time series that describes how outfall stage varies with time.
    gated : Literal["YES", "NO"] = "NO
        YES or NO depending on whether a flap gate is present that prevents reverse
        flow. The default is NO.
    route_to : Optional[BaseSubcatchment], optional = None
        Name of a subcatchment that receives the outfall's discharge. The default
        is not to route the outfall's discharge.
    """

    name: str
    elevation: float
    type_of_outfall: OutfallTypeType = "FREE"
    stage_data: Optional[float | Curve | Timeseries] = None
    gated: Literal["YES", "NO"] = "NO"
    route_to: Optional[Area] = None

    def __post_init__(self):
        if self.type_of_outfall not in typing.get_args(OutfallTypeType):
            raise ValueError(
                "Type of outfall must be one of FREE, NORMAL, FIXED, TIDAL, TIMESERIES"
            )

        if self.type_of_outfall == "FIXED" and not isinstance(self.stage_data, float):
            raise ValueError("stage_data must be a float if type_of_outfall is FIXED")

        elif self.type_of_outfall == "TIDAL" and not isinstance(self.stage_data, Curve):
            raise ValueError(
                "stage_data must be a Curve object if type_of_outfall is TIDAL"
            )

        elif self.type_of_outfall == "TIMESERIES" and not isinstance(
            self.stage_data, Timeseries
        ):
            raise ValueError(
                "stage_data must be a Timeseries object if type_of_outfall is TIMESERIES"
            )

        elif self.type_of_outfall in ["FREE", "NORMAL"] and self.stage_data is not None:
            raise ValueError(
                "stage_data must be None if type_of_outfall is FREE or NORMAL"
            )

        if self.gated not in ["NO", "YES"]:
            raise ValueError("Gated must be one of NO, YES")

    @property
    def as_inp(self):
        if self.type_of_outfall in ["FREE", "NORMAL"]:
            str_stage_data = " " * 16
        else:
            if isinstance(self.stage_data, float):
                str_stage_data = f"{self.stage_data: <16.3f}"
            elif isinstance(self.stage_data, (Curve, Timeseries)):
                str_stage_data = f"{self.stage_data.name: <16}"

        if isinstance(self.route_to, Area):
            str_route_to = f"{self.route_to.name: <16}"
        else:
            str_route_to = ""

        return f"{self.name: <16} {self.elevation: <10.3f} {self.type_of_outfall: <10} {str_stage_data} {self.gated: <8} {str_route_to}"

    @classmethod
    def make_inp(cls, stream: TextIO, outfalls: Iterable[Self]):
        stream.write("[OUTFALLS]\n")
        stream.write(
            ";;Name           Elevation  Type       Stage Data       Gated    Route To        \n"
            ";;-------------- ---------- ---------- ---------------- -------- ----------------\n"
        )

        for outfall in outfalls:
            stream.write(f"{outfall.as_inp}\n")


@dataclass
class Divider(Node):
    """Identifies each flow divider node of the drainage system. Flow dividers
    are junctions with exactly two outflow conduits where the total outflow is
    divided between the two in a prescribed manner.

    Divider nodes are only active under the Steady Flow or Kinematic Wave
    analysis options. For Dynamic Wave flow routing they behave the same as
    Junction nodes.

    Attributes
    ----------
    name : str
        Name assigned to the divider node.
    elevation : float
        Elevation of the divider node's invert (ft or m).
    divided_link; Link
        Link object to which flow is diverted.
    divider_type : Literal["OVERFLOW", "CUROFF", "TABULAR", "WEIR"]
        Type of divider. OVERFLOW, CUROFF, TABULAR, or WEIR.
    qmin: Optional[float] = None
        Flow at which diversion begins for either a CUTOFF or WEIR divider
        (flow units).
    dcurve: Optional[Curve] = None
        Curve for a TABULAR divider that relates diverted flow to total flow.
    ht: Optional[float] = None
        Height of a WEIR divider (ft or m).
    Cd: Optional[float] = None
        Discharge coefficient for a WEIR divider.
    max_depth: float = 0
        Fepth from the ground to the node's invert elevation (ft or m)
        (default is 0). If Ymax is 0 then SWMM sets the node's maximum depth
        equal to the distance from its invert to the top of the highest
        connecting link.
    init_depth: float = 0
        Water depth at the start of the simulation (ft or m) (default is 0).
    sur_depth: float = 0
        Maximum additional pressure head above the ground elevation that the
        junction can sustain under surcharge conditions (ft or m)
        (default is 0).
    aponded: float = 0
        Area subjected to surface ponding once water depth exceeds
        max_depth + sur_depth (ft² or m²) (default is 0). Surface ponding can
        only occur when Apond is non-zero and the ALLOW_PONDING analysis option
        is turned on.
    """

    name: str
    elevation: float
    divided_link: Link
    divider_type: Literal["OVERFLOW", "CUROFF", "TABULAR", "WEIR"]
    qmin: Optional[float] = None
    dcurve: Optional[Curve] = None
    ht: Optional[float] = None
    Cd: Optional[float] = None
    max_depth: float = 0
    init_depth: float = 0
    sur_depth: float = 0
    aponded: float = 0


class Storage(Node):
    def __init__(self):
        raise NotImplementedError("Storage is not yet implemented")
