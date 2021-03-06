import logging
import time
from itertools import chain

from .raw_controls import HANDLERS
from .raw_controls import BaseRawJoystick
from soundboard.enums import EventTypes
from soundboard.exceptions import ControllerException
from soundboard.types import states_tuple
from typing import Any, List, Set
from ..defines import DEFAULT_HANDLER


logger = logging.getLogger("soundboard.controls")


class Joystick:
    callback = None

    def __init__(
            self,
            joystick_source: Any,
            backend: str = DEFAULT_HANDLER,
            buffer_msec: int = 25,
            offset: int = 0,
    ):

        self.raw_joystick = self.open_joystick(joystick_source, backend, offset)

        self.held: Set[int] = set()
        self.released: Set[int] = set()

    @staticmethod
    def open_joystick(joystick_source, backend, offset):
        backend_handler = HANDLERS.get(backend)
        if not backend_handler:
            raise ControllerException("unknown type %s" % backend)
        return backend_handler(joystick_source, offset=offset)

    def poll_raw(self):
        self.raw_joystick.update()
        return self.raw_joystick.pop_events()

    @property
    def pending(self):
        return not self.raw_joystick.isempty


class ControlHandler:
    def __init__(self):
        self.controllers: List[BaseRawJoystick] = []
        self.held = set()
        self.released = set()

    def register_controler(self, controller):
        self.controllers.append(controller)

    @property
    def pending(self):
        return any(j.pending for j in self.controllers)

    def poll_raw(self):
        return list(chain.from_iterable(c.poll_raw() for c in self.controllers))

    def poll_buffered(self, buffer_time: float) -> states_tuple:
        pushed: Set[int] = set()
        released: Set[int] = set()
        break_on = 0

        rounds = max(int(buffer_time / 0.01), 1)

        for i in range(rounds):
            time.sleep(0.01)
            events = self.poll_raw()
            if not any([events, pushed, released]):
                break
            state = self.to_state(events)
            released |= state.released
            pushed |= state.pushed
            if state.released:
                if not break_on:
                    break_on = i + 4
            if break_on and break_on == i:
                break

        clicks = pushed & released
        self.held |= pushed - released
        self.held -= released

        self.released |= released
        released_now = self.released - pushed
        self.released -= released_now

        return states_tuple(*[frozenset(f) for f in [clicks, released_now, self.held]])

    @staticmethod
    def to_states_sets(events):
        containers = {event_type: set() for event_type in EventTypes}
        for (button, state) in events:
            containers[state].add(button)

        pushed = containers[EventTypes.push]
        released = containers[EventTypes.release]
        held = containers[EventTypes.hold]
        return pushed, released, held

    @classmethod
    def to_state(cls, events):
        pushed, released, held = cls.to_states_sets(events)
        return states_tuple(*map(frozenset, [pushed, released, held]))
