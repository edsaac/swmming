from typing import TextIO
from typing import Optional
from typing import Iterable

from .inp_sections import (
    Title,
    Options,
    Snowpack,
    Curve,
    Timeseries,
    Raingage,
    Junction,
    Subcatchment,
    Subarea,
    Infiltration,
    Outfall,
    Conduit,
    Street,
    Transect,
    XSection,
    Inlet,
    InletUsage,
    Report,
    Coordinate,
    LinkVertex,
    PolygonVertex,
    Map,
)

from . import xsection_shapes as XShapes


def assemble_inp(
    stream: TextIO,
    title=Title(),
    options=Options(),
    # evaporations=Optional[Iterable[Evaporation]],
    # raingages=Optional[Iterable[Raingage]],
    subcatchments: Optional[Iterable[Subcatchment]] = None,
    subareas: Optional[Iterable[Subarea]] = None,
    infiltration: Optional[Iterable[Infiltration]] = None,
    junctions: Optional[Iterable[Junction]] = None,
    outfalls: Optional[Iterable[Outfall]] = None,
    conduits: Optional[Iterable[Conduit]] = None,
    xsections: Optional[Iterable[XSection]] = None,
    transects: Optional[Iterable[Transect]] = None,
    streets: Optional[Iterable[Street]] = None,
    inlets: Optional[Iterable[Inlet]] = None,
    inlet_usages: Optional[Iterable[InletUsage]] = None,
    timeseries: Optional[Iterable[Timeseries]] = None,
    # report: Optional[Report] = None,
    # tags: Optional[Iterable[Tag]] = None,
    # map: Optional[Map] = None,
    coordinates: Optional[Iterable[Coordinate]] = None,
    vertices: Optional[Iterable[LinkVertex]] = None,
    # vertices: Optional[Iterable[Vertex]] = None,
    polygons: Optional[Iterable[PolygonVertex]] = None,
    # symbols: Optional[Iterable[Symbol]] = None,
    map: Optional[Map] = None,
):
    def add_empty_line():
        stream.write("\n\n")

    title.make_inp(stream)
    add_empty_line()

    options.make_inp(stream)
    add_empty_line()

    if subcatchments:
        Subcatchment.make_inp(stream, subcatchments)
        add_empty_line()

    if subareas:
        Subarea.make_inp(stream, subareas)
        add_empty_line()

    if infiltration:
        Infiltration.make_inp(stream, infiltration)
        add_empty_line()

    if junctions:
        Junction.make_inp(stream, junctions)
        add_empty_line()

    if outfalls:
        Outfall.make_inp(stream, outfalls)
        add_empty_line()

    if conduits:
        Conduit.make_inp(stream, conduits)
        add_empty_line()

    if xsections:
        XSection.make_inp(stream, xsections)
        add_empty_line()

    if transects:
        Transect.make_inp(stream, transects)
        add_empty_line()

    if timeseries:
        Timeseries.make_inp(stream, timeseries)
        add_empty_line()

    if streets:
        Street.make_inp(stream, streets)
        add_empty_line()

    if inlets:
        Inlet.make_inp(stream, inlets)
        add_empty_line()

    if inlet_usages:
        InletUsage.make_inp(stream, inlet_usages)
        add_empty_line()

    if map:
        map.make_inp(stream)
        add_empty_line()

    if coordinates:
        Coordinate.make_inp(stream, coordinates)
        add_empty_line()

    if vertices:
        LinkVertex.make_inp(stream, vertices)
        add_empty_line()

    if polygons:
        PolygonVertex.make_inp(stream, polygons)
        add_empty_line()


__all__ = [
    "Title",
    "Options",
    "Snowpack",
    "Curve",
    "Timeseries",
    "Raingage",
    "Junction",
    "Subcatchment",
    "Subarea",
    "Infiltration",
    "Outfall",
    "Conduit",
    "Street",
    "Transect",
    "XSection",
    "Inlet",
    "InletUsage",
    "Report",
    "Vertex",
    "LinkVertex",
    "PolygonVertex",
    "XShapes",
]
