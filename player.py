from typing import NamedTuple

class Player(NamedTuple):
    name: str
    id: str
    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Player):
            return self.id == __o.id
        return NotImplemented