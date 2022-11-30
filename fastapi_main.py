import datetime
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from typing import Callable

from log_usecase import LogUsecase

# GUIを使わない
matplotlib.use("Agg")

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

class SingletonLogUsecase(LogUsecase):
    def __call__(self):
        return self

get_log_usecase: Callable[[], LogUsecase] = SingletonLogUsecase()


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
