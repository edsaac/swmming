from typing import Iterable
from dataclasses import dataclass


@dataclass
class BaseGeometricShape:
    def __post_init__(self, name: str):
        self._name = ""
        self._geom: Iterable[float] = [0, 0, 0, 0]

    @property
    def as_inp(self):
        if self._geom:
            return f"{self._name: <12} {self._geom[0]: <17.2f}" + " ".join(
                [f"{g: <10.2f}" for g in self._geom[1:]]
            )

        else:
            return f"{self._name: <12}"


@dataclass
class Circular(BaseGeometricShape):
    diameter: float

    def __post_init__(self):
        self._name = "CIRCULAR"
        self._geom = [self.diameter, 0, 0, 0]


@dataclass
class ForceMain(BaseGeometricShape):
    diameter: float
    roughness: float

    def __post_init__(self):
        self._name = "FORCE_MAIN"
        self._geom = [self.diameter, self.roughness, 0, 0]


@dataclass
class FilledCircular(BaseGeometricShape):
    diameter: float
    sediment_depth: float

    def __post_init__(self):
        self._name = "FILLED_CIRCULAR"
        self._geom = [self.diameter, self.sediment_depth, 0, 0]


@dataclass
class RectClosed(BaseGeometricShape):
    full_height: float
    top_width: float

    def __post_init__(self):
        self._name = "RECT_CLOSED"
        self._geom = [self.full_height, self.top_width, 0, 0]


@dataclass
class RectOpen(BaseGeometricShape):
    full_height: float
    top_width: float

    def __post_init__(self):
        self._name = "RECT_OPEN"
        self._geom = [self.full_height, self.top_width, 0, 0]


@dataclass
class Trapezoidal(BaseGeometricShape):
    """Slopes are horizontal run / vertical rise"""

    full_height: float
    base_width: float
    left_slope: float
    right_slope: float

    def __post_init__(self):
        self._name = "TRAPEZOIDAL"
        self._geom = [
            self.full_height,
            self.base_width,
            self.left_slope,
            self.right_slope,
        ]


@dataclass
class Triangular(BaseGeometricShape):
    full_height: float
    top_width: float

    def __post_init__(self):
        self._name = "TRIANGULAR"
        self._geom = [self.full_height, self.top_width, 0, 0]


@dataclass
class HorizEllipse(BaseGeometricShape):
    """Size codes in Appendix A12 of SWMM Users Manual"""

    full_height: float
    max_width: float
    size_code: int

    def __post_init__(self):
        self._name = "HORIZ_ELLIPSE"
        self._geom = [self.full_height, self.max_width, self.size_code, 0]


@dataclass
class VertEllipse(BaseGeometricShape):
    """Size codes in Appendix A12 of SWMM Users Manual"""

    full_height: float
    max_width: float
    size_code: int

    def __post_init__(self):
        self._name = "VERT_ELLIPSE"
        self._geom = [self.full_height, self.max_width, self.size_code, 0]


@dataclass
class Arch(BaseGeometricShape):
    """Size codes in Appendix A13 of SWMM Users Manual"""

    full_height: float
    max_width: float
    size_code: int

    def __post_init__(self):
        self._name = "ARCH"
        self._geom = [self.full_height, self.max_width, self.size_code, 0]


@dataclass
class Parabolic(BaseGeometricShape):
    full_height: float
    top_width: float

    def __post_init__(self):
        self._name = "PARABOLIC"
        self._geom = [self.full_height, self.top_width, 0, 0]


@dataclass
class Power(BaseGeometricShape):
    full_height: float
    top_width: float
    exponent: float

    def __post_init__(self):
        self._name = "POWER"
        self._geom = [self.full_height, self.top_width, self.exponent, 0]


@dataclass
class RectTriangular(BaseGeometricShape):
    full_height: float
    top_width: float
    triangle_height: float

    def __post_init__(self):
        self._name = "RECT_TRIANGULAR"
        self._geom = [self.full_height, self.top_width, self.triangle_height, 0]


@dataclass
class RectRound(BaseGeometricShape):
    full_height: float
    top_width: float
    bottom_radius: float

    def __post_init__(self):
        self._name = "RECT_ROUND"
        self._geom = [self.full_height, self.top_width, self.bottom_radius, 0]


@dataclass
class ModBasketHandle(BaseGeometricShape):
    full_height: float
    base_width: float
    top_radius: float

    def __post_init__(self):
        self._name = "MODBASKETHANDLE"
        self._geom = [self.full_height, self.base_width, self.top_radius, 0]


@dataclass
class Egg(BaseGeometricShape):
    full_height: float

    def __post_init__(self, name: str):
        self._name = "EGG"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class HorseShoe(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "HORSESHOE"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class Gothic(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "GOTHIC"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class Catenary(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "CATENARY"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class SemiElliptical(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "SEMIELLIPTICAL"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class BasketHandle(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "BASKETHANDLE"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class SemiCircular(BaseGeometricShape):
    full_height: float

    def __post_init__(self):
        self._name = "SEMICIRCULAR"
        self._geom = [self.full_height, 0, 0, 0]


@dataclass
class Custom(BaseGeometricShape):
    """The CUSTOM shape is a closed conduit whose width versus height is
    described by a user-supplied Shape Curve."""

    geom1: float

    def __post_init__(self):
        self._name = "CUSTOM"
        self._geom = [self.geom1, "", "", ""]


@dataclass
class Irregular(BaseGeometricShape):
    def __post_init__(self):
        self._name = "IRREGULAR"
        self._geom = []


@dataclass
class Street(BaseGeometricShape):
    def __post_init__(self):
        self._name = "STREET"
        self._geom = []


__all__ = [
    "Circular",
    "ForceMain",
    "FilledCircular",
    "RectClosed",
    "RectOpen",
    "Trapezoidal",
    "Triangular",
    "HorizEllipse",
    "VertEllipse",
    "Arch",
    "Parabolic",
    "Power",
    "RectTriangular",
    "RectRound",
    "ModBasketHandle",
    "Egg",
    "HorseShoe",
    "Gothic",
    "Catenary",
    "SemiElliptical",
    "BasketHandle",
    "SemiCircular",
    "Custom",
    "Irregular",
    "Street",
]
