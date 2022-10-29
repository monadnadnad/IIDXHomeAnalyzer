import pytest
from pytest_mock import MockerFixture
import datetime

from log import Log, ILogRepository
from player import Player
from logger import ScheduleLogger

class InMemLogRepository(ILogRepository):
    def __init__(self):
        self.data: dict[datetime.datetime, list[Player]] = {}
    def save_row(self, logged_at: datetime.datetime, player_list: list[Player]):
        self.data[logged_at] = player_list
    def get_log_by_date(self, date: datetime.date) -> Log:
        pass

@pytest.fixture
def repository():
    return InMemLogRepository()
@pytest.fixture
def players():
    return [Player("test1", "1111-1111"), Player("test2", "2222-2222")]
@pytest.fixture
def logger(
        mocker: MockerFixture,
        repository: InMemLogRepository,
        players: list[Player]
    ):
    c = mocker.MagicMock()
    mocker.patch.object(c, "get_log", return_value=players)
    return ScheduleLogger(c, repository)

def test_logger_can_log_once(logger: ScheduleLogger, repository, players):
    logger.log_once()
    vs = list(repository.data.values())
    assert len(vs) == 1
    v = vs[0]
    assert len(v) == len(players)
    assert all(v[i] == players[i] for i in range(len(v)))
