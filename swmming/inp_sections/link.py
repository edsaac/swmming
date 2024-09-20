from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self

from .catchment import Junction, Outfall


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


class Pump:
    def __init__(self):
        raise NotImplementedError("Pump is not yet implemented")


class Orifice:
    def __init__(self):
        raise NotImplementedError("Orifice is not yet implemented")


class Weir:
    def __init__(self):
        raise NotImplementedError("Weir is not yet implemented")


class Outlet:
    def __init__(self):
        raise NotImplementedError("Outlet is not yet implemented")
