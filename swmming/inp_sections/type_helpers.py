from typing import Literal

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

EvaporationFormatType = Literal[
    "CONSTANT",
    "MONTHLY",
    "TIMESERIES",
    "TEMPERATURE",
    "FILE",
]

OutfallTypeType = Literal[
    "FREE",
    "NORMAL",
    "FIXED",
    "TIDAL",
    "TIMESERIES",
]
