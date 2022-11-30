import datetime
from abc import ABC, abstractmethod
from typing import Iterator
from player import Player

class Log:
    """
    ログファイルの情報を管理
    特定の一日のデータのみを扱う
    """
    def __init__(self, data: dict[datetime.datetime, list[Player]]):
        # 時刻のリスト
        self._times: list[datetime.datetime] = sorted(data.keys())
        if len(self._times) > 0 and self._times[-1].date() != self._times[0].date():
            raise ValueError("log accepts only data in one day")
        # 時刻ごとのプレイヤーリスト
        self._logs: list[list[Player]] = [data[t] for t in self._times]
        # ログに存在する全プレイヤ―の集合
        _st = set()
        for v in data.values():
            _st.update(v)
        self._player_set: frozenset[Player] = frozenset(_st)
        # サンプルしたログの数（行数）
        self.size = len(self._times)
        # 時刻ごとにログの何番目にいるか
        self._player_positions: dict[Player, list[int | None]] = dict()
        for p in self._player_set:
            self._player_positions[p] = [None]*self.size
        for idx, t in enumerate(self._times):
            for position, p in enumerate(data[t]):
                self._player_positions[p][idx] = position
    def get_times(self) -> list[datetime.datetime]:
        #return self._times[:]
        return self._times
    def iter_logs(self) -> Iterator[list[Player]]:
        for log in self._logs:
            #yield log[:]
            yield log
    def get_players(self) -> frozenset[Player]:
        return self._player_set
    def get_player_positions(self, p: Player) -> list[int | None]:
        try:
            return self._player_positions[p][:]
        except KeyError as e:
            raise KeyError(f"player: {p} not found") from e

class ILogRepository(ABC):
    @abstractmethod
    def save_row(self, logged_at: datetime.datetime, player_list: list[Player]):
        raise NotImplementedError
    @abstractmethod
    def get_log_by_date(self, date: datetime.date) -> Log:
        raise NotImplementedError
