import datetime
import matplotlib.dates as mdates
from collections import defaultdict
from scipy import interpolate

def _interpolate_datetimex(
        xs: list[datetime.datetime],
        ys: list[float],
        new_xs: list[datetime.datetime],
    ) -> list[float]:
    _xs = mdates.date2num(xs)
    f = interpolate.interp1d(_xs, ys, kind="nearest", bounds_error=False, fill_value=0)
    _new_xs = mdates.date2num(new_xs)
    ys_new = f(_new_xs)
    return ys_new

class OnedayAccumulator:
    def __init__(self):
        tick = 5
        # 24:00からtick分前までを扱う
        self._xs: list[datetime.timedelta] = [
            i*datetime.timedelta(minutes=tick)
            for i in range(24*60//tick)
        ]
        self._fake_date = datetime.datetime(2022,1,1,0,0,0)
        self._fake_oneday = [self._fake_date + t for t in self._xs]
        self._result: defaultdict[datetime.timedelta, list[float]] = defaultdict(list)
    def _to_fake_oneday(self, xs: list[datetime.datetime]):
        return [
            self._fake_date
            + (t-datetime.datetime.combine(t.date(), datetime.time.min)) for t in xs
        ]
    def append(self, xs: list[datetime.datetime], ys: list[float]):
        if max(xs) - min(xs) > datetime.timedelta(days=1):
            raise ValueError("`xs` shoud be in 24 hours")
        new_ys = _interpolate_datetimex(self._to_fake_oneday(xs), ys, self._fake_oneday)
        for x, y in zip(self._xs, new_ys):
            self._result[x].append(y)
    def result(self) -> dict[datetime.timedelta, list[float]]:
        return dict(self._result)
