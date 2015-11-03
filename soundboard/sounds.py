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
from soundboard.config import YAMLConfig, state, settings
from soundboard.mixer import SDLMixer
from soundboard.types import sound_state


class SoundFactory:

    def __init__(self, mixer, directory, state=state):
        """:type mixer: SDLMixer"""
        # https://stackoverflow.com/questions/529240/what-happened-to-types-classtype-in-python-3
        self.mixer = mixer() if isinstance(mixer, type) else mixer
        self.state = state
        self.directory = directory

    def by_name(self, name):
        cls = self.state.sounds.by_name(name)
        return cls(mixer=self.mixer, base_dir=self.directory)

    def __getattr__(self, attr):
        def funky_wrapper(data):
            sound = self.by_name(attr)
            sound.setup(data)
            return sound
        return funky_wrapper


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

    def __init__(self, mixer, base_dir, data=None):
        """:type mixer: SDLMixer"""
        self.mixer = mixer
        self.dir = base_dir
        self.name = "I'm so unnammed"
        self.current_chunk = None

        if data:
            self.setup(data)

    def setup(self, paths):
        paths = [os.path.join(self.dir, p) for p in paths]
        self.chunks = [self.mixer.read(p) for p in paths]

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


@state.sounds.register
class SimpleSound(Sound):
    simple_name = 'simple'
    config_sounds_attribute = 'file'

    def setup(self, path):
        super(SimpleSound, self).setup([path])


@state.sounds.register
class RandomSound(Sound):
    simple_name = 'random'
    config_sounds_attribute = 'files'

    @staticmethod
    def on_next(chunks, state):
        return random.choice(chunks)


@state.sounds.register
class ListSound(Sound):
    simple_name = 'list'
    config_sounds_attribute = 'files'

    @staticmethod
    def on_start(chunks, state):
        return chunks[0]


@state.sounds.register
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


@state.sounds.register
class VoxSound(Sound):
    simple_name = 'vox'
    config_sounds_attribute = 'sentence'

    def setup(self, sentence):
        super(VoxSound, self).setup(voxify(sentence))

    def play(self):
        for chunk in self.chunks:
            chunk.play()


@state.sounds.register
class WeatherSound(Sound):
    temperature = 2137
    simple_name = 'weather'
    config_sounds_attribute = 'location'
    base_sentence = 'black mesa topside temperature is %d degrees'
    api_url = settings.weather_url

    def setup(self, location):
        if location.isdigit():
            self.params = {'id': int(location), 'units': 'metric'}
        else:
            self.params = {'q': location, 'units': 'metric'}

    def play(self):
        raise NotImplementedError()
        sentence = self.base_sentence % self.temperature
        if self.temperature < 0:
            sentence += 'ebin'
        sound = VoxSound(data=sentence, mixer=self.mixer, base_dir=self.dir)
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


class SoundSet(object):

    def __init__(self, config, mixer=SDLMixer):

        self.config = config
        self.sounds_factory = SoundFactory(mixer, config['wav_directory'])

        self.busy_time = time()
        self.sounds = {}
        self._load_sounds()

        logging.info("Creating board %s", self.name)

    def __getattr__(self, attr):
        if attr in ['name', 'keys']:
            return self.config[attr]
        raise AttributeError(attr)

    @classmethod
    def from_yaml(cls, yaml_path, settings, *args, **kwargs):
        config = YAMLConfig(yaml_path, settings=settings)
        return cls(config, *args, **kwargs)

    def _load_sounds(self):
        for soundentry in self.config['sounds']:
            sound = self._create_sound(soundentry)

            keys = soundentry['keys']
            self.sounds[keys] = sound

    def _create_sound(self, config):
        sound = self.sounds_factory.by_name(config['type'])
        input = config['input']
        if 'name' in config:
            sound.name = config['name']
        sound.setup(input)
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
