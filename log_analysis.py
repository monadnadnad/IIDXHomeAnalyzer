# DomainS
import datetime
from itertools import pairwise

from log import Log
from player import Player

class LogAnalyzer:
    """
    ログから情報を構築する
    """
    def __init__(
            self,
            max_stable_time: datetime.timedelta = datetime.timedelta(minutes=30),
            max_time_between_reentry: datetime.timedelta = datetime.timedelta(hours=1)
        ):
        # この時間だけは状態が変わらなくても入店していると判断する
        self.MAX_STABLE_TIME = max_stable_time
        # 再入店までに最低でもかかる時間（再入店と誤認しないための精度上げに使う）
        self.MAX_TIME_BETWEEN_REENTRY = max_time_between_reentry
    def get_status_changed(self, log: Log, p: Player) -> list[bool]:
        """
        プレイした事が確定したタイミングを記録したリストを返す
        """
        positions = log.get_player_positions(p)
        ret = [False]*len(positions)
        for i, (log1, log2) in enumerate(pairwise(log.iter_logs())):
            p1 = positions[i]
            p2 = positions[i+1]
            # 前のログでpよりも左にいたプレイヤー
            p1 = p1 if p1 != None else len(log1)
            log1_left = set(log1[:p1])
            # 後のログでpよりも右にいたプレイヤー
            p2 = p2 if p2 != None else len(log2)
            log2_right = set(log2[p2+1:])
            # 新規入店を考慮しない場合の判定
            if log1_left.intersection(log2_right):
                ret[i] = True
            ## 以降の新規入店プレイヤーを抜かした場合の判定は失敗しやすいためdeprecate
            # log1_right = set(log1[p1+1:])
            ## 前のログで左にいたか、誰かが消えてログに現れた過去のプレイヤーか、新規プレイヤー
            #left_old_new_players = log2_right.difference(log1_right)
            ## 前にいたプレイヤーを抜かしたらプレイ判定
            #if len(left_old_new_players.intersection(log1_left)) != 0:
            #    ret[i] = True
            #    continue
            ## 新規プレイヤーを抜かしていればプレイ判定
            #both_right_indices = list(map(log2.index, log2_right.intersection(log1_right)))
            #for q in left_old_new_players:
            #    q_idx = log2.index(q)
            #    # 一人でもログ右側の共通部分を抜いているプレイヤーは新規プレイヤーと判定する
            #    if any(q_idx < idx for idx in both_right_indices):
            #        ret[i] = True
            #        break
        return ret
    def get_player_in_venue(self, log: Log, p: Player) -> list[bool]:
        """
        プレイヤーがその時間にいた可能性をboolで表現したリスト
        """
        # 入店の確定位置を探す、最後の確定位置以降は退店しているとみなせる
        status_changed = self.get_status_changed(log, p)
        N = len(status_changed)
        ret = [False]*N
        # 推定退店時間のindex
        last = None
        for i in range(N-1, 0, -1):
            if status_changed[i-1]:
                last = i
                break
        # 入店確定位置がないためプレイしていないと判定
        if last == None:
            return ret
        # 尺取り法で入店確定位置から閾値時間だけ入店していると判定する
        l, r = 0, 1
        times = log.get_times()
        while r <= N:
            if status_changed[l]:
                while r < N and times[r-1] - times[l] <= self.MAX_STABLE_TIME:
                    ret[r-1] = True
                    r += 1
            l += 1
            if l == r:
                r += 1
        # 再入店の誤認を修正する（開店時間から数分後入店のプレイヤーについて失敗するバグがあるかもしれない）
        l = status_changed.index(True)
        r = l + 1
        while r <= N:
            if ret[l] == False:
                # 退店判定の区間[l,r)を求める
                while r < N and ret[r] == False:
                    r += 1
                # 退店判定から入店判定になる時間までがある程度短ければ間を入店判定で埋める
                if times[r-1] - times[l] <= self.MAX_TIME_BETWEEN_REENTRY:
                    for i in range(l, r):
                        ret[i] = True
                l = r
            else:
                l += 1
            if l == r:
                r += 1
        # 最後の確定位置（推定退店時間）から伸ばしてしまった分を削る
        for i in range(last + 1, N):
            ret[i] = False
        return ret
    def get_players_over_time(self, log: Log) -> list[set[Player]]:
        """
        各時間にいた可能性のあるプレイヤーの集合のリスト
        """
        ps = log.get_players()
        player_in_venue = {}
        for p in ps:
            player_in_venue[p] = self.get_player_in_venue(log, p)
        return [
            set(p for p in ps if player_in_venue[p][i])
            for i in range(log.size)
        ]
    def get_headcounts(self, log: Log) -> list[int]:
        playersets = self.get_players_over_time(log)
        headcounts = [len(ps) for ps in playersets]
        return headcounts
