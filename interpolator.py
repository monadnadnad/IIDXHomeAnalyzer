import datetime
import matplotlib.dates as mdates
from collections import defaultdict
from abc import ABC, abstractmethod
from statistics import median_high
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

class OnedayAccumulator(ABC):
    def __init__(self):
        tick = 5
        # 24:00からtick分前までを扱う
        self._xs: list[datetime.timedelta] = [
            i*datetime.timedelta(minutes=tick)
            for i in range(24*60//tick)
        ]
        self._fake_date = datetime.datetime(2022,1,1,0,0,0)
        self._fake_oneday = [self._fake_date + t for t in self._xs]
    def _to_fake_oneday(self, xs: list[datetime.datetime]):
        return [
            self._fake_date
            + (t-datetime.datetime.combine(t.date(), datetime.time.min)) for t in xs
        ]
    def append(self, xs: list[datetime.datetime], ys: list[float]):
        """
        時系列のfloatデータに対して補間と集積を行う
        `xs`は時系列順で1日以内な必要がある
        """
        if xs[-1] - xs[0] > datetime.timedelta(days=1):
            raise ValueError("`xs` should be in 24 hours")
        new_ys = _interpolate_datetimex(self._to_fake_oneday(xs), ys, self._fake_oneday)
        self._process_interpolated_data(new_ys)
    @abstractmethod
    def _process_interpolated_data(self, new_ys):
        """
        一日に補間されたデータを集積する
        データの長さは`_xs`に揃える
        """
        raise NotImplementedError
    @abstractmethod
    def result(self) -> dict[datetime.timedelta, float]:
        """
        appendされたデータから一日に補間と集積を行った結果を返す
        """
        raise NotImplementedError

class OnedaySum(OnedayAccumulator):
    def __init__(self):
        super().__init__()
        self._result: defaultdict[datetime.timedelta, float] = defaultdict(float)
    def _process_interpolated_data(self, new_ys):
        for x, y in zip(self._xs, new_ys):
            # ignore overflow
            self._result[x] += y
    def result(self) -> dict[datetime.timedelta, float]:
        return dict(self._result)

class OnedayAverage(OnedayAccumulator):
    def __init__(self):
        super().__init__()
        self._count = 0
        self._result: defaultdict[datetime.timedelta, float] = defaultdict(float)
    def _process_interpolated_data(self, new_ys):
        self._count += 1
        for x, y in zip(self._xs, new_ys):
            # ignore overflow
            self._result[x] += y
    def result(self) -> dict[datetime.timedelta, float]:
        assert self._count > 0
        for k in self._result:
            self._result[k] /= self._count
        return dict(self._result)

class OnedayMedian(OnedayAccumulator):
    def __init__(self):
        super().__init__()
        self._count = 0
        self._result: defaultdict[datetime.timedelta, list[float]] = defaultdict(list)
    def _process_interpolated_data(self, new_ys):
        self._count += 1
        for x, y in zip(self._xs, new_ys):
            self._result[x].append(y)
    def result(self) -> dict[datetime.timedelta, float]:
        assert self._count > 0
        d = {}
        for k in self._result:
            d[k] = median_high(self._result[k])
        return d

class OnedayMax(OnedayAccumulator):
    def __init__(self):
        super().__init__()
        self._result: defaultdict[datetime.timedelta, float] = defaultdict(lambda:-float("inf"))
    def _process_interpolated_data(self, new_ys):
        for x, y in zip(self._xs, new_ys):
            if self._result[x] < y:
                self._result[x] = y
    def result(self) -> dict[datetime.timedelta, float]:
        return dict(self._result)
