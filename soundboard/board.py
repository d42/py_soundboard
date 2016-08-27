from __future__ import division

import time
import logging
import traceback

from .enums import ModifierTypes
from .controls import ControlHandler
from .client_api import ApiManager
from .sounds import SoundSet, SoundFactory
from .mixer import SDLMixer

logger = logging.getLogger('board')


class Board():

    def __init__(self, settings):
        '''
        :type settings: soundboard.config.settings
        '''
        self.settings = settings
        self.mixer = SDLMixer()
        self.sound_factory = SoundFactory(mixer=self.mixer, directory=settings['wav_directory'])

        self.api_manager = ApiManager()
        self.combinations = {}
        self.shared_online = {}
        self.control = ControlHandler()
        self.running = False
        self.active_sound_set = None
        self.board_state = {'allow_dank_memes': False}
        if self.settings.mqtt:
            self.setup_mqtt(self.settings.mqtt_path)

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""
        self.control.register_controler(joystick)

    def register_sound_set(self, sound_set=None, yamlfile=None):
        if all([yamlfile, sound_set]) or not any([sound_set, yamlfile]):
            raise ValueError("provide SoundSet instance or yaml file path")
        if yamlfile and not sound_set:
            sound_set = SoundSet.from_yaml(yamlfile, settings=self.settings, mixer=self.mixer)

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
            sound_set.play(pushed, prometheus=self.settings.prometheus, board_state=self.board_state)
        except Exception as e:
            logger.exception(e)

    def finish_sounds(self, released):
        for sound_set in self.combinations.values():
            sound_set.stop(released)

    def setup_mqtt(self, path):
        import paho.mqtt.client as mqtt

        server, channel = path.split('/', 1)
        def on_connect(client, userdata, flags, rc):
            print("bebin")
            client.subscribe(channel)

        def on_message(client, userdata, msg):
            print(msg.topic, msg.payload)
            if msg.topic ==  'hswaw/dank/state':
                allow = {b'safe': False, b'engaged': True}[msg.payload]
                if allow == self.board_state['allow_dank_memes']:
                    return
                mode = 'engaged' if allow else 'disengaged'
                sound = self.sound_factory.vox('may may mode %s' % mode)
                sound.play()
                self.board_state['allow_dank_memes'] = allow
                print(self.board_state)

        def on_log(client, userdata, level, buf):
            print(client, userdata, level, buf)

        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set('public', 'public')
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_log = on_log
        self.mqtt_client.on_message = on_message
        self.mqtt_client.connect(server, 1883, 60)


    def poll_mqtt(self):
        ret_val = self.mqtt_client.loop(timeout=1.0)
        if ret_val:
            print("mqtt failure: %d" % ret_val)
            server, channel = self.settings.mqtt_path.split('/', 1)
            self.mqtt_client.connect(server, 1883, 60)

    def run(self):
        self.running = True
        self.api_manager.start()

        buffers = {
            False: self.settings.button_poll_buffer/100,
            True: self.settings.button_poll_active_buffer/100
        }
        is_active = False


        while self.running:
            if not is_active and self.settings.mqtt:
                self.poll_mqtt()
            time.sleep(1/100)
            buttons = self.control.poll_buffered(buffers[is_active])
            if not any(buttons):
                is_active = False
                continue

            is_active = True
            self.on_buttons(buttons)

        self.api_manager.stop()
