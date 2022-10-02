# Infra
import time
import datetime
import schedule
from io import TextIOWrapper
from pathlib import Path

import config
from log import LogRow
from crawler import Crawler

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

if __name__ == "__main__":
    logger = Logger()
    logger.main_loop()