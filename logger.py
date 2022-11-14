import traceback
import time
import json
import datetime
import schedule
from pydantic import DirectoryPath

from config import Settings
from log import Log, ILogRepository
from crawler import Crawler
from player import Player

settings = Settings()

class JsonRowLogRepository(ILogRepository):
    def __init__(self):
        self.log_directory: DirectoryPath = settings.log_directory
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

class ScheduleLogger:
    def __init__(self, c: Crawler, repository: ILogRepository):
        self.crawler = c
        self.repository = repository
    def log_once(self, take=10):
        log = self.crawler.get_log()
        now = datetime.datetime.now()
        self.repository.save_row(now, log[:take])
    def main_loop(self, start_time: datetime.datetime, end_time: datetime.datetime):
        assert start_time <= end_time
        try:
            schedule.every(8).minutes.until(end_time).do(self.log_once)
            if start_time <= datetime.datetime.now():
                self.log_once()
            while (now := datetime.datetime.now()) <= end_time:
                try:
                    if start_time <= now:
                        schedule.run_pending()
                    time.sleep(30)
                except KeyboardInterrupt:
                    traceback.print_exc()
                    break
                except ConnectionError:
                    traceback.print_exc()
                    time.sleep(30)
        finally:
            self.crawler.save_cookies()
            schedule.clear()

if __name__ == "__main__":
    c = Crawler()
    c.load_cookies()
    logger = ScheduleLogger(c, JsonRowLogRepository())
    today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today + datetime.timedelta(hours=9, minutes=30)
    end_time = today + datetime.timedelta(hours=24)
    logger.main_loop(start_time, end_time)