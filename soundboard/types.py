from typing import NamedTuple, FrozenSet, Any
from .enums import EventTypes


class event_tuple(NamedTuple):
    button: int
    type: EventTypes


class states_tuple(NamedTuple):
    pushed: FrozenSet[int]
    released: FrozenSet[int]
    held: FrozenSet[int]


class sound_state(NamedTuple):
    chunk: Any
    position: int


class api_state(NamedTuple):
    data: dict
    status: int
