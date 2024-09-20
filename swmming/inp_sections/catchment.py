import typing

from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self, Literal

from .meteo import Raingage
from .gw import Snowpack
from .tabular import Curve, Timeseries

from .type_helpers import InfiltrationMethodType, OutfallTypeType


@dataclass
class Junction:
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
class Subcatchment:
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

    name: str
    rain_gage: Raingage
    outlet: Junction
    area: float
    percent_imperv: float
    width: float
    slope: float
    curb_length: float = 0
    snow_pack: Optional[Snowpack] = None

    def __post_init__(self):
        if not isinstance(self.outlet, Junction):
            raise ValueError("Outlet must be a Junction object")

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


class LID_Control:
    def __init__(self):
        raise NotImplementedError("LID_Control is not yet implemented")


class LID_Use:
    def __init__(self):
        raise NotImplementedError("LID_Use is not yet implemented")


@dataclass
class Outfall:
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
    route_to : Optional[Subcatchment], optional = None
        Name of a subcatchment that receives the outfall's discharge. The default
        is not to route the outfall's discharge.
    """

    name: str
    elevation: float
    type_of_outfall: OutfallTypeType = "FREE"
    stage_data: Optional[float | Curve | Timeseries] = None
    gated: Literal["YES", "NO"] = "NO"
    route_to: Optional[Subcatchment] = None

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

        if isinstance(self.route_to, Subcatchment):
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


class Divider:
    def __init__(self):
        raise NotImplementedError("Divider is not yet implemented")


class Storage:
    def __init__(self):
        raise NotImplementedError("Storage is not yet implemented")
