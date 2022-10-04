import datetime

from player import Player

class Log:
    """
    ログファイルの情報を管理
    """
    def __init__(self, data: dict[datetime.datetime, list[Player]]):
        # 時刻ごとのプレイヤーリスト
        self.data: dict[datetime.datetime, list[Player]] = data
        # 全プレイヤ―の集合
        self.player_set: set[Player] = set()
        for t in data:
            self.player_set.update(data[t])
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
