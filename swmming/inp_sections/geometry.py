from dataclasses import dataclass
from itertools import batched
from io import StringIO

from typing import TextIO, Iterable, Self, Optional, Literal

from . import xsection_shapes as xshapes
from .base_topology import Node, Link
from .tabular import Curve


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

    link: Link
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
    node : Node
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

    conduit: Link
    inlet: Inlet
    node: Node
    number: int = 1
    percent_clogged: float = 0
    qmax: float = 0
    alocal: float = 0
    wlocal: float = 0
    placement: Literal["AUTOMATIC", "ON_GRADE", "ON_SAG"] = "AUTOMATIC"

    def __post_init__(self):
        if not isinstance(self.conduit, Link):
            raise ValueError("conduit must be a Link object, like a Conduit")

        if not isinstance(self.inlet, Inlet):
            raise ValueError("inlet must be an Inlet object")

        if not isinstance(self.node, Node):
            raise ValueError("node must be a Node object, like a Junction")

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


class Loss:
    def __init__(self):
        raise NotImplementedError("Loss is not yet implemented")


class Control:
    def __init__(self):
        raise NotImplementedError("Control is not yet implemented")
