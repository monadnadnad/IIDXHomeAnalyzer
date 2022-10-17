from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

from io import BytesIO
import datetime
import matplotlib
# GUIを使わない
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Callable
from pathlib import Path
from statistics import fmean, median_high

import config
from log import Log
from logger import Logger
from log_analysis import LogAnalyzer
from player import Player
from interpolator import OnedayAccumulator

app = FastAPI()

def get_buffer() -> BytesIO:
    with BytesIO() as buf:
        yield buf

class LogUsecase:
    def __init__(self):
        self.logs: dict[datetime.date, Log] = {}
        for logfile in Path(config.log_directory()).iterdir():
            _date = datetime.date.fromisoformat(logfile.name[4:-4])
            self.logs[_date] = Logger.load_logfile(logfile)
    # singleton
    def __call__(self):
        return self
    def _plot_xdate(self, xs: list[datetime.datetime], ys: list[float], buffer: BytesIO):
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(xs, ys)
        ax.minorticks_on()
        ax.grid(alpha=0.8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        # free
        plt.close(fig)
    def _plot_oneday(self, xs: list[datetime.timedelta], ys: list[float], buffer: BytesIO):
        fake = datetime.datetime(2022,1,1)
        xs = [fake + t for t in xs]
        self._plot_xdate(xs, ys, buffer)
    def plot_headcounts_of_date(self, _date: datetime.date, buffer: BytesIO):
        log = self.logs[_date]
        a = LogAnalyzer()
        times = log.get_times()
        headcounts = a.get_headcounts(log)
        self._plot_xdate(times, headcounts, buffer)
    def plot_headcounts_average(self, buffer: BytesIO):
        a = LogAnalyzer()
        acc = OnedayAccumulator()
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        res = acc.result()
        xs = list(res.keys())
        avgs = list(map(fmean, res.values()))
        self._plot_oneday(xs, avgs, buffer)
    def plot_headcounts_median(self, buffer: BytesIO):
        a = LogAnalyzer()
        acc = OnedayAccumulator()
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        res = acc.result()
        xs = list(res.keys())
        medians = list(map(median_high, res.values()))
        self._plot_oneday(xs, medians, buffer)
    def plot_headcounts_average_day_of_week(self, weekday: int, buffer: BytesIO):
        a = LogAnalyzer()
        acc = OnedayAccumulator()
        for _date, log in self.logs.items():
            if _date.weekday() != weekday:
                continue
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            acc.append(times, headcounts)
        res = acc.result()
        xs = list(res.keys())
        ys = list(map(fmean, res.values()))
        self._plot_oneday(xs, ys, buffer)
    def plot_playtime(self, id: str, buffer: BytesIO):
        p = Player("fake", id)
        a = LogAnalyzer()
        acc = OnedayAccumulator()
        for log in self.logs.values():
            times = log.get_times()
            piv = a.get_player_in_venue(log, p)
            acc.append(times, list(map(float, piv)))
        res = acc.result()
        xs = list(res.keys())
        counts = list(map(sum, res.values()))
        self._plot_oneday(xs, counts, buffer)
    def get_all_playdate(self, id: str) -> list[datetime.date]:
        p = Player("fake", id)
        ret = []
        a = LogAnalyzer()
        for _date, log in self.logs.items():
            if any(a.get_status_changed(log, p)):
                ret.append(_date)
        return ret

get_log_usecase: Callable[[], LogUsecase] = LogUsecase()


@app.get("/player/{id}/date")
async def player_date(id: str, log_usecase: LogUsecase = Depends(get_log_usecase)):
    return log_usecase.get_all_playdate(id)

@app.get("/player/{id}/time")
async def player_time(
        id: str,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    log_usecase.plot_playtime(id, buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/average")
async def headcounts_average(
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    log_usecase.plot_headcounts_average(buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/average/{weekday}")
async def headcounts_average(
        weekday: int,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    log_usecase.plot_headcounts_average_day_of_week(weekday, buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/median")
async def headcounts_median(
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    log_usecase.plot_headcounts_median(buffer)
    return StreamingResponse(buffer, media_type="image/png")

@app.get("/headcounts/{_date}")
async def headcounts_of_date(
        _date: datetime.date,
        log_usecase: LogUsecase = Depends(get_log_usecase),
        buffer = Depends(get_buffer)
    ):
    log_usecase.plot_headcounts_of_date(_date, buffer)
    return StreamingResponse(buffer, media_type="image/png")
