import pytest
import datetime
from interpolator import OnedayAccumulator

def test_oneday_accumulator_sum():
    acc = OnedayAccumulator()
    _date = datetime.datetime(2022,1,1)
    times = [_date + i*datetime.timedelta(minutes=5) for i in range(24*60//5+1)]
    data = [1]*len(times)
    acc.append(times, data)
    acc.append(times, data)
    vs = map(sum, acc.result().values())
    assert all(2 == v for v in vs)
def test_ondday_accumulator_exception():
    acc = OnedayAccumulator()
    times = [
        datetime.datetime(2022,1,1),
        datetime.datetime(2022,1,3)
    ]
    data = [0]*len(times)
    with pytest.raises(ValueError):
        acc.append(times, data)
