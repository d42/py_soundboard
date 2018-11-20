from __future__ import division

import logging
import time
from itertools import chain


from soundboard.enums import EventTypes
from soundboard.types import states_tuple
from soundboard.exceptions import ControllerException

from .raw_controls import HANDLERS

logger = logging.getLogger('controls')


class Joystick():
    callback = None

    def __init__(self, joystick_id, backend='evdev',
                 buffer_msec=25, mapping=None, offset=0):

        self.raw_joystick = self.open_joystick(
            joystick_id, backend, mapping, offset)

        self.held = set()
        self.released = set()

    @staticmethod
    def open_joystick(joystick_id, backend, mapping, offset):
        backend = HANDLERS.get(backend)
        if not backend:
            ControllerException("unknown type %s" % backend)
        return backend(joystick_id, mapping=mapping, offset=offset)

    def poll_raw(self):
        self.raw_joystick.update()
        return self.raw_joystick.pop_events()

    @property
    def pending(self):
        return not self.raw_joystick.isempty


class ControlHandler():
    def __init__(self):
        self.controllers = []
        self.held = set()
        self.released = set()

    def register_controler(self, controller):
        self.controllers.append(controller)

    @property
    def pending(self):
        return any(j.pending for j in self.controllers)

    def poll_raw(self):
        return list(chain.from_iterable(c.poll_raw() for c in self.controllers))

    def poll_buffered(self, buffer_time):
        events = self.poll_raw()
        if events or self.held:
            time.sleep(buffer_time)
            events.extend(self.poll_raw())
        return self.postprocess(events)

    def postprocess(self, events):  # TODO: this is cancer :3

        pushed, released, held = self.to_states_sets(events)
        self.held |= pushed
        self.held -= released
        self.released |= released

        held |= self.held
        pushed -= held

        released |= self.released
        released -= pushed
        self.released -= released

        return states_tuple(*map(frozenset, [pushed, released, held]))

    @staticmethod
    def to_states_sets(events):
        containers = {event_type: set() for event_type in EventTypes}
        for (button, state) in events:
            containers[state].add(button)

        pushed = containers[EventTypes.push]
        released = containers[EventTypes.release]
        held = containers[EventTypes.hold]
        return pushed, released, held
