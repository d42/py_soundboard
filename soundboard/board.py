from __future__ import division

import time
import logging
import traceback

from .enums import ModifierTypes
from .controls import ControlHandler
from .client_api import ApiManager

logger = logging.getLogger('board')


class Board():

    def __init__(self, settings):
        '''
        :type settings: soundboard.config.settings
        '''
        self.settings = settings

        self.api_manager = ApiManager()
        self.combinations = {}
        self.shared_online = {}
        self.control = ControlHandler()
        self.running = False
        self.active_sound_set = None

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""
        self.control.register_controler(joystick)

    def register_sound_set(self, sound_set):
        if ModifierTypes.floating not in sound_set.modifiers:
            self.register_on_keys(sound_set, sound_set.keys)
        if ModifierTypes.http in sound_set.modifiers:
            self.register_on_http(sound_set, sound_set.name)

    def register_on_http(self, sound_set, endpoint):
        self.shared_online[endpoint] = sound_set

    def register_on_keys(self, sound_set, keys):
        if keys in self.combinations:
            raise ValueError("combo %s is occupied" % list(keys))
        self.combinations[frozenset(keys)] = sound_set

    def on_buttons(self, buttons):
        """:type buttons: states_tuple"""
        logger.debug(buttons)
        pushed, held, released = buttons.pushed, buttons.held, buttons.released
        self.play_sounds(pushed, held)
        self.finish_sounds(released)

    def play_sounds(self, pushed, held):

        if held not in self.combinations:
            return

        sound_set = self.combinations[held]
        if sound_set is not self.active_sound_set:
            sound_set.on_activate()
            self.active_sound_set = sound_set

        if not pushed:
            return
        try:
            sound_set.play(pushed, prometheus=self.settings.prometheus)

        except Exception as e:
            traceback.print_exc()
            logging.critical(e)

    def finish_sounds(self, released):
        for sound_set in self.combinations.values():
            sound_set.stop(released)

    def run(self):
        self.running = True
        self.api_manager.start()

        buffers = {
            False: self.settings.button_poll_buffer/100,
            True: self.settings.button_poll_active_buffer/100
        }
        is_active = False

        while self.running:
            time.sleep(1/100)
            buttons = self.control.poll_buffered(buffers[is_active])
            if not any(buttons):
                is_active = False
                continue

            is_active = True
            self.on_buttons(buttons)

        self.api_manager.stop()
