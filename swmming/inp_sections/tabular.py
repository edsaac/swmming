from dataclasses import dataclass
from typing import Iterable, Self
from textwrap import wrap


class Curve:
    def __init__(self):
        raise NotImplementedError("Curve is not yet implemented")


class Pattern:
    def __init__(self):
        raise NotImplementedError("Curve is not yet implemented")


@dataclass
class Timeseries:
    """Describes how a quantity varies over time.

    Attributes
    ----------
    name : str
        Name assigned to the time series.
    time_ts : Iterable[float]
        Hours since the start of the simulation, expressed as a decimal number or as hours:minutes (where hours can be greater than 24).
    value_ts : Iterable[float]
        A value corresponding to the specified date and time.
    date_ts : str
        Date in Month/Day/Year format (e.g., June 15, 2001 would be 6/15/2001).
    hour_ts : str
        24-hour military time (e.g., 8:40 pm would be 20:40) relative to the last date specified (or to midnight of the starting date of the simulation if no previous date was specified).
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
