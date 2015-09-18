import os
import random
import json
import logging
import abc

from functools import partial, update_wrapper
from threading import Thread

import six
import requests
from time import time

from soundboard.vox import voxify
from soundboard import constants
from soundboard.config import YAMLConfig
from soundboard.mixer import SDLMixer


class SoundFactory:

    sound_classes = dict()
    sound_names = dict()

    def __init__(self, mixer):
        """:type mixer: SDLMixer"""
        # https://stackoverflow.com/questions/529240/what-happened-to-types-classtype-in-python-3
        self.mixer = mixer() if isinstance(mixer, type) else mixer

    def by_name(self, name):
        cls = self.sound_names[name]
        cls_partial = partial(cls, mixer=self.mixer)
        cls_wrapped = update_wrapper(cls_partial, cls)
        return cls_wrapped

    def __getattr__(self, attr):
        return self.by_name(attr)


def decorator_register_sound(sound):
    SoundFactory.sound_classes[sound.__name__] = sound
    SoundFactory.sound_names[sound.simple_name] = sound
    return sound


@six.add_metaclass(abc.ABCMeta)
class SoundInterface():
    @abc.abstractproperty
    def simple_name(self): pass

    @abc.abstractproperty
    def config_sounds_attribute(self): pass

    @abc.abstractmethod
    def play(self): pass


class Sound(SoundInterface):

    def __init__(self, data, mixer):
        """:type mixer: SDLMixer"""
        self.mixer = mixer
        self.create(data)

    def create(self, paths):
        self.chunks = [self.mixer.read(p) for p in paths]
        self.chunk = self.chunks[0]

    def _next_sound(self):
        self.chunk = self.next_sound(self.chunks,
                                     self.chunks.index(self.chunk))

    def next_sound(self, chunks, current_position):
        return chunks[current_position]

    def on_end(self): pass

    def on_start(self): pass

    def set_name(self, name):
        if not name:
            raise ValueError("name is empty")
        self._name = name

    @property
    def duration(self):
        return sum(chunk.duration for chunk in self.chunks)

    @property
    def name(self):
        if self._name:
            return self._name

        return self.__hash__

    def play(self):
        self.chunk.play()
        self._next_sound()


@decorator_register_sound
class SimpleSound(Sound):
    simple_name = 'simple'
    config_sounds_attribute = 'file'

    def create(self, path):
        self.chunks = [self.mixer.read(path)]
        self.chunk = self.chunks[0]


@decorator_register_sound
class RandomSound(Sound):
    simple_name = 'random'
    config_sounds_attribute = 'files'

    def next_sound(self, chunks, current_position):
        return random.choice(chunks)


@decorator_register_sound
class ListSound(Sound):
    simple_name = 'list'
    config_sounds_attribute = 'files'

    def next_sound(self, chunks, current_position):
        size = len(chunks)
        return chunks[(current_position + 1) % size]


@decorator_register_sound
class VoxSound(Sound):
    simple_name = 'vox'
    config_sounds_attribute = 'sentence'

    def create(self, sentence):
        paths = voxify(sentence)
        self.chunks = [self.mixer.read(p) for p in paths]

    def play(self):
        for chunk in self.chunks:
            chunk.play()


@decorator_register_sound
class WeatherSound(Sound):
    temperature = 2137
    simple_name = 'weather'
    config_sounds_attribute = 'location'
    base_sentence = 'black mesa topside temperature is %d degrees'
    api_url = constants.weather_url

    def create(self, location):
        if location.isdigit():
            self.params = {'id': int(location), 'units': 'metric'}
        else:
            self.params = {'q': location, 'units': 'metric'}

    def play(self):
        sentence = self.base_sentence % self.temperature
        if self.temperature < 0:
            sentence += 'ebin'
        sound = VoxSound(sentence, mixer=self.mixer)
        sound.play()

    def update_temperature(self):
        logging.info("temperaturatoring :3")
        temperature = self._get_temperature()
        if temperature is None:
            logging.warning("Last temperature update failed")
            return
        self.temperature = temperature

    def _get_temperature(self):
        text = requests.get(self.api_url, params=self.params).text
        j = json.loads(text)
        temp = j.get('main', {}).get('temp', None)
        return temp


class SoundSet(object):

    def __init__(self, name, mixer=SDLMixer):

        self.name = name
        self.busy_time = time()

        self.running_sounds = set()
        logging.info("Creating board %s", name)

        self.sounds_factory = SoundFactory(mixer)

        self._load_config()

    def _load_config(self):
        config = self.name + '.yaml'
        path = os.path.join(constants.sound_sets_directory, config)
        self.config = YAMLConfig(path)
        self._load_sounds()

    def _load_sounds(self):
        self.sounds = {}
        for soundentry in self.config.sounds:
            sound_class = self.sounds_factory.by_name(soundentry['type'])

            sounds_attribute = sound_class.config_sounds_attribute

            sound_instance = sound_class(soundentry[sounds_attribute])
            name = soundentry.get('name', None)

            p = soundentry['position']
            position = frozenset([p]) if isinstance(p, int) else frozenset(p)

            if name:
                sound_instance.set_name(name)

            self.sounds[position] = sound_instance

    def end_sounds(self):
        if not self.running_sounds:
            return

        while time() < self.busy_time:
            continue
        for s in self.running_sounds:
            s.on_end()

        self.running_sounds = set()

    def play(self, buttons):
        if not buttons:
            raise Exception()

        buttons = frozenset(buttons)

        sound = self.sounds.get(buttons, None)
        if not sound:
            logging.error("ENOSOUND")
            return
        # if time() < self.busy_time:
        #     logging.error("ETOOEARLY")
        #     return
        #
        # # c, s = self.timeout_settings
        # # self.busy_time = (time() + c) + (sound.duration * s)
        # self.busy_time = time() + sound.duration * 0.5

        # if sound not in self.running_sounds:
        #     sound.on_start()
        #     self.running_sounds.add(sound)
        # else:
        sound.play()
