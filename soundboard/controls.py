import abc
import threading
import logging
import sys
from time import sleep

import sdl2
import sdl2.ext
import six
import evdev

from soundboard import constants
from soundboard.utils import init_sdl
from collections import namedtuple


logging.basicConfig(stream=sys.stdout)
logger = logging.getLogger('controls')


event_tuple = namedtuple('event_tuple', 'button state')


class ControllerException(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class InputInterface:

    def on_event(self, callback):
        self.callback = callback


class BaseRawJoystick:

    def get_buttons(self):
        events = self.events
        self.events = []
        return events

    def wait(self):
        while not self.events:
            sleep(0.1)
            self._pump_events()

    def pump(self, events):
        for (button, type) in events:
            button = self._translate(button)
            if type not in ('UP', 'DOWN', 'HOLD'):
                raise Exception("Unknown event type %s" % type)

            t = event_tuple(button, type)
            logger.info("event %s", t)
            self.events.append(t)

    def _translate(self, physical_button):
        if self._offset:
            physical_button -= self._offset

        if self._mapping:
            return self._mapping[physical_button]
        else:
            return physical_button


class RawSDLJoystick(InputInterface, BaseRawJoystick):
    _mapping = None

    def __init__(self, joystick_id, mapping=None, offset=0):
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")

        self._mapping = mapping
        self._offset = offset

        self.events = []
        self.previous_events = []
        init_sdl()

        self.joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not self.joystick:
            raise ControllerException("Joystick %d could not be initialized" %
                                      joystick_id)

    def _pump_events(self):

        DOWN = sdl2.SDL_JOYBUTTONDOWN
        UP = sdl2.SDL_JOYBUTTONUP

        types = {DOWN: 'DOWN', UP: 'UP'}

        events = []
        for event in sdl2.ext.get_events():
            if event.type not in types: continue

            button = event.button.jbutton
            type = ('HOLD' if type == DOWN and button in self.previous_events
                    else types[type])
            events.append((button, type))

        self.pump(events)
        return bool(self.events)


class RawEVDEVJoystick(InputInterface, BaseRawJoystick):
    def __init__(self, device_path, mapping=None, offset=0):
        self._mapping = mapping
        self._offset = offset
        self.events = []
        self.joystick = evdev.InputDevice(device_path)

    def _pump_events(self):

        events = []
        while True:
            event = self.joystick.read_one()
            if not event: break
            if event.type != evdev.ecodes.EV_KEY:
                continue

            button_off = getattr(event, 'scancode', event.code)
            button = button_off # - constants.evdev_button_offset

            if hasattr(event, 'value'):
                type = {0: 'UP', 1: 'DOWN', 2: 'HOLD'}[event.value]
            else:
                if event.key_down:
                    type = 'DOWN'
                elif event.key_up:
                    type = 'UP'
                else:
                    raise Exception("wtf bbq %s", event)

            events.append((button, type))

            self.pump(events)


class Joystick(InputInterface):

    def __init__(self, joystick_id, buffer_msec=20, mapping=None, offset=0):
        self.buffer_msec = buffer_msec/100

        self.raw_joystick = RawEVDEVJoystick(joystick_id,
                                             mapping=mapping,
                                             offset=offset)

        t = threading.Thread(target=self._poll_events)
        t.start()

    def _poll_events(self):
        while True:
            self.raw_joystick.wait()
            sleep(self.buffer_msec)
            self.create_event(self.raw_joystick.get_buttons())

    def create_event(self, buttons):
        if self.callback:
            self.callback(buttons)

    def set_callback(self, callback):
        self.callback = callback
    pass


class DumbButton(InputInterface):

    def __init__(self, buttons=(1, 2, 3), interval=5):
        self.callback = None

        def timer_function():
            self.create_event(buttons)
            self.timer = threading.Timer(interval, timer_function)
            self.timer.start()

        timer_function()

    def create_event(self, buttons):
        if self.callback:
            self.callback(buttons)

    def on_event(self, callback):
        self.callback = callback
