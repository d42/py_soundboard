import os
import logging

import yaml
from argumentize import Argumentize, OptionStr, OptionInt, OptionBool
from collections import UserDict

from ..schema import SoundSet

logger = logging.getLogger('config')


class Settings(Argumentize):

    physical_mapping = {k: i for (i, k) in
                        enumerate([8, 7, 6, 5, 1, 2, 3, 4, 9, 10, 11, 0])}
    buttons_count = len(physical_mapping)

    wav_directory = OptionStr(required=True, fmt=os.path.expanduser)
    yaml_directory = OptionStr(required=True, fmt=os.path.expanduser)
    debug = OptionBool(False)
    input_type = OptionStr('evdev', help='sdl, evdev')
    device_path = OptionStr(required=True)
    button_poll_buffer = OptionInt(35)
    button_poll_active_buffer = OptionInt(15)
    scancode_offset = OptionInt(304)
    weather_url = OptionStr('http://127.0.0.1:7654')
    weather_interval = OptionInt(15 * 60)
    jakdojade_url = OptionStr('http://localhost:5000/schedule/next')
    http = OptionBool(True)
    http_ip = OptionStr('0.0.0.0')
    http_port = OptionInt(8080)
    prometheus = OptionBool(True)
    prometheus_port = OptionInt(8000)
    mqtt = OptionBool(True)
    mqtt_path = OptionStr('server path')
    mqtt_login = OptionStr('public')
    mqtt_password = OptionStr('public')

    delay_constant = 0
    delay_multiplier = 0
    sound_sleep_offset = 0.15

    def __contains__(self, key):
        return hasattr(self, key)

    def __getitem__(self, key):
        return getattr(self, key)

settings = Settings('soundboard')


class Store:

    def __init__(self):
        self.store = {}

    def register(self, item):
        name = item.name
        self.store[name] = item
        return item

    def by_name(self, name):
        return self.store[name]


class SoundStore(Store):

    def attributes(self, sound):
        return self.by_name(sound).config_sounds_attributes

    def __contains__(self, sound_name):
        return sound_name in self.store

    def __getitem__(self, sound_name):
        return self.store[sound_name]


class ClientStore(Store):
    pass


class State:

    def __init__(self, sounds=SoundStore):
        self.sounds = sounds()
        self.clients = ClientStore()


state = State()


class YAMLConfig(UserDict):

    def __init__(self, path, state=state, settings=settings):
        self.settings = settings
        self.state = state
        self.load(path)

    def load(self, path):
        self._path = path
        logger.info("loading %s", path)
        with open(path, 'r') as file:
            data = yaml.load(file.read())

            schema = SoundSet()
            schema.context = dict(
                sounds=self.state.sounds,
                settings=self.settings,
            )
            self.data, errors = schema.load(data)
            if errors:
                raise Exception(path, errors)

    def reload(self):
        self.load(self._path)

    def __getitem__(self, item):
        return self.data[item]
