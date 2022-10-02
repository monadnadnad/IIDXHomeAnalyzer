# Domain
from typing import NamedTuple

#Player = namedtuple("Player", ["name", "id"])
class Player(NamedTuple):
    name: str
    id: str
