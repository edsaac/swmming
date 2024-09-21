from dataclasses import dataclass
from typing import Optional, TextIO, Iterable, Self


@dataclass
class Node:
    name: str
    elevation: float


@dataclass
class Link:
    name: str
    from_node: Node
    to_node: Node


@dataclass
class Area:
    name: str
