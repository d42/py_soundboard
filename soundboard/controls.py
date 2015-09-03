import abc
import threading
import logging
import sys
from time import sleep

import sdl2
import sdl2.ext
import six

from soundboard.utils import init_sdl
from soundboard import constants
from collections import namedtuple


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('controls')


event_tuple = namedtuple('event_tuple', 'button state')


class ControllerException(Exception):
    pass


@six.add_metaclass(abc.ABCMeta)
class InputInterface:

    def on_event(self, callback):
        self.callback = callback


class RawSDLJoystick(InputInterface):
    def __init__(self, joystick_id):
        sdl2.SDL_SetHint(sdl2.SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, b"1")

        self.events = []
        init_sdl()

        self.joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not self.joystick:
            raise ControllerException("Joystick %d could not be initialized" %
                                      joystick_id)

    def get_buttons(self):
        events = self.events
        self.events = []
        return events

    def wait(self):
        while not self.events:
            sleep(0.1)
            self._pump_events()

    def _pump_events(self):

        joystick_events = {sdl2.SDL_JOYBUTTONUP: 'UP',
                           sdl2.SDL_JOYBUTTONDOWN: 'DOWN'}

        def pump(event):
            type = joystick_events.get(event.type, None)
            if not type:
                return
            button = self._translate(event.jbutton.button)
            t = event_tuple(button, type == 'DOWN')
            logger.info("event %s", t)
            self.events.append(t)

        for e in sdl2.ext.get_events():
            pump(e)

        return bool(self.events)

    def _translate(self, physical_button):
        button_id = constants.physical_mapping[physical_button]
        return button_id


class Joystick(InputInterface):

    def __init__(self, joystick_id=0, buffer_msec=20):
        self.buffer_msec = buffer_msec/100
        self.raw_joystick = RawSDLJoystick(joystick_id)
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
