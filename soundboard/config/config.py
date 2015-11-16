import os
import logging

import yaml
from argumentize import Argumentize, OptionStr, OptionInt, OptionBool

from ..schema import SoundSet

logger = logging.getLogger('config')


class Settings(Argumentize):

    physical_mapping = dict(enumerate([8, 7, 6, 5, 1, 2, 3, 4, 9, 10, 11, 0]))
    buttons_count = len(physical_mapping)

    wav_directory = OptionStr(os.path.expanduser("~/soundboard/files"))
    yaml_directory = os.path.expanduser("~/soundboard/yaml")
    debug = OptionBool(False)
    input_type = OptionStr('evdev')
    device_path = OptionStr('/dev/input/event0')
    button_interval = OptionInt(10)
    scancode_offset = OptionInt(304)
    weather_url = OptionStr('http://api.openweathermap.org/data/2.5/weather')
    weather_interval = OptionInt(15 * (60 * 1000))

    delay_constant = 0
    delay_multiplier = 0
    sound_sleep_offset = 0.25

settings = Settings('soundboard')


class SoundStore:

    def __init__(self):
        self.sounds = {}

    def register(self, sound_class):
        name = sound_class.simple_name
        self.sounds[name] = sound_class
        return sound_class

    def by_class(self, cls):
        pass

    def by_name(self, name):
        return self.sounds[name]

    def get_sound_attribute(self, sound):
        return self.by_name(sound).config_sounds_attribute

    def register_decorator(self, sound):
        self.register(sound)
        return sound


class State:

    def __init__(self, sounds=SoundStore):
        self.sounds = sounds()

state = State()


class YAMLConfig:

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
            schema = schema.bind(
                sounds=self.state.sounds,
                settings=self.settings
            )
            self.deserialized = schema.deserialize(data)

    def reload(self):
        self.load(self._path)

    def __getitem__(self, item):
        return self.deserialized[item]
