from __future__ import division

import threading
import logging
import sys
from time import sleep


from .enums import EventTypes
from .types import states_tuple
from .raw_controls import handlers
from .exceptions import ControllerException


logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger('controls')


class Joystick():
    callback = None

    def __init__(self, joystick_id, backend='evdev',
                 buffer_msec=25, mapping=None, offset=0):

        self.raw_joystick = self.open_joystick(
            joystick_id, backend, mapping, offset)

        self.buffer_time = buffer_msec / 100
        self.buffer_action_time = (buffer_msec / 1.4) / 100
        self.held = set()
        self.released = set()
        self.action = False

        t = threading.Thread(target=self._event_loop)
        t.start()

    @staticmethod
    def open_joystick(joystick_id, backend, mapping, offset):
        if isinstance(backend, str) and backend in handlers:
            backend = handlers[backend]
        else:
            ControllerException("unknown type %s" % backend)
        return backend(joystick_id, mapping=mapping, offset=offset)

    def _event_loop(self):
        while True:
            sleep(self.buffer_action_time if self.action else self.buffer_time)
            self.raw_joystick.update()

            if not self.raw_joystick.isempty:
                if not self.action:
                    sleep(self.buffer_time)
                self.raw_joystick.update()

            events = self.raw_joystick.pop_events()
            events_tuple = self.postprocess(events)
            self.notify_callback(events_tuple)

    def postprocess(self, events):
        pushed, released, held = self.to_states_sets(events)
        self.held |= pushed
        self.held -= released
        self.released |= released

        held |= self.held
        pushed -= held

        released |= self.released
        released -= pushed
        self.released -= released

        self.action = bool(pushed)

        events_tuple = self.freeze_states([pushed, released, held])
        return events_tuple

    @staticmethod
    def to_states_sets(events):
        containers = {event_type: set() for event_type in EventTypes}
        for (button, state) in events:
            containers[state].add(button)

        pushed = containers[EventTypes.push]
        released = containers[EventTypes.release]
        held = containers[EventTypes.hold]
        return pushed, released, held

    @staticmethod
    def freeze_states(states):
        frozen_states = [frozenset(s) for s in states]
        return states_tuple(*frozen_states)

    def notify_callback(self, events):
        if self.callback and any(events):
            self.callback(events)

    def set_callback(self, callback):
        if self.callback:
            raise ValueError("Callback already registered")
        self.callback = callback
