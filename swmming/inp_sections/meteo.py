import typing

from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self, Literal

from .tabular import Timeseries, Pattern
from .type_helpers import EvaporationFormatType


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
    station_name : str = ""
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
    station_name: Optional[str] = None
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

            if self.station_name is None:
                raise ValueError("sta must be specified if fname is specified")

            if self.units not in ["IN", "MM"]:
                raise ValueError("Units must be one of IN or MM")

    @property
    def as_inp(self):
        if self._mode == "TIMESERIES":
            return f"{self.name: <16} {self.form: <9} {self.interval: <9} {self.scf: <6.2f} {self._mode} {self.tseries.name} "

        elif self._mode == "FILE":
            return f"{self.name: <16} {self.form: <9} {self.interval: <9} {self.scf: <6.2f} {self._mode} {self.fname} {self.station_name: <10} {self.units: <10}"

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
class Evaporation:
    """Specifies how daily potential evaporation rates vary with time for the
    study area. If no [EVAPORATION] section appears, then evaporation is
    assumed to be 0. The evaporation rates provided in this section are
    **potential rates**. The actual amount of water evaporated will depend
    on the amount available as a simulation progresses.

    Attributes
    ----------
    evap_format: EvaporationFormatType
        Specifies how evaporation rates vary with time.
    const_evap_rate: Optional[float] = None
        Constant evaporation rate (in/day or mm/day).
    monthly_evap_rate: Optional[Iterable[float]] = None
        Monthly evaporation rates (in/day or mm/day).
    tseries_evap_rate: Optional[Timeseries] = None
        Timeseries object with evaporation data.
    file_pan_coef: Optional[Literal[float]] = None
        Monthly pan coefficient for evaporation data.
    recovery: Optional[Pattern] = None
        Identifies an optional monthly time Pattern object used to
        modify infiltration recovery rates during dry periods.
    dry_only: Literal["YES", "NO"] = "NO"
        determines if evaporation only occurs during periods with no
        precipitation. The default is NO.

    Notes
    -----
    - TEMPERATURE indicates that evaporation rates will be computed from the
    daily air temperatures contained in an external climate file whose name is
    provided in the [TEMPERATURE] section. This method also uses the site's
    latitude, which can also be specified in the [TEMPERATURE] section.

    - FILE indicates that evaporation data will be read directly from the same
    xternal climate file used for air temperatures as specified in the
    [TEMPERATURE] section. Supplying monthly pan coefficients for these data is
    optional.

    - For recovery patterns, for example, if the normal infiltration recovery
    rate was 1% during a specific time period and a pattern factor of 0.8
    applied to this period, then the actual recovery rate would be 0.8%.

    """

    evap_format: EvaporationFormatType
    recovery: Optional[Pattern] = None
    dry_only: Literal["YES", "NO"] = "NO"

    def __post_init__(self, **kwargs):
        if self.evap_format not in typing.get_args(EvaporationFormatType):
            raise ValueError(
                "evap_format must be one of "
                "CONSTANT, MONTHLY, TIMESERIES, TEMPERATURE, FILE"
            )

        if self.evap_format == "CONSTANT":
            if self.const_evap_rate is None:
                raise ValueError(
                    "const_evap_rate must be specified if evap_format is CONSTANT"
                )

            self._parameters_as_str = self.const_evap_rate

        elif self.evap_format == "MONTHLY":
            if self.monthly_evap_rate is None:
                raise ValueError(
                    "monthly_evap_rate must be specified if evap_format is MONTHLY"
                )

            elif len(self.monthly_evap_rate) != 12:
                raise ValueError("monthly_evap_rate must be an Iterable of 12 values")

            self._parameters_as_str = "".join(
                f"{v: <10.3f}" for v in self.monthly_evap_rate
            )

        elif self.evap_format == "TIMESERIES":
            if not isinstance(self.tseries_evap_rate, Timeseries):
                raise ValueError(
                    "tseries_evap_rate must be a Timeseries object if evap_format "
                    "is TIMESERIES"
                )

            self._parameters_as_str = self.tseries_evap_rate.name

        elif self.evap_format == "FILE":
            if self.file_pan_coef is None:
                raise ValueError(
                    "file_pan_coef must be specified if evap_format is FILE"
                )
            elif len(self.file_pan_coef) != 12:
                raise ValueError("file_pan_coef must be an Iterable of 12 values")

            self._parameters_as_str = "".join(
                f"{v: <10.3f}" for v in self.file_pan_coef
            )

        if self.recovery is not None:
            raise NotImplementedError("recovery is not yet implemented")

    def make_inp(self, stream: TextIO):
        stream.write(
            "[EVAPORATION]\n"
            ";;Data Source    Parameters\n"
            ";;-------------- ----------------\n"
            f"{self.evap_format: <16} {self._parameters_as_str}\n"
            f"DRY_ONLY         {self.dry_only: <16}\n"
        )

        if self.recovery:
            stream.write(f"RECOVERY         {self.recovery.name: <16}\n")


@dataclass
class SnowmeltParams:
    """Container for snowmelt parameters.

    Attributes
    ----------
    temp: Optional[float] = None
        Air temperature at which precipitation falls as snow (deg F or C).
    ati_wt: float = 0.5
        Antecedent temperature index weight (default is 0.5).
    rnm: float = 0.6
        Negative melt ratio (default is 0.6).
    elev: float = 0.0
        Average elevation of study area above mean sea level (ft or m)
        (default is 0).
    lat: float = 50.0
        Latitude of the study area in degrees North (default is 50).
    dt_long: float = 0.0
        Correction, in minutes of time, between true solar time and the
        standard clock time (default is 0)"""

    stemp: float
    ati_wt: float = 0.5
    rnm: float = 0.6
    elev: float = 0.0
    lat: float = 50.0
    dt_long: float = 0.0


@dataclass
class Temperature:
    """Specifies daily air temperatures, monthly wind speed, and various
    snowmelt parameters for the study area. Required only when snowmelt is
    being modeled or when evaporation rates are computed from daily
    temperatures or are read from an external climate file.

    Attributes
    ----------
    tseries: Optional[Timeseries | str] = None
        Timeseries object with temperature data or name of an external
        Climate file with temperature data. If neither
        format is used, then air temperature remains constant at 70 degrees F.
    file_start: Optional[str] = None
        Date to begin reading from the file in month/day/year format
        (default is the beginning of the file).
    file_units: Optional[Literal["C", "F", "C10"]] = "C10"
        Temperature units for GHCN files (C10 for tenths of a degree C
        (the default), C for degrees Celsius, or F for degrees Fahrenheit).
    windspeed: Optional[Iterable[float] | Literal["FILE"]] = None
        Monthly wind speeds (in mph or km/h). Wind speed can be specified
        either by monthly average values or by the same Climate file
        used for air temperature. If neither option appears, then wind speed
        is assumed to be 0.
    snowmelt: Optional[SnowmeltParams] = None
        Parameters for snowmelt computations.
    adc_impervious: Optional[Iterable[float]] = None
        Areal Depletion Curves for impervious areas. Fraction of area
        covered by snow when ratio of snow depth to depth at 100% cover is
        0, 0.1, ... to 0.9. Defaults to 1.0 for all, meaning no depletion.
    adc_pervious: Optional[Iterable[float]] = None
        Areal Depletion Curves for pervious areas. Fraction of area
        covered by snow when ratio of snow depth to depth at 100% cover is
        0, 0.1, ... to 0.9. Defaults to 1.0 for all, meaning no depletion.
    """

    tseries: Optional[Timeseries | str] = None
    file_start: Optional[str] = None
    file_units: Optional[Literal["C", "F", "C10"]] = "C10"
    windspeed: Optional[Iterable[float] | Literal["FILE"]] = None
    snowmelt: Optional[SnowmeltParams] = None
    adc_impervious: Optional[Iterable[float]] = None
    adc_pervious: Optional[Iterable[float]] = None

    def __post_init__(self):
        if isinstance(self.tseries, Timeseries):
            self._mode = "TIMESERIES"

        elif isinstance(self.tseries, str):
            self._mode = "FILE"

            if self.file_start is None:
                raise ValueError("file_start must be specified if tseries is a file")

            if self.file_units not in ["C", "F", "C10"]:
                raise ValueError("file_units must be one of C, F, or C10")

        if not self.windspeed == "FILE":
            if len(self.windspeed) != 12:
                raise ValueError("windspeed must be an Iterable of 12 values")

        if self.adc_impervious is not None:
            if len(self.adc_impervious) != 9:
                raise ValueError("adc_impervious must be an Iterable of 9 values")
        else:
            self.adc_impervious = [1.0] * 9

        if self.adc_pervious is not None:
            if len(self.adc_pervious) != 9:
                raise ValueError("adc_pervious must be an Iterable of 9 values")
        else:
            self.adc_pervious = [1.0] * 9

        self.adc_impv_as_str = "".join(f"{v: <10.3f}" for v in self.adc_impervious)
        self.adc_perv_as_str = "".join(f"{v: <10.3f}" for v in self.adc_pervious)


class Adjustments:
    def __init__(self):
        raise NotImplementedError("Adjustments is not yet implemented")
