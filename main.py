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
from statistics import median_high
from scipy import interpolate

import config
from log import Log
from logger import Logger
from log_analysis import LogAnalyzer
from player import Player

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
    def _fake_timeline(self):
        tick = 5
        fake = datetime.datetime(2022,1,1,0,0,0)
        timeline = [fake + i*datetime.timedelta(minutes=tick) for i in range(24*60//tick + 1)]
        return timeline
    def _to_fake_timeline(self, times: list[datetime.datetime]):
        fake = datetime.datetime(2022,1,1,0,0,0)
        new_times = [fake + (t-datetime.datetime.combine(t.date(), datetime.time.min)) for t in times]
        return new_times
    def _interpolate_xdate(
            self,
            x: list[datetime.datetime],
            y: list[float],
            x_new: list[datetime.datetime]
        ) -> list[float]:
        _x = mdates.date2num(x)
        f = interpolate.interp1d(_x, y, kind="nearest", bounds_error=False, fill_value=0)
        _x_new = mdates.date2num(x_new)
        y_new = f(_x_new)
        return y_new
    def _plot_one_xdate(self, xs: list[datetime.datetime], ys: list[float], buffer: BytesIO):
        fig, ax = plt.subplots(figsize=(8,4))
        ax.plot(xs, ys)
        ax.minorticks_on()
        ax.grid(alpha=0.8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        # free
        plt.close(fig)
    def plot_headcounts_of_date(self, _date: datetime.date, buffer: BytesIO):
        log = self.logs[_date]
        a = LogAnalyzer()
        times = log.get_times()
        headcounts = a.get_headcounts(log)
        self._plot_one_xdate(times, headcounts, buffer)
    def plot_headcounts_average(self, buffer: BytesIO):
        timeline = self._fake_timeline()
        a = LogAnalyzer()
        N = len(timeline)
        total = [0]*N
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            xs = self._to_fake_timeline(times)
            new_hc = self._interpolate_xdate(xs, headcounts, timeline)
            for i in range(N):
                total[i] += new_hc[i]
        L = len(self.logs)
        assert L != 0
        for i in range(N):
            total[i] /= L
        self._plot_one_xdate(timeline, total, buffer)
    def plot_headcounts_median(self, buffer: BytesIO):
        timeline = self._fake_timeline()
        a = LogAnalyzer()
        N = len(timeline)
        all_headcounts = [[] for _ in range(N)]
        for log in self.logs.values():
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            xs = self._to_fake_timeline(times)
            hc_new = self._interpolate_xdate(xs, headcounts, timeline)
            for i in range(N):
                all_headcounts[i].append(hc_new[i])
        medians = [median_high(hc) for hc in all_headcounts]
        self._plot_one_xdate(timeline, medians, buffer)
    def plot_headcounts_average_day_of_week(self, weekday: int, buffer: BytesIO):
        timeline = self._fake_timeline()
        a = LogAnalyzer()
        N = len(timeline)
        total = [0]*N
        L = 0
        for _date, log in self.logs.items():
            if _date.weekday() != weekday:
                continue
            L += 1
            times = log.get_times()
            headcounts = a.get_headcounts(log)
            xs = self._to_fake_timeline(times)
            hc_new = self._interpolate_xdate(xs, headcounts, timeline)
            for i in range(N):
                total[i] += hc_new[i]
        assert L != 0
        for i in range(N):
            total[i] /= L
        self._plot_one_xdate(timeline, total, buffer)
    def plot_playtime(self, id: str, buffer: BytesIO):
        p = Player("fake", id)
        timeline = self._fake_timeline()
        N = len(timeline)
        counts = [0]*N
        a = LogAnalyzer()
        for log in self.logs.values():
            times = log.get_times()
            piv = a.get_player_in_venue(log, p)
            xs = self._to_fake_timeline(times)
            new_piv = self._interpolate_xdate(xs, list(map(float, piv)), timeline)
            for i in range(N):
                counts[i] += new_piv[i]
        self._plot_one_xdate(timeline, counts, buffer)
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
