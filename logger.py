import time
import json
import datetime
import schedule
from pathlib import Path

import config
from log import Log, ILogRepository
from crawler import Crawler
from player import Player

class JsonRowLogRepository(ILogRepository):
    def __init__(self):
        self.log_directory = Path(config.log_directory())
    def save_row(self, logged_at: datetime.datetime, player_list: list[Player]):
        # 本来は最新のタイムスタンプより前の入力が来たらエラーにしたい
        # uowを気にしないようにするため都度openしているが書き込みは数分に一回なので問題ないはず
        path = self.log_directory / f"log_{logged_at.date().isoformat()}.txt"
        with open(path, "a") as f:
            f.write(
                json.dumps({"logged_time": logged_at.isoformat(), "log": player_list})
                + "\n"
            )
    def get_log_by_date(self, date: datetime.date) -> Log:
        path = self.log_directory / f"log_{date.isoformat()}.txt"
        data = {}
        with open(path, "r") as logfile:
            for format_string in logfile:
                fmt = json.loads(format_string)
                logged_time = datetime.datetime.fromisoformat(fmt["logged_time"])
                log = list(map(Player._make, fmt["log"]))
                data[logged_time] = log
        return Log(data)

class Logger:
    def __init__(self, repository: ILogRepository):
        self.c = Crawler()
        self.c.load_cookies()
        self.repository = repository
    def log_once(self, repository: ILogRepository, take=10):
        log = self.c.get_log()
        log = log[:take]
        now = datetime.datetime.now()
        repository.save_row(now, log)
    def main_loop(self, start_time: datetime.datetime, end_time: datetime.datetime):
        assert start_time <= end_time
        try:
            schedule.every(8).minutes.until(end_time).do(
                self.log_once, repository=self.repository
            )
            self.log_once(self.repository)
            while (now := datetime.datetime.now()) <= end_time:
                if start_time <= now:
                    schedule.run_pending()
                    time.sleep(30)
        finally:
            schedule.clear()

if __name__ == "__main__":
    logger = Logger(JsonRowLogRepository())
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today + datetime.timedelta(hours=9, minutes=30)
    end_time = today + datetime.timedelta(hours=24)
    logger.main_loop(start_time, end_time)