from dataclasses import dataclass
from typing import Literal, Optional
from datetime import date, time, timedelta

from .type_helpers import (
    FlowUnitsType,
    InfiltrationMethodType,
    RoutingMethodType,
)

from .catchment import Junction, Subcatchment, Outfall
from .link import Conduit


@dataclass
class Title:
    header: str = "Project Title"
    description: str = "Project Description"

    def make_inp(self, stream):
        stream.write("[TITLE]\n;;Project Title/Notes\n")
        stream.write(self.header + "\n")
        stream.write(self.description)


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
