import logging
import time

import evdev.ecodes
import sdl2.ext

from soundboard.enums import EventTypes
from soundboard.exceptions import ControllerException
from soundboard.types import event_tuple
from soundboard.utils import init_sdl

logger = logging.getLogger('controls.raw')


class BaseRawJoystick():

    def __init__(self, mapping=None, offset=0):
        self.mapping = mapping if mapping else dict()
        self.scancode_offset = offset
        self.events = list()

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
            logger.debug('shift %d -> %d', button, new_button)
            return new_button

        def remap(button):
            new_button = self.mapping.get(button, button)
            logger.debug('remap %d -> %d', button, new_button)
            return new_button

        button, type = event
        new_button = remap(shift(button))
        return event_tuple(new_button, type)


class RawQueueJoystick(BaseRawJoystick):
    def __init__(self, queue, mapping=None, offset=0):
        ''':type queue: Queue.Queue'''
        super().__init__(mapping, offset)
        self.queue = queue
        self.keys_held = dict()
        self.last_key_at = 0

    def update(self):
        while not self.queue.empty():
            button_id, event_id = self.queue.get_nowait()
            event = EventTypes(event_id)
            logging.info('%s %s', button_id, event)
            self.events.append(event_tuple(button_id, event))
            if event == EventTypes.push:
                timestamp = time.time()
                self.keys_held[button_id] = timestamp
                self.last_key_at = timestamp

        self.reset_stale()

    def reset_stale(self):
        if not self.last_key_at:
            return
        if time.time() - self.last_key_at < 30:
            return

        for btn_id, timestamp in self.keys_held.items():
            if not timestamp:
                continue
            event = event_tuple(btn_id, EventTypes.release)
            self.events.append(event)
            self.keys_held[btn_id] = False


class RawSDLJoystick(BaseRawJoystick):

    @property
    def JOYSTICK_EVENTS(self):
        return (sdl2.SDL_JOYBUTTONUP, sdl2.SDL_JOYBUTTONDOWN)

    def __init__(self, joystick_id, mapping=None, offset=0):
        super().__init__(mapping, offset)
        init_sdl()
        self.joystick = self.open_joystick(joystick_id)

    @staticmethod
    def open_joystick(joystick_id):
        joystick = sdl2.SDL_JoystickOpen(joystick_id)
        if not joystick:
            text = 'Joystick %d could not be initialized' % joystick_id
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

    @property
    def JOYSTICK_EVENTS(self):
        return [evdev.ecodes.EV_KEY]  # noqa

    def __init__(self, device_path, mapping=None, offset=0):
        super().__init__(mapping, offset)
        self.device_path = device_path
        self.setup_device(self.device_path)

    def setup_device(self, device_path):
        is_name = 'input/event' not in device_path
        func = self.device_from_name if is_name else evdev.InputDevice
        try:
            self.joystick = func(device_path)
            self.joystick.grab()
        except Exception as e:
            logger.warning(e)

    def device_from_name(self, device_name):
        for path in evdev.list_devices():
            dev = evdev.InputDevice(path)
            if dev.name == device_name:
                return dev
        raise ValueError('unknown device %s' % device_name)

    def _read(self):
        try:
            return list(self.joystick.read())
        except OSError:
            self.setup_device(self.device_path)
            return []
        except Exception:
            return []

    def update(self):
        def to_tuple(event):
            type = EventTypes(event.value)
            button = event.code
            return event_tuple(button, type)

        events = [e for e in self._read() if e.type in self.JOYSTICK_EVENTS]
        self.process(events, to_tuple)


HANDLERS = {
    'sdl': RawSDLJoystick,
    'evdev': RawEVDEVJoystick,
    'queue': RawQueueJoystick,
}
