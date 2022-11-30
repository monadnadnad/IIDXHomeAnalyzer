import datetime

from interpolator import OnedayAverage, OnedayMax, OnedayMedian, OnedaySum
from log import Log
from logger import JsonRowLogRepository, ScheduleLoggerSettings
from log_analysis import LogAnalyzer
from player import Player

settings = ScheduleLoggerSettings()

class LogUsecase:
    def __init__(self):
        self.logs: dict[datetime.date, Log] = {}
        jsonrows = JsonRowLogRepository()
        for logfile in settings.log_directory.iterdir():
            date = datetime.date.fromisoformat(logfile.stem[4:])
            self.logs[date] = jsonrows.get_log_by_date(date)
    def get_headcounts_of_date(self, date: datetime.date) -> dict[datetime.datetime, float]:
        a = LogAnalyzer()
        log = self.logs[date]
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
