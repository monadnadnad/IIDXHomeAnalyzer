# Domain
import json
import datetime
from typing import NamedTuple

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

class Log:
    """
    ログファイルの情報を管理
    """
    def __init__(self, log_path: str):
        self.data: dict[datetime.datetime, list[Player]] = {}
        self.player_set: set[Player] = set()
        # 本来Infraに依存したくない
        with open(log_path, "r") as f:
            for line in f:
                logrow = LogRow.fromformat(line)
                logged_time = logrow.logged_time
                log = logrow.log
                self.data[logged_time] = log
                for p in log:
                    self.player_set.add(p)
        # 時刻のリスト
        self.times: list[datetime.datetime] = list(self.data.keys())
        # 時刻ごとにログの何番目にいるか
        self.player_positions: dict[Player, list[int | None]] = dict()
        for p in self.player_set:
            self.player_positions[p] = [None]*len(self.times)
        for idx, t in enumerate(self.times):
            for position, p in enumerate(self.data[t]):
                self.player_positions[p][idx] = position
    def get_times(self) -> list[datetime.datetime]:
        return self.times
    def get_players(self) -> set[Player]:
        return self.player_set
    def get_log_at_time(self, t: datetime.datetime) -> list[Player]:
        return self.data[t]
    def get_player_positions(self, p: Player) -> list[int | None]:
        # clone
        return self.player_positions[p][:]
