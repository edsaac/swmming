import typing

from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self, Literal

from .base_topology import Node, Area
from .meteorology import Raingage
from .gw import Snowpack

from .type_helpers import InfiltrationMethodType


@dataclass
class Subcatchment(Area):
    """Identifies each subcatchment within the study area. Subcatchments are land area units which
    generate runoff from rainfall.

    Parameters
    ----------
    name : str
        Name assigned to the subcatchment.
    rain_gage : Raingage
        Name of the rain gage assigned to the subcatchment.
    outlet : Junction
        Name of the node or subcatchment receiving runoff.
    area : float
        Area of the subcatchment (acres or hectares).
    percent_imperv : float
        Percentage of the area that is impervious.
    width : float
        Characteristic width of the subcatchment (ft or meters).
    slope : float
        Slope of the subcatchment (percent).
    curb_length : float = 0
        Total curb length used for pollutant buildup (any units).
    snow_pack : Optional[Snowpack] = None
        Name of a snow pack object for snow accumulation.


    """

    rain_gage: Raingage
    outlet: Node | Self
    area: float
    percent_imperv: float
    width: float
    slope: float
    curb_length: float = 0
    snow_pack: Optional[Snowpack] = None

    def __post_init__(self):
        if not isinstance(self.outlet, (Node, Self)):
            raise ValueError("Outlet must be a Node object or another Subcatchment")

        if self.outlet is self:
            raise ValueError("Outlet cannot be itself")

        if not isinstance(self.rain_gage, Raingage):
            raise ValueError("Rain Gage must be a Raingage object")

        if self.snow_pack:
            raise NotImplementedError("Snowpack is not yet implemented")

        self.snow_pack = ""

    @property
    def as_inp(self):
        return f"{self.name: <16} {self.rain_gage.name: <16} {self.outlet.name: <16} {self.area: <8.2f} {self.percent_imperv: <8.2f} {self.width: <8.2f} {self.slope: <8.4f} {self.curb_length: <8.2f} {self.snow_pack: <16}"

    @classmethod
    def make_inp(cls, stream: TextIO, subcatchments: Iterable[Self]):
        stream.write("[SUBCATCHMENTS]\n")
        stream.write(
            ";;Name           Rain Gage        Outlet           Area     %Imperv  Width    %Slope   CurbLen  SnowPack        \n"
            ";;-------------- ---------------- ---------------- -------- -------- -------- -------- -------- ----------------\n"
        )
        for subcatchment in subcatchments:
            stream.write(f"{subcatchment.as_inp}\n")


@dataclass
class Subarea:
    """Supplies information about pervious and impervious areas for each subcatchment. Each
    subcatchment can consist of a pervious subarea, an impervious subarea with depression
    storage, and an impervious subarea without depression storage.

    Attributes
    ----------
    subcatchment : str
        Subcatchment name.
    nimp : float
        Manning's coefficient (n) for overland flow over the impervious subarea.
    nperv : float
        Manning's coefficient (n) for overland flow over the pervious subarea.
    simp : float
        Depression storage for the impervious subarea (inches or mm).
    sperv : float
        Depression storage for the pervious subarea (inches or mm).
    percent_zero : float
        Percent of impervious area with no depression storage.
    route_to : str = "OUTLET"
        IMPERVIOUS if pervious area runoff runs onto impervious area, PERVIOUS if
        impervious runoff runs onto pervious area, or OUTLET if both areas drain to
        the subcatchment's outlet. Default is OUTLET.
    percent_routed : float = 100
        Percent of runoff routed from one type of area to another. Default is 100.
    """

    subcatchment: Subcatchment
    nimp: float
    nperv: float
    simp: float
    sperv: float
    percent_zero: float
    route_to: Literal["OUTLET", "IMPERVIOUS", "PERVIOUS"] = "OUTLET"
    pctrouted: float = 100

    def __post_init__(self):
        if self.route_to not in ["OUTLET", "IMPERVIOUS", "PERVIOUS"]:
            raise ValueError("Route to must be either OUTLET or OUTFALL")

    @property
    def as_inp(self):
        return f"{self.subcatchment.name: <16} {self.nimp: <10.4f} {self.nperv: <10.4f} {self.simp: <10.4f} {self.sperv: <10.4f} {self.percent_zero: <10.2f} {self.route_to: <10} {self.pctrouted: <10.2f}"

    @classmethod
    def make_inp(cls, stream: TextIO, subareas: Iterable[Self]):
        stream.write("[SUBAREAS]\n")
        stream.write(
            ";;Subcatchment   N-Imperv   N-Perv     S-Imperv   S-Perv     PctZero    RouteTo    PctRouted \n"
            ";;-------------- ---------- ---------- ---------- ---------- ---------- ---------- ----------\n"
        )
        for subarea in subareas:
            stream.write(f"{subarea.as_inp}\n")


@dataclass
class Infiltration:
    """Supplies infiltration parameters for each subcatchment. Rainfall lost
    to infiltration only occurs over the pervious subarea of a subcatchment.

    Attributes
    ----------
    subcatchment : Subcatchment
        Subcatchment object.
    method : InfiltrationMethodType | Literal[""] = ""
        Infiltration method, either HORTON, MODIFIED_HORTON, GREEN_AMPT,
        MODIFIED_GREEN_AMPT, or CURVE_NUMBER. If not specified, the
        infiltration method supplied in the [OPTIONS] section is used.
    parameters : Iterable[float]
        Parameters for the infiltration method. The number of parameters
        depends on the method.

    Notes
    -------
    For Horton and Modified Horton Infiltration:
    - p1: maximum infiltration rate on the Horton curve (in/hr or mm/hr).
    - p2: minimum infiltration rate on the Horton curve (in/hr or mm/hr).
    - p3 decay rate constant of the Horton curve (1/hr).
    - p4: time it takes for a fully saturated soil to dry (days).
    - p5: maximum infiltration volume possible (0 if not applicable) (in or mm).

    For Green-Ampt and Modified Green-Ampt Infiltration:
    - p1: soil capillary suction (in or mm).
    - p2: soil saturated hydraulic conductivity (in/hr or mm/hr).
    - p3: initial soil moisture deficit (porosity minus moisture content) (fraction).

    For Curve-Number Infiltration:
    - p1: SCS Curve Number.
    - p2: no longer used.
    - p3: time it takes for a fully saturated soil to dry (days).
    """

    subcatchment: Subcatchment
    parameters: Iterable[float]
    method: InfiltrationMethodType | Literal[""] = ""

    def __post_init__(self):
        if self.method not in typing.get_args(InfiltrationMethodType):
            raise ValueError(
                "Method must be one of HORTON, MODIFIED_HORTON, GREEN_AMPT, MODIFIED_GREEN_AMPT, CURVE_NUMBER\n"
                "If not specified then the infiltration method supplied in the [OPTIONS] section is used."
            )

        elif "HORTON" in self.method:
            if len(self.parameters) != 5:
                raise ValueError(f"{self.method} requires 5 parameters.")

        elif "GREEN_AMPT" in self.method:
            if len(self.parameters) != 3:
                raise ValueError(f"{self.method} requires 3 parameters.")

        elif "CURVE_NUMBER" in self.method:
            if len(self.parameters) != 3:
                raise ValueError(
                    f"{self.method} requires 3 parameters. "
                    "The second parameter is not used though, so it can be any value"
                )

    @property
    def as_inp(self):
        params_str = " ".join(f"{p: <10.2f}" for p in self.parameters)
        return f"{self.subcatchment.name: <16} {params_str: <54} {self.method}"

    @classmethod
    def make_inp(cls, stream: TextIO, infiltrations: Iterable[Self]):
        stream.write("[INFILTRATION]\n")
        stream.write(
            ";;Subcatchment   Param1     Param2     Param3     Param4     Param5    \n"
            ";;-------------- ---------- ---------- ---------- ---------- ----------\n"
        )
        for infiltration in infiltrations:
            stream.write(f"{infiltration.as_inp}\n")
