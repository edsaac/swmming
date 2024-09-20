from dataclasses import dataclass
from typing import Iterable, Literal, TextIO, Self

from .meteo import Raingage
from .catchment import Junction, Outfall
from .link import Conduit
from .catchment import Subcatchment


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
