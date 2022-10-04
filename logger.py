import time
import json
import datetime
import schedule
from io import TextIOWrapper
from typing import NamedTuple
from pathlib import Path

import config
from log import Log
from crawler import Crawler
from player import Player

class LogRow(NamedTuple):
    """
    ログの行のフォーマットを定義
    """
    logged_time: datetime.datetime
    log: list[Player]
    def format(self) -> str:
        return json.dumps({
            "logged_time": self.logged_time.isoformat(),
            "log": self.log
        })
    @classmethod
    def fromformat(cls, format_string: str):
        fmt = json.loads(format_string)
        logged_time = datetime.datetime.fromisoformat(fmt["logged_time"])
        log = list(map(Player._make, fmt["log"]))
        return cls(logged_time, log)

class Logger:
    def __init__(self):
        self.c = Crawler()
        self.c.load_cookies()
    def log_once(self, f: TextIOWrapper, take=10):
        log = self.c.get_log()
        log = log[:take]
        now = datetime.datetime.now()
        # 呼び出しはかなり少ないのでflush
        f.write(LogRow(now, log).format()+"\n")
        f.flush()
    def main_loop(self):
        today = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        #start_time = today + datetime.timedelta(hours=9, minutes=30)
        limit_time = today + datetime.timedelta(hours=24)
        path = Path(config.log_directory()) / f"log_{today.date().isoformat()}.txt"
        with open(path, "a") as f:
            schedule.every(8).minutes.until(limit_time).do(self.log_once, f=f)
            #schedule.every(30).seconds.until(limit_time).do(self.log_once, f=f)
            try:
                while datetime.datetime.now() <= limit_time:
                    schedule.run_pending()
                    time.sleep(30)
            finally:
                schedule.clear()
    @staticmethod
    def load_logfile(log_path: str) -> Log:
        data = {}
        with open(log_path, "r") as f:
            for line in f:
                logrow = LogRow.fromformat(line)
                data[logrow.logged_time] = logrow.log
        log = Log(data)
        return log

if __name__ == "__main__":
    logger = Logger()
    logger.main_loop()