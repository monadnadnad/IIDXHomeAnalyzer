from typing import NamedTuple

class Player(NamedTuple):
    name: str
    id: str
    def __hash__(self) -> int:
        return hash(id)
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Player):
            return self.id == __o.id
        return NotImplemented