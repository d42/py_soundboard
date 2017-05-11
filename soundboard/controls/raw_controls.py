import time
import logging

import sdl2
import sdl2.ext
import evdev
import evdev.ecodes

from soundboard.exceptions import ControllerException
from soundboard.utils import init_sdl
from soundboard.types import event_tuple, timestamped_event_tuple
from soundboard.enums import EventTypes

logger = logging.getLogger('controls.raw')


class BaseRawJoystick(object):

    def __init__(self, mapping=None, offset=0):
        self.mapping = mapping if mapping else dict()
        self.scancode_offset = offset
        self.events = list()
        self.pushed = set()

    @property
    def isempty(self):
        return len(self.events) == 0

    def pop_events(self):
        events = self.events
        self.events = []
        return events

    def process(self, events, preprocess_func):
        """ :type events: list(EventTypes)"""
        """ :type preprocess: func -> event_tuple"""
        if preprocess_func:
            events = [preprocess_func(e) for e in events]

        events = [self.translate(e) for e in events]

        self.events.extend(events)

    def translate(self, event):
        """:type event: event_tuple"""
        def shift(button):
            new_button = button - self.scancode_offset
            logger.debug("shift %d -> %d", button, new_button)
            return new_button

        def remap(button):
            new_button = self.mapping.get(button, button)
            logger.debug("remap %d -> %d", button, new_button)
            return new_button

        button, type = event
        new_button = remap(shift(button))
        return event_tuple(new_button, type)


class RawQueueJoystick(BaseRawJoystick):
    def __init__(self, queue, mapping=None, offset=0):
        ''':type queue: Queue.Queue'''
        super(RawQueueJoystick, self).__init__(mapping, offset)
        self.queue = queue

    def update(self):
        pushed = set()
        while not self.queue.empty():
            button_id = self.queue.get_nowait()
            if button_id in pushed: continue
            pushed.add(button_id)
            self.events.append(event_tuple(button_id, EventTypes.push))

        released_buttons = self.pushed - pushed
        for button_id in released_buttons:
            self.events.append(event_tuple(button_id, EventTypes.release))

        self.pushed = (self.pushed | pushed) - released_buttons


class RawSDLJoystick(BaseRawJoystick):
    JOYSTICK_EVENTS = (sdl2.SDL_JOYBUTTONUP, sdl2.SDL_JOYBUTTONDOWN)

    def __init__(self, joystick_id, mapping=None, offset=0):
        super(RawSDLJoystick, self).__init__(mapping, offset)
        init_sdl()
        self.joystick = self.open_joystick(joystick_id)

    @staticmethod
    def open_joystick(joystick_id):
        joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not joystick:
            text = "Joystick %d could not be initialized" % joystick_id
            raise ControllerException(text)
        return joystick

    def update(self):

        def to_tuple(event):
            button = event.button.jbutton
            type = EventTypes.from_sdl(event.type)
            return event_tuple(button, type)

        events = []
        all_events = sdl2.ext.get_events()
        events = [e for e in all_events if e.type in self.JOYSTICK_EVENTS]
        self.process(events, preprocess_func=to_tuple)


class RawEVDEVJoystick(BaseRawJoystick):
    JOYSTICK_EVENTS = [evdev.ecodes.EV_KEY]

    def __init__(self, device_path, mapping=None, offset=0):
        super(RawEVDEVJoystick, self).__init__(mapping, offset)
        if 'input/event' not in device_path:
            self.joystick = self.path_from_devicename(device_path)
        else:
            self.joystick = evdev.InputDevice(device_path)


    def device_from_name(self, device_name):
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            if dev.name == device_name:
                return dev
        raise ValueError("unknown device %s" % device_name)


    def _read(self):
        try:
            ebin = list(self.joystick.read())
        except:
            return []
        return ebin

    def update(self):
        def to_tuple(event):
            type = EventTypes(event.value)
            button = event.code
            return event_tuple(button, type)

        events = [e for e in self._read() if e.type in self.JOYSTICK_EVENTS]
        self.process(events, to_tuple)

handlers = {
    'sdl': RawSDLJoystick,
    'evdev': RawEVDEVJoystick,
    'queue': RawQueueJoystick,
}
