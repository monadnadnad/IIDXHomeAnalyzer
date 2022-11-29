import pytest
import datetime
from interpolator import OnedayAverage, OnedayMax, OnedayMedian, OnedaySum

@pytest.fixture
def times():
    _date = datetime.datetime(2022,1,1)
    times = [_date + i*datetime.timedelta(minutes=5) for i in range(24*60//5+1)]
    return times

def test_oneday_sum(times):
    acc = OnedaySum()
    data = [1]*len(times)
    acc.append(times, data)
    acc.append(times, data)
    vs = acc.result().values()
    assert all(2 == v for v in vs)

def test_oneday_average(times):
    acc = OnedayAverage()
    data = [1]*len(times)
    acc.append(times, data)
    data = [2]*len(times)
    acc.append(times, data)
    data = [3]*len(times)
    acc.append(times, data)
    vs = acc.result().values()
    assert all(2.0 == v for v in vs)

def test_oneday_median(times):
    acc = OnedayMedian()
    data = [1]*len(times)
    acc.append(times, data)
    data = [2]*len(times)
    acc.append(times, data)
    data = [3]*len(times)
    acc.append(times, data)
    vs = acc.result().values()
    assert all(2.0 == v for v in vs)

def test_oneday_max(times):
    acc = OnedayMax()
    data = [1]*len(times)
    acc.append(times, data)
    data = [10]*len(times)
    acc.append(times, data)
    vs = acc.result().values()
    assert all(10.0 == v for v in vs)

def test_oneday_sum_exception():
    acc = OnedaySum()
    times = [
        datetime.datetime(2022,1,1),
        datetime.datetime(2022,1,3)
    ]
    data = [0]*len(times)
    with pytest.raises(ValueError):
        acc.append(times, data)
