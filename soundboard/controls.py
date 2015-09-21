import abc
import threading
import logging
import sys
from time import sleep
from enum import Enum
from functools import reduce

import sdl2
import sdl2.ext
import six
import evdev

from soundboard.utils import init_sdl
from collections import namedtuple, defaultdict


logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger('controls')


event_tuple = namedtuple('event_tuple', 'button state')
states_tuple = namedtuple('events_change_tuple', 'pushed released held')


class EventTypes(Enum):
    release = 0
    push = 1
    hold = 2

    @classmethod
    def from_sdl(cls, sdl_event):
        sdl_event_types = {
            sdl2.SDL_JOYBUTTONDOWN: cls.push,
            sdl2.SDL_JOYBUTTONUP:  cls.release
        }
        return sdl_event_types[sdl_event]


class ControllerException(Exception):
    pass


class BaseRawJoystick:

    def __init__(self, mapping, offset):
        self._mapping = mapping
        self._offset = offset
        self.events = list()

    def get_events(self):
        events = self.events
        self.events = list()
        return events

    def wait(self):
        while not self.events:
            sleep(0.1)
            self._pump_events()

    def pump(self, events):
        """ :type events: list(EventTypes)"""
        for (button, type) in events:
            button = self._translate(button)
            t = event_tuple(button, type)
            logger.info("event %s", t)
            self.events.append(t)

    def _translate(self, physical_button):
        if self._offset:
            physical_button -= self._offset

        if self._mapping:
            return self.mapping[physical_button]
        else:
            return physical_button


class RawSDLJoystick(BaseRawJoystick):
    _listened_events = (sdl2.SDL_JOYBUTTONUP, sdl2.SDL_JOYBUTTONDOWN)

    def __init__(self, joystick_id, mapping=None, offset=0):
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")
        super(RawSDLJoystick, self).__init__(mapping, offset)
        init_sdl()

        self.joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not self.joystick:
            raise ControllerException("Joystick %d could not be initialized" %
                                      joystick_id)

    def _pump_events(self):
        events = []
        for event in sdl2.ext.get_events():
            if event.type in self._listened_events:
                events.append(self._translate_event(event))
        self.pump(events)
        return bool(self.events)

    def _translate_event(self, event):
        button = event.button.jbutton
        type = EventTypes.from_sdl(event.type)
        return event_tuple(button, type)


class RawEVDEVJoystick(BaseRawJoystick):
    def __init__(self, device_path, mapping=None, offset=0):
        super(RawEVDEVJoystick, self).__init__(mapping, offset)
        self.joystick = evdev.InputDevice(device_path)

    def _pump_events(self):

        events = []
        while True:
            event = self.joystick.read_one()
            if not event:
                break

            if event.type == evdev.ecodes.EV_KEY:
                events.append(self._pump_one_event(event))

        self.pump(events)

    def _pump_one_event(self, evdev_event):
        input_event = getattr(evdev_event, 'event', evdev_event)
        button = input_event.code
        type = EventTypes(min(input_event.value, 1)) # hack hack hack :3
        return event_tuple(button, type)


class StubJoystick:
    def __init__(self, device_path, mapping=None, offset=0):
        pass


class Joystick():
    callback = None

    def __init__(self, joystick_id, backend=RawEVDEVJoystick,
                 buffer_msec=20, mapping=None, offset=0):
        self.buffer_msec = buffer_msec/100
        self.buttons_state = defaultdict(lambda: EventTypes.release)

        self.raw_joystick = backend(
            joystick_id, mapping=mapping, offset=offset)

        t = threading.Thread(target=self._handle_new_events)
        t.start()

    def _handle_new_events(self):
        while True:
            self.raw_joystick.wait()
            sleep(self.buffer_msec)
            events = self.get_events()
            events_tuple = self.to_states_tuple(events)
            self.notify_callback(events_tuple)

    def to_states_tuple(self, events):
        containers = {EventTypes.hold: [],
                      EventTypes.push: [],
                      EventTypes.release: []}

        for (button, type) in events:
            containers[type].append(button)

        pushed = containers[EventTypes.push]
        released = containers[EventTypes.release]
        held = containers[EventTypes.hold]
        return states_tuple(pushed=pushed, released=released, held=held)

    def get_events(self):
        joystick_events = self.raw_joystick.get_events()
        events_unique = self.filter_events(joystick_events)
        events_final = self.update_held_buttons(events_unique)
        return events_final

    @staticmethod
    def filter_events(events):
        unique_events = []
        for e in events:
            if not unique_events:
                unique_events.append(e)
            elif unique_events[-1] != e:
                unique_events.append(e)
        return unique_events

    def update_held_buttons(self, events):
        buttons_final = []
        et = EventTypes

        transitions = {
                (et.release, et.push): et.push,
                (et.push, et.push): et.hold,
                (et.push, et.hold): et.hold,
                (et.hold, et.push): et.hold,
                (et.hold, et.hold): et.hold,
                (et.push, et.release): et.release,
                (et.hold, et.release): et.release,
        }

        for (button, new_state) in events:
            current_state = self.buttons_state[button]
            state = transitions[(current_state, new_state)]
            self.buttons_state[button] = state
            buttons_final.append(event_tuple(button, state))
        return buttons_final

    def notify_callback(self, events):
        if self.callback:
            self.callback(events)

    def set_callback(self, callback):
        if self.callback:
            raise ValueError("Callback already registered")
        self.callback = callback
    pass
