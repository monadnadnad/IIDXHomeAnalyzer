import pytest
import datetime

from player import Player
from log import Log

def test_log_accepts_only_data_in_one_day():
    with pytest.raises(ValueError):
        Log({
            datetime.datetime(2022,1,1,0,0): [],
            datetime.datetime(2022,1,2,0,0): []
        })
    
    with pytest.raises(ValueError):
        Log({
            datetime.datetime(2022,1,1,12,0): [],
            datetime.datetime(2022,1,2,0,0): []
        })
    
    Log({
        datetime.datetime(2022,1,1,10,0,0): [],
        datetime.datetime(2022,1,1,23,59,59): []
    })
