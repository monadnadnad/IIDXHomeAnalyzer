from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

from io import BytesIO
import datetime
import matplotlib
# GUIを使わない
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Callable

from config import Settings
from log import Log
from logger import JsonRowLogRepository, ScheduleLoggerSettings
from log_analysis import LogAnalyzer
from player import Player
from interpolator import OnedayAverage, OnedayMax, OnedayMedian, OnedaySum

settings = ScheduleLoggerSettings()

app = FastAPI()

def get_buffer() -> BytesIO:
    with BytesIO() as buf:
        yield buf

def plot_datetime(xs: list[datetime.datetime], ys: list[float], buffer: BytesIO):
    # open
    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(xs, ys)
    ax.minorticks_on()
    ax.grid(alpha=0.8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    # free
    plt.close(fig)
def plot_oneday(xs: list[datetime.timedelta], ys: list[float], buffer: BytesIO):
    fake = datetime.datetime(2022,1,1)
    xs = [fake + t for t in xs]
    plot_datetime(xs, ys, buffer)

class LogUsecase:
    def __init__(self):
        self.logs: dict[datetime.date, Log] = {}
        jsonrows = JsonRowLogRepository()
        for logfile in settings.log_directory.iterdir():
            date = datetime.date.fromisoformat(logfile.stem[4:])
            self.logs[date] = jsonrows.get_log_by_date(date)
    # singleton
    def __call__(self):
        return self
    def get_headcounts_of_date(self, date: datetime.date) -> dict[datetime.datetime, float]:
        log = self.logs[date]
        a = LogAnalyzer()
        times = log.get_times()
        headcounts = a.get_headcounts(log)
        return dict(zip(times, headcounts))
    def get_headcounts_average(self) -> dict[datetime.timedelta, float]:
        a = LogAnalyzer()
        acc = OnedayAverage()
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        return acc.result()
    def get_headcounts_median(self) -> dict[datetime.timedelta, float]:
        a = LogAnalyzer()
        acc = OnedayMedian()
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        return acc.result()
    def get_headcounts_max(self) -> dict[datetime.timedelta, float]:
        a = LogAnalyzer()
        acc = OnedayMax()
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        return acc.result()
    def get_headcounts_average_weekday(self, weekday: int) -> dict[datetime.timedelta, float]:
        a = LogAnalyzer()
        acc = OnedayAverage()
        for _date, log in self.logs.items():
            if _date.weekday() != weekday:
                continue
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        return acc.result()
    def get_playtime(self, id: str) -> dict[datetime.timedelta, float]:
        p = Player("fake", id)
        a = LogAnalyzer()
        acc = OnedaySum()
        for log in self.logs.values():
            times = log.get_times()
            piv = a.get_player_in_venue(log, p)
            acc.append(times, list(map(float, piv)))
        return acc.result()
    def get_all_playdate(self, id: str) -> list[datetime.date]:
        p = Player("fake", id)
        ret = []
        a = LogAnalyzer()
        for _date, log in self.logs.items():
            if any(a.get_status_changed(log, p)):
                ret.append(_date)
        return ret
    def get_all_playerlist(self) -> list[Player]:
        ret = set()
        for log in self.logs.values():
            # 名前変更は関知しない
            ps = log.get_players()
            ret.update(ps)
        return list(ret)
    def get_players_over_time(self, date: datetime.date) -> dict[datetime.datetime, set[Player]]:
        a = LogAnalyzer()
        log = self.logs[date]
        times = log.get_times()
        players = a.get_players_over_time(log)
        return dict(zip(times, players))

get_log_usecase: Callable[[], LogUsecase] = LogUsecase()


@app.get("/player/list")
async def player_list(log_usecase: LogUsecase = Depends(get_log_usecase)):
    return log_usecase.get_all_playerlist()

@app.get("/player/{id}/date")
async def player_date(id: str, log_usecase: LogUsecase = Depends(get_log_usecase)):
    return log_usecase.get_all_playdate(id)

@app.get("/player/{id}/time")
async def player_time(
        id: str,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    playtime = log_usecase.get_playtime(id)
    plot_oneday(playtime.keys(), playtime.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/average")
async def headcounts_average(
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    data = log_usecase.get_headcounts_average()
    plot_oneday(data.keys(), data.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/average/{weekday}")
async def headcounts_average_of_weekday(
        weekday: int,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    data = log_usecase.get_headcounts_average_weekday(weekday)
    plot_oneday(data.keys(), data.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/median")
async def headcounts_median(
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    data = log_usecase.get_headcounts_median()
    plot_oneday(data.keys(), data.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/max")
async def headcounts_max(
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    data = log_usecase.get_headcounts_max()
    plot_oneday(data.keys(), data.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/{date}")
async def headcounts_of_date(
        date: datetime.date,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    data = log_usecase.get_headcounts_of_date(date)
    plot_datetime(data.keys(), data.values(), buffer)
    return StreamingResponse(buffer, media_type="image/png")
