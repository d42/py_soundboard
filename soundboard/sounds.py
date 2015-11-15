import os
import random
import json
import logging
import abc
import re

from functools import partial, update_wrapper
from threading import Thread

import arrow
import six
import requests
from time import time

from soundboard.vox import voxify
from soundboard import constants
from soundboard.config import YAMLConfig
from soundboard.mixer import SDLMixer
from soundboard.types import sound_state


class SoundFactory:

    sound_classes = dict()
    sound_names = dict()

    def __init__(self, mixer):
        """:type mixer: SDLMixer"""
        # https://stackoverflow.com/questions/529240/what-happened-to-types-classtype-in-python-3
        self.mixer = mixer() if isinstance(mixer, type) else mixer

    def by_name(self, name):
        cls = self.sound_names[name]
        return cls(mixer=self.mixer)

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
    running = False

    def __init__(self, mixer, data=None):
        """:type mixer: SDLMixer"""
        self.mixer = mixer
        self.name = "I'm So unnammed"
        self.current_chunk = None

        if data: self.setup(data)

    def setup(self, paths):
        self.chunks = [self.mixer.read(p) for p in paths]
        self.chunk = None

    @staticmethod
    def on_next(chunks, state):
        return chunks[(state.position + 1) % len(chunks)]

    @staticmethod
    def on_end(chunks, state):
        return None

    @staticmethod
    def on_start(chunks, state):
        return chunks[state.position if state.position else 0]

    def signal(self, name):
        func = getattr(self, 'on_' + name)
        current_state = self._get_state()
        chunk = func(self.chunks, current_state)
        return chunk

    def _get_state(self):
        chunk = self.current_chunk
        position = self.chunks.index(chunk) if chunk in self.chunks else None
        return sound_state(chunk, position)

    def _obtain_chunk(self):  # sup :3
        signals = ['start', 'next'][1 if self.running else 0:]
        chunk = next(chunk for chunk in map(self.signal, signals) if chunk)
        return chunk

    def play(self):
        self.current_chunk = self._obtain_chunk()
        self.current_chunk.play()
        self.running = True
        return self.current_chunk.duration

    def end(self):
        self.running = False
        chunk = self.signal('end')
        if chunk:
            return chunk.play()  # noqa


@decorator_register_sound
class SimpleSound(Sound):
    simple_name = 'simple'
    config_sounds_attribute = 'file'

    def setup(self, path):
        self.chunks = [self.mixer.read(path)]


@decorator_register_sound
class RandomSound(Sound):
    simple_name = 'random'
    config_sounds_attribute = 'files'

    @staticmethod
    def on_next(chunks, state):
        return random.choice(chunks)


@decorator_register_sound
class ListSound(Sound):
    simple_name = 'list'
    config_sounds_attribute = 'files'

    @staticmethod
    def on_start(chunks, state):
        return chunks[0]


@decorator_register_sound
class WrappedSound(Sound):
    simple_name = 'wrapped'
    config_sounds_attribute = 'files'

    @staticmethod
    def on_next(chunks, state):
        top = len(chunks) - 1
        pos = max(1, ((state.position + 1) % top))
        return chunks[pos]

    @staticmethod
    def on_start(chunks, state):
        return chunks[0]

    @staticmethod
    def on_end(chunks, state):
        return chunks[-1]


@decorator_register_sound
class VoxSound(Sound):
    simple_name = 'vox'
    config_sounds_attribute = 'sentence'

    def setup(self, sentence):
        self.chunks = super(VoxSound, self).setup(voxify(sentence))

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

    def setup(self, location):
        if location.isdigit():
            self.params = {'id': int(location), 'units': 'metric'}
        else:
            self.params = {'q': location, 'units': 'metric'}

    def play(self):
        sentence = self.base_sentence % self.temperature
        if self.temperature < 0:
            sentence += 'ebin'
        sound = VoxSound(data=sentence, mixer=self.mixer)
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
        json_content = json.loads(text)
        temp = json_content.get('main', {}).get('temp', None)
        return temp


# mock
def _get_next_train(line, stop):
    now = arrow.utcnow()
    return now.replace(minutes=7, seconds=20)


@decorator_register_sound
class ZTMSound(Sound):
    def setup(self, line, stop):
        self.line = line
        self.stop = stop

    @classmethod
    def _line_humanize(self, line):
        if re.match(r'[0-9]{2}', line):
            # tram
            return 'topside train number {}'.format(line)
        elif re.match(r'[0-9]{3}', line):
            # day bus
            return 'day bust number {}'.format(line)
        elif re.match(r'm[0-9]+', line.lower()):
            # metro line
            return 'subsurface train'
        else:
            return 'transportation'

    def play(self):
        next = _get_next_train(self.line, self.stop)


class SoundSet(object):

    def __init__(self, name, mixer=SDLMixer):

        self.name = name
        self.busy_time = time()
        self.sounds = {}

        logging.info("Creating board %s", name)

        self.sounds_factory = SoundFactory(mixer)

        self._load_config()

    def _load_config(self):
        config = self.name + '.yaml'
        path = os.path.join(constants.sound_sets_directory, config)
        self.config = YAMLConfig(path)
        self._load_sounds()

    def _load_sounds(self):
        for soundentry in self.config.sounds:
            sound = self._create_sound(soundentry)

            position = soundentry['position']
            position = [position] if isinstance(position, int) else position
            position = frozenset(position)
            self.sounds[position] = sound

    def _create_sound(self, config):
        sound = self.sounds_factory.by_name(config['type'])
        value = config[sound.config_sounds_attribute]
        if 'name' in config:
            sound.name = config['name']
        sound.setup(value)
        return sound


    def play(self, buttons):
        if not buttons: return  # noqa

        buttons = frozenset(buttons)
        sound = self.sounds.get(buttons, None)
        if not sound: return  # noqa
        sound.play()

    def stop(self, released_buttons):
        for (buttons, sound) in self.sounds.items():
            if released_buttons & buttons and sound.running:
                sound.end()
