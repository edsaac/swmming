import typing
import warnings  # noqa

from typing import Self, Iterable, TextIO, Literal, Optional
from dataclasses import dataclass
from datetime import date, time, timedelta
from itertools import batched
from io import StringIO
from textwrap import wrap

from . import xsection_shapes as xshapes


@dataclass
class Title:
    header: str = "Project Title"
    description: str = "Project Description"

    def make_inp(self, stream):
        stream.write("[TITLE]\n;;Project Title/Notes\n")
        stream.write(self.header + "\n")
        stream.write(self.description)


FlowUnitsType = Literal[
    "CFS",
    "GPM",
    "MGD",
    "CMS",
    "LPS",
    "MLD",
]

InfiltrationMethodType = Literal[
    "HORTON",
    "MODIFIED_HORTON",
    "GREEN_AMPT",
    "MODIFIED_GREEN_AMPT",
    "CURVE_NUMBER",
]

RoutingMethodType = Literal[
    "STEADY",
    "KINWAVE",
    "DYNWAVE",
]


@dataclass
class Options:
    """
    Provides values for various analysis options.

    Attributes
    ----------
    flow_units : FlowUnitsType = "CFS"
        Makes a choice of flow units. Selecting a US flow unit means that all other
        quantities will be expressed in US customary units, while choosing a metric
        flow unit will force all quantities to be expressed in SI metric units.
        Exceptions are pollutant concentration and Manning's roughness coefficient (n)
        which are always in metric units. Default is CFS.
    infiltration : InfiltrationMethodType = "HORTON"
        Selects a model for computing infiltration of rainfall into the upper soil zone
        of subcatchments. Default model is HORTON.
    flow_routing : RoutingMethodType = "DYNWAVE"
        Determines which method is used to route flows through the drainage system.
        STEADY refers to sequential steady state routing (i.e., hydrograph translation),
        KINWAVE to kinematic wave routing, DYNWAVE to dynamic wave routing. Default is
        DYNWAVE.
    link_offsets : Literal["DEPTH", "ELEVATION"] = "DEPTH"
        Determines the convention used to specify the position of a link offset above the
        invert of its connecting node. DEPTH indicates that offsets are expressed as the
        distance between the node invert and the link while ELEVATION indicates that the
        absolute elevation of the offset is used. Default is DEPTH.
    force_main_equation : Literal["H-W", "D-W"] = "H-W"
        Establishes whether the Hazen-Williams (H-W) or the Darcy-Weisbach (D-W) equation
        will be used to compute friction losses for pressurized flow in conduits assigned a
        Circular Force Main cross-section shape. Default is H-W.
    ignore_rainfall : Literal["YES", "NO"] = "NO"
        Set to YES if all rainfall data and runoff calculations should be ignored. SWMM
        will only perform flow and pollutant routing based on user-supplied direct and dry
        weather inflows. Default is NO.
    ignore_snowmelt : Literal["YES", "NO"] = "NO"
        Set to YES if snowmelt calculations should be ignored when a project file contains
        snow pack objects. Default is NO.
    ignore_groundwater : Literal["YES", "NO"] = "NO"
        Set to YES if groundwater calculations should be ignored when a project file contains
        aquifer objects. Default is NO.
    ignore_rdii : Literal["YES", "NO"] = "NO"
        Set to YES if rainfall-dependent infiltration and inflow should be ignored when RDII
        unit hydrographs and RDII inflows have been supplied to a project file. Default is NO.
    ignore_routing : Literal["YES", "NO"] = "NO"
        Set to YES if only runoff should be computed even if the project contains drainage
        system links and nodes. Default is NO.
    ignore_quality : Literal["YES", "NO"] = "NO"
        Set to YES if pollutant washoff, routing, and treatment should be ignored in a project
        that has pollutants defined. Default is NO.
    allow_ponding : Literal["YES", "NO"] = "NO"
        Determines whether excess water is allowed to collect atop nodes and be re-introduced
        into the system as conditions permit. Default is NO ponding. Ponding will occur at
        a node only if a non-zero value for its Ponded Area attribute is used.
    skip_steady_state : Literal["YES", "NO"] = "NO"
        Set to YES if flow routing computations should be skipped during steady state periods
        of a simulation during which the last set of computed flows will be used. A time step
        is considered to be in steady state if the percent difference between total system
        inflow and total system outflow is below SYS_FLOW_TOL and the percent difference
        between current and previous lateral inflows are below LAT_FLOW_TOL. Default is NO.
    sys_flow_tol : int = 5
        Maximum percent difference between total system inflow and total system outflow which
        can occur for the SKIP_STEADY_STATE option to take effect. Default is 5 percent.
    lat_flow_tol : int = 5
        Maximum percent difference between the current and previous lateral inflow at all nodes
        in the conveyance system for the SKIP_STEADY_STATE option to take effect. Default is
        5 percent.
    start_date : date | str = "1/1/2004"
        The date when the simulation begins. If not supplied, a date of 1/1/2004 is used.
    start_time : time | str = "0:00:00"
        The time of day on the starting date when the simulation begins. Default is 12 midnight (0:00:00).
    end_date : date | str = "1/1/2004"
        The date when the simulation is to end. Default is the start date.
    end_time : time | str = "24:00:00"
        The time of day on the ending date when the simulation will end. Default is 24:00:00.
    report_start_date : date | str = "1/1/2004"
        The date when reporting of results is to begin. Default is the simulation start date.
    report_start_time : time | str = "0:00:00"
        The time of day on the report starting date when reporting is to begin. Default is the simulation start time of day.
    sweep_start : str = "1/1"
        The day of the year (month/day) when street sweeping operations begin. Default is 1/1.
    sweep_end : str = "12/31"
        The day of the year (month/day) when street sweeping operations end. Default is 12/31.
    dry_days : int = 0
        The number of days with no rainfall prior to the start of the simulation. Default is 0.
    report_step : timedelta | str = "0:15:00"
        The time interval for reporting of computed results. Default is 0:15:00.
    wet_step : timedelta | str = "0:05:00"
        The time step length used to compute runoff from subcatchments during periods of rainfall
        or when ponded water still remains on the surface. Default is 0:05:00.
    dry_step : timedelta | str = "1:00:00"
        The time step length used for runoff computations (consisting essentially of pollutant
        buildup) during periods when there is no rainfall and no ponded water. Default is 1:00:00.
    routing_step : float = 20.0
        The time step length in seconds used for routing flows and water quality constituents through
        the conveyance system. Default is 20 sec. This can be increased if dynamic wave routing is
        not used. Fractional values (e.g., 2.5) are permissible as are values entered in hours:minutes:seconds format.
    lengthening_step : float = 0.0
        A time step, in seconds, used to lengthen conduits under dynamic wave routing, so that they
        meet the Courant stability criterion under full-flow conditions. A value of 0 (the default) means
        that no conduits will be lengthened.
    variable_step : float = 0.0
        A safety factor applied to a variable time step computed for each time period under dynamic
        wave flow routing. The variable time step is computed to satisfy the Courant stability criterion
        for each conduit and yet not exceed the ROUTING_STEP value. If the safety factor is 0 (the default),
        no variable time step is used.
    minimum_step : float = 0.5
        The smallest time step allowed when variable time steps are used for dynamic wave flow routing.
        Default value is 0.5 seconds.
    inertial_damping : Literal["NONE", "PARTIAL", "FULL"] = "PARTIAL"
        Indicates how the inertial terms in the Saint Venant momentum equation will be handled under
        dynamic wave flow routing. NONE maintains these terms at their full value under all conditions.
        PARTIAL (the default) reduces the terms as flow comes closer to being critical (and ignores them
        when flow is supercritical). FULL drops the terms altogether.
    normal_flow_limited : Literal["SLOPE", "FROUDE", "BOTH"] = "BOTH"
        Specifies which condition is checked to determine if flow in a conduit is supercritical and
        should be limited to normal flow. Use SLOPE to check if the water surface slope is greater than
        the conduit slope, FROUDE to check if the Froude number is greater than 1.0, or BOTH to check
        both conditions. Default is BOTH.
    surcharge_method : Literal["EXTRAN", "SLOT"] = "EXTRAN"
        Selects which method will be used to handle surcharge conditions. EXTRAN uses a variation of
        the Surcharge Algorithm from previous versions of SWMM to update nodal heads when all connecting
        links become full. SLOT uses a Preissmann Slot to add a small amount of virtual top surface width
        to full flowing pipes so that SWMM's normal procedure for updating nodal heads can continue to be used.
        Default is EXTRAN.
    min_surfarea : float = 0
        Minimum surface area used at nodes when computing changes in water depth under dynamic wave routing.
        If 0 is entered, the default value of 12.566 ft² (1.167 m²) is used (i.e., the area of a 4-ft diameter manhole).
    min_slope : float = 0
        The minimum value allowed for a conduit's slope (%). If zero (the default) then no minimum is imposed
        (although SWMM uses a lower limit on elevation drop of 0.001 ft (0.00035 m) when computing a conduit slope).
    max_trials : int = 8
        The maximum number of trials allowed during a time step to reach convergence when updating hydraulic
        heads at the conveyance system's nodes. Default value is 8.
    head_tolerance : float = 0.005
        The difference in computed head at each node between successive trials below which the flow solution
        for the current time step is assumed to have converged. Default tolerance is 0.005 ft (0.0015 m).
    threads : int = 1
        The number of parallel computing threads to use for dynamic wave flow routing on machines equipped
        with multi-core processors. Default is 1.

    """

    flow_units: FlowUnitsType = "CFS"
    infiltration: InfiltrationMethodType = "HORTON"
    flow_routing: RoutingMethodType = "DYNWAVE"
    link_offsets: Literal["DEPTH", "ELEVATION"] = "DEPTH"
    force_main_equation: Literal["H-W", "D-W"] = "H-W"
    ignore_rainfall: Literal["YES", "NO"] = "NO"
    ignore_snowmelt: Literal["YES", "NO"] = "NO"
    ignore_groundwater: Literal["YES", "NO"] = "NO"
    ignore_rdii: Literal["YES", "NO"] = "NO"
    ignore_routing: Literal["YES", "NO"] = "NO"
    ignore_quality: Literal["YES", "NO"] = "NO"
    allow_ponding: Literal["YES", "NO"] = "NO"
    skip_steady_state: Literal["YES", "NO"] = "NO"
    sys_flow_tol: int = 5
    lat_flow_tol: int = 5
    start_date: date | str = "1/1/2004"
    start_time: time | str = "0:00:00"
    end_date: date | str = "1/1/2004"
    end_time: time | str = "23:59:59"
    report_start_date: date | str = "1/1/2004"
    report_start_time: time | str = "0:00:00"
    sweep_start: str = "1/1"
    sweep_end: str = "12/31"
    dry_days: int = 0
    report_step: timedelta | str = "0:15:00"
    wet_step: timedelta | str = "0:05:00"
    dry_step: timedelta | str = "1:00:00"
    routing_step: float = 20.0
    lengthening_step: float = 0.0
    variable_step: float = 0.0
    minimum_step: float = 0.5
    inertial_damping: Literal["NONE", "PARTIAL", "FULL"] = "PARTIAL"
    normal_flow_limited: Literal["SLOPE", "FROUDE", "BOTH"] = "BOTH"
    surcharge_method: Literal["EXTRAN", "SLOT"] = "EXTRAN"
    min_surfarea: float = 0
    min_slope: float = 0
    max_trials: int = 8
    head_tolerance: float = 0.005
    threads: int = 8

    def make_inp(self, stream):
        stream.write("[OPTIONS]\n" ";;Option             Value\n")

        for key, value in self.__dict__.items():
            stream.write(f"{key.upper(): <20} {value}\n")


class Snowpack:
    def __init__(self):
        raise NotImplementedError("Snowpack is not yet implemented")


@dataclass
class Curve:
    def __init__(self):
        raise NotImplementedError("Curve is not yet implemented")


@dataclass
class Timeseries:
    """Describes how a quantity varies over time.

    Attributes
    ----------
    name : str
        Name assigned to the time series.
    date_ts : str
        Date in Month/Day/Year format (e.g., June 15, 2001 would be 6/15/2001).
    hour_ts : str
        24-hour military time (e.g., 8:40 pm would be 20:40) relative to the last date specified (or to midnight of the starting date of the simulation if no previous date was specified).
    time_ts : Iterable[float]
        Hours since the start of the simulation, expressed as a decimal number or as hours:minutes (where hours can be greater than 24).
    value_ts : Iterable[float]
        A value corresponding to the specified date and time.
    fname : str
        The name of a file in which the time series data are stored.
    """

    name: str
    time_ts: Iterable[float]
    value_ts: Iterable[float]
    date_ts: str = ""
    hour_ts: str = ""
    fname: str = ""
    description: str = ""

    def __post_init__(self):
        if len(self.time_ts) != len(self.value_ts):
            raise ValueError("time and value must be the same length")

    @classmethod
    def make_inp(self, stream, timeseries: Iterable[Self]):
        stream.write(
            "[TIMESERIES]\n"
            ";;Name           Date       Time       Value     \n"
            ";;-------------- ---------- ---------- ----------\n"
        )
        for ts in timeseries:
            _date = ts.date_ts

            if not ts.description:
                stream.write(str.ljust(";", 49) + "\n")
            else:
                for chunk in wrap(ts.description, 48):
                    stream.write(f"; {chunk: <47}\n")

            for t, v in zip(ts.time_ts, ts.value_ts):
                stream.write(f"{ts.name: <16} {_date: <10} {t: <10.2f} {v: <10.3f}\n")
                _date = ""


@dataclass
class Raingage:
    """Identifies each rain gage that provides rainfall data for the study area.

    Attributes
    ----------
    name : str
        Name assigned to the rain gage.
    form : Literal["INTENSITY", "VOLUME", "CUMULATIVE"]
        Form of recorded rainfall, either 'INTENSITY', 'VOLUME', or 'CUMULATIVE'.
    interval : str | float
        Time interval between gage readings in decimal hours or hours:minutes format (e.g., 0:15 for 15-minute readings).
    tseries : Timeseries
        Timeseries object with rainfall data.
    scf : float = 1.0
        Snow catch deficiency correction factor (use 1.0 for no adjustment).
    fname : str = ""
        Name of an external file with rainfall data.
    sta : str = ""
        Name of the recording station in a user-prepared formatted rain file.
    units : str = "IN"
        Rain depth units for the data in a user-prepared formatted rain file, either 'IN' (inches) or 'MM' (millimeters).

    Notes
    -------
    Enclose the external file name in double quotes if it contains spaces and include its full path if it resides in a different directory than the SWMM input file.
    The station name and depth units entries are only required when using a user-prepared formatted rainfall file.
    """

    name: str
    form: Literal["INTENSITY", "VOLUME", "CUMULATIVE"]
    interval: str | float
    scf: float = 1.0
    tseries: Optional[Timeseries] = None
    fname: Optional[str] = None
    sta: Optional[str] = None
    units: Optional[Literal["IN", "MM"]] = None

    def __post_init__(self):
        if self.form not in ["INTENSITY", "VOLUME", "CUMULATIVE"]:
            raise ValueError("Form must be one of INTENSITY, VOLUME, or CUMULATIVE")

        if self.tseries is None and self.fname is None:
            raise ValueError("Either a tseries or fname must be specified")

        elif self.tseries is not None and self.fname is not None:
            raise ValueError("Only one of tseries or fname can be specified")

        elif isinstance(self.tseries, Timeseries):
            self._mode = "TIMESERIES"

        elif isinstance(self.fname, str):
            self._mode = "FILE"

            if self.sta is None:
                raise ValueError("sta must be specified if fname is specified")

            if self.units not in ["IN", "MM"]:
                raise ValueError("Units must be one of IN or MM")

    @property
    def as_inp(self):
        if self._mode == "TIMESERIES":
            return f"{self.name: <16} {self.form: <9} {self.interval: <9} {self.scf: <6.2f} {self._mode} {self.tseries.name} "

        elif self._mode == "FILE":
            return f"{self.name: <16} {self.form: <9} {self.interval: <9} {self.scf: <6.2f} {self._mode} {self.fname} {self.sta: <10} {self.units: <10}"

    @classmethod
    def make_inp(cls, stream: TextIO, raingages: Iterable[Self]):
        stream.write(
            "[RAINGAGES]\n"
            ";;Name           Format    Interval  SCF    Source    \n"
            ";;-------------- --------- --------- ------ ----------\n"
        )

        for rg in raingages:
            stream.write(f"{rg.as_inp}\n")


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
        Elevation of the junction’s invert (ft or m).
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


OutfallTypeType = Literal["FREE", "NORMAL", "FIXED", "TIDAL", "TIMESERIES"]


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


@dataclass
class Conduit:
    """Identifies each conduit link of the drainage system.
    Conduits are pipes or channels that convey water from one node to another

    Attributes
    ----------
    name : str
        Name assigned to conduit link.
    from_node : Junction | Outfall
        Name of the conduit's upstream node.
    to_node : Junction | Outfall
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

    name: str
    from_node: Junction | Outfall
    to_node: Junction | Outfall
    length: float
    roughness: float
    in_offset: float = 0
    out_offset: float = 0
    init_flow: float = 0
    max_flow: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.from_node, (Junction, Outfall)):
            raise ValueError("from_node must be a Junction or Outfall object")

        if not isinstance(self.to_node, (Junction, Outfall)):
            raise ValueError("to_node must be a Junction or Outfall object")

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
class Street:
    """Describes the cross-section geometry of conduits that represent streets.
    If the street has no depressed gutter (a = 0) then the gutter width entry is ignored.
    If the street has no backing then the three backing parameters can be omitted.

    Attributes
    ----------
    name : str
        Name assigned to the street cross-section.
    Tcrown : float
        Distance from the street's curb to its crown (ft or m).
    Hcurb : float
        Curb height (ft or m).
    Sx : float
        Street cross slope (%).
    nRoad : float
        Manning's roughness coefficient (n) of the road surface.
    a : float = 0
        Gutter depression height (in or mm). Default is 0.
    W : float = 0
        Depressed gutter width (ft or m). Default is 0.
    Sides : int = 1
        1 for single-sided street or 2 for two-sided street. Default is 2.
    Tback : float = 0
        Street backing width (ft or m). Default is 0.
    Sback : float = 0
        Street backing slope (%). Default is 0.
    nBack : float = 0
        Street backing Manning's roughness coefficient (n). Default is 0.
    """

    name: str
    Tcrown: float
    Hcurb: float
    Sx: float
    nRoad: float
    a: float = 0
    W: float = 0
    Sides: int = 1
    Tback: float = 0
    Sback: float = 0
    nBack: float = 0

    @property
    def as_inp(self):
        return f"{self.name: <16} {self.Tcrown: <8.2f} {self.Hcurb: <8.2f} {self.Sx: <8.4f} {self.nRoad: <8.4f} {self.a: <8.2f} {self.W: <8.2f} {self.Sides: <8} {self.Tback: <8.2f} {self.Sback: <8.4f} {self.nBack: <8.4f}"

    @classmethod
    def make_inp(cls, stream: TextIO, streets: Iterable[Self]):
        stream.write("[STREETS]\n")
        stream.write(
            ";;Name           Tcrown   Hcurb    Sx       nRoad    a        W        Sides    Tback    Sback    nBack   \n"
            ";;-------------- -------- -------- -------- -------- -------- -------- -------- -------- -------- --------\n"
        )
        for street in streets:
            stream.write(f"{street.as_inp}\n")


@dataclass
class Transect:
    """Describes the cross-section geometry of natural channels or conduits with
    irregular shapes following the HEC-2 data format.

    Attributes
    ----------
    name : str
        Name assigned to the transect.
    station : Iterable[float]
        Distance of a cross-section station from some fixed reference (ft or m).
    elevation : Iterable[float]
        Elevation of the channel bottom at a cross-section station relative to some
        fixed reference (ft or m).
    nleft : float
        Manning's roughness coefficient (n) of the left overbank portion of the
        channel (use 0 if no change from previous NC line).
    nright : float
        Manning's roughness coefficient (n) of the right overbank portion of the
        channel (use 0 if no change from previous NC line).
    nchannel : float
        Manning's roughness coefficient (n) of the main channel portion of the
        channel (use 0 if no change from previous NC line).
    xleft : float
        Station position which ends the left overbank portion of the channel (ft
        or m).
    xright : float
        Station position which begins the right overbank portion of the channel
        (ft or m).
    meander_modifier : float = 0
        Meander modifier that represents the ratio of the length of a meandering
        main channel to the length of the overbank area that surrounds it
        (use 0 if not applicable).
    station_modifier : float = 0
        Factor by which distances between stations should be multiplied to
        increase (or decrease) the width of the channel (enter 0 if not applicable).
    elev_offset : float = 0
        Amount to be added (or subtracted) from the elevation of each station
        (ft or m).
    """

    name: str
    station: Iterable[float]
    elevation: Iterable[float]
    nleft: float
    nright: float
    nchannel: float
    xleft: float
    xright: float
    meander_modifier: float = 0
    station_modifier: float = 0
    elev_offset: float = 0

    def __post_init__(self):
        if len(self.elevation) != len(self.station):
            raise ValueError("elevation and station must be the same length")

        if self.xleft not in self.station:
            raise ValueError("xleft must be in station")

        if self.xright not in self.station:
            raise ValueError("xright must be in station")

        self.n_stations = len(self.elevation)

    @classmethod
    def make_inp(cls, stream: TextIO, transects: Iterable[Self]):
        stream.write("[TRANSECTS]\n;;Transect Data in HEC-2 format\n")

        for tr in transects:
            stream.write(
                ";\n"
                f"NC {tr.nleft: <11.4f} {tr.nright: <10.4f} {tr.nchannel: <10.4f}\n"
                f"X1 {tr.name: <17} {tr.n_stations: <8} {tr.xleft: <8.2f} {tr.xright: <8.2f} 0.0      0.0      {tr.meander_modifier: <8.2f} {tr.station_modifier: <8.2f} {tr.elev_offset: <8}\n"
            )

            ## Station and elevation data
            for batch_elev, batch_stat in zip(
                batched(tr.elevation, 5), batched(tr.station, 5)
            ):
                stream.write("GR ")
                for elev, stat in zip(batch_elev, batch_stat):
                    stream.write(f"{elev: <8.2f} {stat: <8.2f} ")
                stream.write("\n")

    @classmethod
    def print_inp(cls, transects: Iterable[Self]):
        with StringIO() as stream:
            cls.make_inp(transects=transects, stream=stream)
            print(stream.getvalue())


@dataclass
class XSection:
    """Provides cross-section geometric data for conduit and regulator links of the drainage system.

    Attributes
    ----------
    link : Conduit
        Conduit object, orifice, or weir.
    shape : BaseGeometricShape
        Cross-section shape (see Tables D-2 for available shapes).
    barrels : int = 1
        Number of barrels (i.e., number of parallel pipes of equal size, slope, and
        roughness) associated with a conduit. Default is 1.
    culvert : str = ""
        Code number from Table A.10 for the conduit’s inlet geometry if it is a
        culvert subject to possible inlet flow control. Leave blank otherwise.
    curve : Optional[Curve] = None
        Name of a Shape Curve in the [CURVES] section that defines how cross-section
        width varies with depth.
    tsect : Optional[Transect] = None
        Name of an entry in the [TRANSECTS] section that describes the cross-section
        geometry of an irregular channel.
    street : Optional[Street] = None
        Name of an entry in the [STREETS] section that describes the cross-section
        geometry of a street.
    """

    link: Conduit
    shape: xshapes.BaseGeometricShape
    barrels: int = 1
    culvert: int | str = ""
    curve: Optional[Curve] = None
    tsect: Optional[Transect] = None
    street: Optional[Street] = None

    def __post_init__(self):
        if not isinstance(self.shape, xshapes.BaseGeometricShape):
            raise ValueError("Shape must be a subclass of BaseGeometricShape")

        if isinstance(self.shape, xshapes.Custom):
            if not isinstance(self.curve, Curve):
                raise ValueError("curve must be a Curve object if shape is Custom")

        elif isinstance(self.shape, xshapes.Street):
            if not isinstance(self.street, Street):
                raise ValueError("street must be a Street object if shape is Street")

        elif isinstance(self.shape, xshapes.Irregular):
            if not isinstance(self.tsect, Transect):
                raise ValueError(
                    "tsect must be a Transect object if shape is Irregular"
                )

    @property
    def as_inp(self):
        if isinstance(self.shape, xshapes.Custom):
            return f"{self.link.name: <16} {self.shape.as_inp} {self.curve.name: <16} {self.barrels: <10}"
        elif isinstance(self.shape, xshapes.Irregular):
            return f"{self.link.name: <16} {self.shape.as_inp} {self.tsect.name: <16}"
        elif isinstance(self.shape, xshapes.Street):
            return f"{self.link.name: <16} {self.shape.as_inp} {self.street.name: <16}"

        return f"{self.link.name: <16} {self.shape.as_inp} {self.barrels: <10} {self.culvert: <10}"

    @classmethod
    def make_inp(cls, stream: TextIO, xsections: Iterable[Self]):
        stream.write("[XSECTIONS]\n")
        stream.write(
            ";;Link           Shape        Geom1            Geom2      Geom3      Geom4      Barrels    Culvert   \n"
            ";;-------------- ------------ ---------------- ---------- ---------- ---------- ---------- ----------\n"
        )
        for xsection in xsections:
            stream.write(f"{xsection.as_inp}\n")


@dataclass
class Inlet:
    """
    Defines inlet structure designs used to capture street and channel flow that are
    sent to below ground sewers.

    Attributes
    ----------
    name : str
        Name assigned to the inlet structure.
    type: Literal["GRATE", "DROP_GRATE", "CURB", "DROP_CURB", "SLOTTED", "CUSTOM"]
        Type of inlet structure. GRATE, CURB, and SLOTTED inlets are used with
        STREET conduits, DROP_GRATE and DROP_CURB inlets with open channels, and a
        CUSTOM inlet with any conduit.
    length : Optional[float] = None
        Length of the inlet parallel to the street curb (ft or m).
    width : Optional[float] = None
        Width of a GRATE or SLOTTED inlet (ft or m).
    height : Optional[float] = None
        Height of a CURB opening inlet (ft or m).
    type_grate : Optional[Literal["P_BAR-50", "P_BAR-50X100", "P_BAR-30",
        "CURVED_VANE","TILT_BAR-45", "TILT_BAR-30", "RETICULINE", "GENERIC"]]
        Type of GRATE used.
    aopen : Optional[float] = None
        Fraction of a GENERIC grate’s area that is open.
    vsplash : Optional[float] = None
        Splash over velocity for a GENERIC grate (ft/s or m/s).
    throat : Optional[Literal["HORIZONTAL", "INCLINED", "VERTICAL"]] = None
        The throat angle of a CURB opening inlet (HORIZONTAL, INCLINED, or
        VERTICAL).
    dcurve : Optional[Curve] = None
        A Diversion-type Curve object (captured flow vs. approach flow) for a
        CUSTOM inlet.
    rcurve : Optional[Curve] = None
        Name of a Rating-type Curve object (captured flow vs. water depth) for a
        CUSTOM inlet.
    """

    name: str
    type: Literal["GRATE", "DROP_GRATE", "CURB", "DROP_CURB", "SLOTTED", "CUSTOM"]
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    type_grate: Optional[
        Literal[
            "P_BAR-50",
            "P_BAR-50X100",
            "P_BAR-30",
            "CURVED_VANE",
            "TILT_BAR-45",
            "TILT_BAR-30",
            "RETICULINE",
            "GENERIC",
        ]
    ] = None
    aopen: Optional[float] = None
    vsplash: Optional[float] = None
    throat: Optional[Literal["HORIZONTAL", "INCLINED", "VERTICAL"]] = None
    dcurve: Optional[Curve] = None
    rcurve: Optional[Curve] = None

    def __post_init__(self):
        if self.type in ["GRATE", "DROP_GRATE"]:
            if self.length is None:
                raise ValueError(
                    "length must be specified for GRATE and DROP_GRATE inlets"
                )
            if self.width is None:
                raise ValueError(
                    "width must be specified for GRATE and DROP_GRATE inlets"
                )
            if self.type_grate is None:
                raise ValueError(
                    "type_grate must be specified for GRATE and DROP_GRATE inlets"
                )

            if self.type_grate == "GENERIC":
                if self.aopen is None:
                    raise ValueError("aopen must be specified for GENERIC inlets")
                if self.vsplash is None:
                    raise ValueError("vsplash must be specified for GENERIC inlets")

        elif self.type in ["CURB", "DROP_CURB"]:
            if self.length is None:
                raise ValueError(
                    "length must be specified for CURB and DROP_CURB inlets"
                )
            if self.height is None:
                raise ValueError(
                    "height must be specified for CURB and DROP_CURB inlets"
                )
            if self.throat is None and self.type == "CURB":
                raise ValueError(
                    "throat must be specified for CURB and DROP_CURB inlets"
                )

        elif self.type == "SLOTTED":
            if self.length is None:
                raise ValueError("length must be specified for SLOTTED inlets")
            if self.width is None:
                raise ValueError("width must be specified for SLOTTED inlets")

        elif self.type == "CUSTOM":
            if not isinstance(self.dcurve, Curve) and not isinstance(
                self.rcurve, Curve
            ):
                raise ValueError(
                    "A Curve object must be specified as dcurve or as rcurce for CUSTOM inlets"
                )
            if isinstance(self.rcurve, Curve) and isinstance(self.dcurve, Curve):
                raise ValueError(
                    "Specify only one of dcurve or rcurve for CUSTOM inlets"
                )

        else:
            raise ValueError(
                "type must be one of GRATE, DROP_GRATE, CURB, DROP_CURB, SLOTTED, or CUSTOM"
            )

    @property
    def as_inp(self):
        if self.type in ["GRATE", "DROP_GRATE"]:
            if self.type_grate == "GENERIC":
                return f"{self.name: <16} {self.type: <16} {self.length: <9.2f} {self.width: <9.2f} {self.type_grate: <12} {self.aopen: <9.2f} {self.vsplash: <9.2f}"
            else:
                return f"{self.name: <16} {self.type: <16} {self.length: <9.2f} {self.width: <9.2f} {self.type_grate: <12}"

        elif self.type in ["CURB", "DROP_CURB"]:
            if self.type == "CURB":
                return f"{self.name: <16} {self.type: <16} {self.length: <9.2f} {self.height: <9.2f} {self.throat: <12}"
            else:
                return f"{self.name: <16} {self.type: <16} {self.length: <9.2f} {self.height: <9.2f}"

        elif self.type == "SLOTTED":
            return f"{self.name: <16} {self.type: <16} {self.length: <9.2f} {self.width: <9.2f}"

        elif self.type == "CUSTOM":
            if self.dcurve is not None:
                return f"{self.name: <16} {self.type: <16} {self.dcurve.name: <16}"
            else:
                return f"{self.name: <16} {self.type: <16} {self.rcurve.name: <16}"

    @classmethod
    def make_inp(cls, stream: TextIO, inlets: Iterable[Self]):
        stream.write(
            "[INLETS]\n"
            ";;Name           Type             Parameters:\n"
            ";;-------------- ---------------- -----------\n"
        )

        for inlet in inlets:
            stream.write(f"{inlet.as_inp}\n")


@dataclass
class InletUsage:
    """Assigns inlet structures to specific street and open channel conduits.

    Attributes
    ----------
    conduit : Conduit
        Name of a street or open channel conduit containing the inlet.
        Only conduits with a STREET cross section can be assigned a CURB and
        GUTTER inlet while DROP inlets can only be assigned to conduits with a
        RECT_OPEN or TRAPEZOIDAL cross section.
    inlet : Inlet
        Inlet object to use.
    node : Junction
        Name of the network node receiving flow captured by the inlet.
    number : int = 1
        Number of replicate inlets placed on each side of the street.
    percent_clogged : float = 0
        Degree to which inlet capacity is reduced due to clogging (%).
    qmax : float = 0
        Maximum flow that the inlet can capture (flow units). A qmax value of
        0 indicates that the inlet has no flow restriction.
    alocal : float = 0
        Height of local gutter depression (in or mm).
    wlocal : float = 0
        Width of local gutter depression (ft or m).
    placement : Literal["AUTOMATIC", "ON_GRADE", "ON_SAG"] = "AUTOMATIC"
        Placement type for the inlet. The default inlet placement is AUTOMATIC,
        meaning that the program uses the network topography to determine
        whether an inlet operates on-grade or on-sag. On-grade means the inlet
        is located on a continuous grade. On-sag means the inlet is located at
        a sag or sump point where all adjacent conduits slope towards the
        inlet leaving no place for water to flow except a into the inlet.
    """

    conduit: Conduit
    inlet: Inlet
    node: Junction
    number: int = 1
    percent_clogged: float = 0
    qmax: float = 0
    alocal: float = 0
    wlocal: float = 0
    placement: Literal["AUTOMATIC", "ON_GRADE", "ON_SAG"] = "AUTOMATIC"

    def __post_init__(self):
        if not isinstance(self.conduit, Conduit):
            raise ValueError("conduit must be a Conduit object")

        if not isinstance(self.inlet, Inlet):
            raise ValueError("inlet must be an Inlet object")

        if not isinstance(self.node, Junction):
            raise ValueError("node must be a Junction object")

    @property
    def as_inp(self):
        return f"{self.conduit.name: <16} {self.inlet.name: <16} {self.node.name: <16} {self.number: <9} {self.percent_clogged: <9.2f} {self.qmax: <9.2f} {self.alocal: <9.2f} {self.wlocal: <9.2f} {self.placement: <19}"

    @classmethod
    def make_inp(cls, stream: TextIO, inlet_usages: Iterable[Self]):
        stream.write(
            "[INLET_USAGE]\n"
            ";;Conduit        Inlet            Node             Number    %Clogged  Qmax      aLocal    wLocal    Placement\n"
            ";;-------------- ---------------- ---------------- --------- --------- --------- --------- --------- --------- ---------\n"
        )

        for iu in inlet_usages:
            stream.write(f"{iu.as_inp}\n")


@dataclass
class Map:
    """Provides dimensions and distance units for the map.

    Attributes
    ----------
    dimensions : Iterable[float]
        The dimensions of the map in the order X1, Y1, X2, Y2, where:
        - X1: lower-left X coordinate of full map extent
        - Y1: lower-left Y coordinate of full map extent
        - X2: upper-right X coordinate of full map extent
        - Y2: upper-right Y coordinate of full map extent
    units : Literal["FEET", "METERS", "DEGREES", "NONE"] = "NONE"
        Distance units for the map. Default is NONE.

    """

    dimensions: Iterable[float]
    units: Literal["FEET", "METERS", "DEGREES", "NONE"] = "NONE"

    def __post_init__(self):
        if len(self.dimensions) != 4:
            raise ValueError("dimensions must be a 4-element iterable")

    def make_inp(self, stream):
        stream.write("[MAP]\n")
        stream.write(
            "DIMENSIONS " + " ".join(f"{d:.2f}" for d in self.dimensions) + "\n"
        )
        stream.write(f"UNITS     {self.units}\n")


@dataclass
class Coordinate:
    """Assigns X,Y coordinates to drainage system nodes."""

    node: Junction | Outfall
    coord: Iterable[float]

    def __post_init__(self):
        if not isinstance(self.node, (Junction, Outfall)):
            raise ValueError("node must be a Junction or Outfall object")

        if len(self.coord) != 2:
            raise ValueError("coord must be a 2-element iterable")

        self.xcoord = self.coord[0]
        self.ycoord = self.coord[1]

        # if getattr(self.node, "xcoord", False):
        #     if self.xcoord is not None:
        #         warnings.warn(
        #             "xcoord was specified for node, but node already has xcoord "
        #             "attribute. xcoord will be ignored."
        #         )

        #     self.xcoord = self.node.xcoord

        # if getattr(self.node, "ycoord", False):
        #     if self.ycoord is not None:
        #         warnings.warn(
        #             "ycoord was specified for node, but node already has ycoord "
        #             "attribute. ycoord will be ignored."
        #         )

        #     self.ycoord = self.node.ycoord

    @property
    def as_inp(self):
        return f"{self.node.name: <16} {self.xcoord: <18.3f} {self.ycoord: <18.3f}"

    @classmethod
    def make_inp(cls, stream: TextIO, coordinates: Iterable[Self]):
        stream.write(
            "[COORDINATES]\n"
            ";;Node           X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
        )

        for coord in coordinates:
            stream.write(f"{coord.as_inp}\n")


@dataclass
class SymbolPoint:
    """Assigns X,Y coordinates to rain gage symbols."""

    gage: Raingage
    coord: Iterable[float]

    def __post_init__(self):
        if not isinstance(self.gage, Raingage):
            raise ValueError("gage must be a Raingage object")

        if len(self.coord) != 2:
            raise ValueError("coord must be a 2-element iterable")

        self.xcoord = self.coord[0]
        self.ycoord = self.coord[1]

    @property
    def as_inp(self):
        return f"{self.gage.name: <16} {self.xcoord: <18.3f} {self.ycoord: <18.3f}"

    @classmethod
    def make_inp(cls, stream: TextIO, raingages_symbols: Iterable[Self]):
        stream.write(
            "[SYMBOLS]\n"
            ";;Rain Gage      X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
        )


@dataclass
class LinkVertex:
    """Assigns X,Y coordinates to interior vertex points of curved drainage
    system links. Include a separate line for each interior vertex of the
    link, ordered from the inlet node to the outlet node.
    Straight-line links have no interior vertices and therefore are not listed in this section."""

    link: Conduit
    coord: Iterable[float]

    def __post_init__(self):
        if not isinstance(self.link, Conduit):
            raise ValueError("link must be a Conduit object")

        if len(self.coord) != 2:
            raise ValueError("coord must be a 2-element iterable")

        self.xcoord = self.coord[0]
        self.ycoord = self.coord[1]

    @property
    def as_inp(self):
        return f"{self.link.name: <16} {self.xcoord: <18.3f} {self.ycoord: <18.3f}"

    @classmethod
    def make_inp(cls, stream: TextIO, vertices: Iterable[Self]):
        stream.write(
            "[VERTICES]\n"
            ";;Link           X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
        )

        for vertex in vertices:
            stream.write(f"{vertex.as_inp}\n")


@dataclass
class PolygonVertex:
    """Assigns X,Y coordinates to vertex points of polygons that define a
    subcatchment boundary. Include a separate line for each vertex of the
    subcatchment polygon, ordered in a consistent clockwise or counter-
    clockwise sequence."""

    subcatchment: Subcatchment
    coord: Iterable[float]

    def __post_init__(self):
        if not isinstance(self.subcatchment, Subcatchment):
            raise ValueError("subcatchment must be a Subcatchment object")

        if len(self.coord) != 2:
            raise ValueError("coord must be a 2-element iterable")

        self.xcoord = self.coord[0]
        self.ycoord = self.coord[1]

    @property
    def as_inp(self):
        return (
            f"{self.subcatchment.name: <16} {self.xcoord: <18.3f} {self.ycoord: <18.3f}"
        )

    @classmethod
    def make_inp(cls, stream: TextIO, vertices: Iterable[Self]):
        stream.write(
            "[POLYGONS]\n"
            ";;Subcatchment   X-Coord            Y-Coord           \n"
            ";;-------------- ------------------ ------------------\n"
        )
        for vertex in vertices:
            stream.write(f"{vertex.as_inp}\n")


@dataclass
class Report:
    """Describes the contents of the report file that is produced.

    Attributes
    ----------
    disabled : Literal["YES, NO"] = "NO"
        Setting DISABLED to YES disables all reporting (except for error and
        warning messages) regardless of what other reporting options are
        chosen. The default is NO.
    input : Literal["YES, NO"] = "NO"
        Specifies whether or not a summary of the input data should be provided
        in the output report. The default is NO.
    continuity : Literal["YES, NO"] = "YES"
        Specifies if continuity checks should be reported or not. The default
        is YES.
    flowstats : Literal["YES, NO"] = "YES"
        Specifies whether summary flow statistics should be reported or not.
        The default is YES
    controls : Literal["YES, NO"] = "NO"
        Specifies whether all control actions taken during a simulation should
        be listed or not. The default is NO
    subcatchments : Literal["ALL", "NONE"] | list[Subcatchment] = "NONE"
        Gives a list of subcatchments whose results are to be reported. The default
        is NONE.
    subcatchments : Literal["ALL", "NONE"] | list[Junction, Outfall] = "NONE"
        Gives a list of nodes whose results are to be reported. The default is NONE.
    links : Literal["ALL", "NONE"] | list[Conduit] = "NONE"
        Gives a list of links whose results are to be reported. The default is NONE.
    lid : str = ""
        raises NotImplementedError.
    """

    disabled: Literal["YES, NO"] = "NO"
    input: Literal["YES, NO"] = "NO"
    continuity: Literal["YES, NO"] = "YES"
    flowstats: Literal["YES, NO"] = "YES"
    controls: Literal["YES, NO"] = "NO"
    subcatchments: Literal["ALL", "NONE"] | list[Subcatchment] = "NONE"
    nodes: Optional[Literal["ALL"] | list[Junction, Outfall]] = None
    links: Optional[Literal["ALL"] | list[Conduit]] = None
    lid: str = ""

    def __post_init__(self):
        if self.lid:
            raise NotImplementedError("lid is not yet implemented")

    def make_inp(self, stream):
        stream.write("[REPORT]\n")

        for key, value in self.__dict__.items():
            stream.write(f"{key.upper(): <21} {value}\n")
