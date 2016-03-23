import os
import random
import logging
import abc
import re
from time import time

import six
import arrow

from soundboard.vox import voxify
from soundboard import config
from soundboard.mixer import SDLMixer
from soundboard.types import sound_state
from soundboard.client_api import JSONApi
from soundboard.exceptions import SoundException, VoxException
from soundboard import utils

logger = logging.getLogger('sounds')


class SoundFactory:

    def __init__(self, mixer, directory,
                 state=config.state, settings=config.settings):
        """:type mixer: SDLMixer"""
        # https://stackoverflow.com/questions/529240/what-happened-to-types-classtype-in-python-3
        self.mixer = mixer() if isinstance(mixer, type) else mixer
        self.settings = settings
        self.state = state
        self.directory = directory

    def by_name(self, name):
        ":rtype: Sound"
        cls = self.state.sounds.by_name(name)
        instance = cls(mixer=self.mixer, base_dir=self.directory)
        instance.settings = self.settings  # TODO: unuglify
        return instance

    def __getattr__(self, attr):
        def funky_wrapper(data):
            sound = self.by_name(attr)
            sound.setup(data)
            return sound
        return funky_wrapper


class SoundMeta(abc.ABCMeta):
    @property
    def attributes(cls):
        return utils.read_func_attributes(cls.setup)


@six.add_metaclass(SoundMeta)
class SoundInterface():

    @abc.abstractproperty
    def name(self):
        pass

    # @abc.abstractproperty
    # def config_sounds_attribute(self):
    #     pass

    @abc.abstractmethod
    def setup(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def play(self):
        pass


class Sound(SoundInterface):
    running = False

    def __init__(self, mixer, base_dir, data=None):
        """:type mixer: SDLMixer"""
        self.mixer = mixer
        self.dir = base_dir
        self.name = "I'm so unnammed"
        self.current_sample = None
        self.duration_const = 0

        if data:
            self.setup(data)

    def setup(self, paths, duration_const=0):
        self.duration_const = duration_const
        paths = [os.path.join(self.dir, p) for p in paths]

        try:
            self.samples = [self.mixer.read(p) for p in paths]
        except FileNotFoundError as e:
            raise SoundException(e.strerror, e.filename)

    @staticmethod
    def on_next(samples, state):
        return samples[(state.position + 1) % len(samples)]

    @staticmethod
    def on_end(samples, state):
        return None

    @staticmethod
    def on_start(samples, state):
        return samples[state.position if state.position else 0]

    def signal(self, name):
        func = getattr(self, 'on_' + name)
        current_state = self._get_state()
        sample = func(self.samples, current_state)
        return sample

    def _get_state(self):
        sample = self.current_sample
        position = self.samples.index(sample) if sample in self.samples else None
        return sound_state(sample, position)

    def _obtain_sample(self):  # sup :3
        signals = ['start', 'next'][1 if self.running else 0:]
        sample = next(sample for sample in map(self.signal, signals) if sample)
        return sample

    def play(self, async=False, **kwargs):
        self.current_sample = self._obtain_sample()
        self.current_sample.play(self.duration_const, async=async)
        self.running = True

    def play_all(self, async=False):
        for sample in self.samples:
            sample.play(self.duration_const, async=async)

    def end(self):
        self.running = False
        sample = self.signal('end')
        if sample:
            return sample.play()  # noqa


# https://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-given-class-in-python
# TODO: Increase magic

@config.state.sounds.register
class SimpleSound(Sound):
    name = 'simple'

    def setup(self, path):
        super(SimpleSound, self).setup([path])


@config.state.sounds.register
class RandomSound(Sound):
    name = 'random'

    @staticmethod
    def on_next(samples, state):
        return random.choice(samples)


@config.state.sounds.register
class ListSound(Sound):
    name = 'list'

    @staticmethod
    def on_start(samples, state):
        return samples[0]


@config.state.sounds.register
class WrappedSound(Sound):
    name = 'wrapped'

    @staticmethod
    def on_next(samples, state):
        top = len(samples) - 1
        pos = max(1, ((state.position + 1) % top))
        return samples[pos]

    @staticmethod
    def on_start(samples, state):
        return samples[0]

    @staticmethod
    def on_end(samples, state):
        return samples[-1]


@config.state.sounds.register
class VoxSound(Sound):
    name = 'vox'
    vox_duration_const = 0.15

    def setup(self, sentence):
        try:
            super(VoxSound, self).setup(voxify(sentence.lower()),
                                        duration_const=self.vox_duration_const)
        except SoundException as e:
            raise VoxException(e.msg, e.filename, sentence)

    def play(self):
        super(VoxSound, self).play_all()


@config.state.sounds.register
class WeatherSound(Sound):
    name = 'weather'
    location = 'warsaw,pl'
    config_attributes = ['location']
    sentence = 'topside temperature is %d degrees'
    below_zero = 'sub zero'
    temperature = 2137

    def setup(self, location, weather_url=None, interval=None):
        weather_url = weather_url or self.settings.weather_url
        interval = interval or self.settings.weather_interval

        if location.isdigit():
            location = int(location)
        self.location = location
        self.api = JSONApi(weather_url,
                           q=location,
                           units='metric',
                           appid='44db6a862fba0b067b1930da0d769e98',
                           _interval=interval)

    @classmethod
    def _weather2text(cls, temperature):
        text = cls.sentence + ' ' + (cls.below_zero if temperature < 0 else '')
        return text % abs(int(temperature))

    def play(self):
        sound = VoxSound(mixer=self.mixer, base_dir=self.dir)
        req = self.api.get()
        if req.status != JSONApi.OK:
            logger.critical(req)
            sound.setup(req.status)
        else:
            temperature = req.data.get('main', {}).get('temp')
            self.temperature = temperature
            sentence = self._weather2text(temperature)
            sound.setup(sentence)
        sound.play()


@config.state.sounds.register
class ZTMSound(Sound):
    name = 'ztm'
    config_attributes = ['line']

    def setup(self, line, stop, direction):
        jakdojade_url = self.settings.jakdojade_url
        self.line, self.stop, self.direction = line, stop, direction

        self.api = JSONApi(jakdojade_url,
                           line=self.line,
                           stop=self.stop,
                           direction=self.direction,
                           _cacheme=False)

    @staticmethod
    def _get_type(content):
        if 'type' in content:
            return content['type']
        line = content['line']
        if re.match(r'^[0-9]{1,2}$', line):
            return 'train'
        elif re.match(r'^[0-9]{3}$', line):
            return 'bus'
        elif re.match(r'^m[0-9]+$', line.lower()):
            return 'metro'
        else:
            return 'transportation'

    @classmethod
    def _ztm2text(cls, content):
        transport_prefix = {
            'train': 'topside train number {line}',
            'bus': 'day bust number {line}',
            'metro': 'subsurface train line {line}',
            'transportation': 'transportation',
        }
        line = content['line']
        minutes = content['minutes']
        hours = content['hours']
        heading = 'accelerating {} {}'.format(*content['heading'])
        transport_type = cls._get_type(content)

        sentence = ' '.join([transport_prefix[transport_type],
                             heading,
                             'will reach location at {h}{m} zulu'])

        return sentence.format(line=line, h=hours, m=minutes)

    def play(self):
        sound = VoxSound(mixer=self.mixer, base_dir=self.dir)
        req = self.api.get()
        if req.status != JSONApi.OK:
            logger.critical(req)
            sound.setup(req.status)
        else:
            sentence = self._ztm2text(req.data)
            sound.setup(sentence)
        sound.play()


@config.state.sounds.register
class LastZTMSound(ZTMSound):
    name = 'lastztm'

    @staticmethod
    def _get_prefix(next_transport):
        now = arrow.utcnow()
        seconds = (next_transport - now).seconds
        if seconds <= (15 * 60):
            return 'warning warning last'
        if seconds <= (30 * 60):
            return 'warning last'
        else:
            return 'last'

    @staticmethod
    def _get_transport():
        # mock
        now = arrow.utcnow()
        return now.replace(minutes=15)


class SoundSet(object):

    def __init__(self, config=None, mixer=SDLMixer):

        self.mixer = mixer
        self.startup_sound = None

        self.busy_time = time()
        self.combinations = {}
        self.sounds = {}
        if config:
            self.load_config(config)

        logger.info("created board %s", self.name)

    def __getitem__(self, key):
        return self.sounds[key]

    def load_config(self, config):
        self.sounds_factory = SoundFactory(self.mixer, config['wav_directory'])
        self.name = config['name']
        self.keys = config['keys']
        self.modifiers = config['modifiers']
        self._load_sounds(config)

    @classmethod
    def from_yaml(cls, yaml_path, settings, *args, **kwargs):
        cfg = config.YAMLConfig(yaml_path, settings=config.settings)
        return cls(cfg, *args, **kwargs)

    def _load_sounds(self, config):
        startup_entry = config.get('startup', {}).get('sound')
        if startup_entry:
            self.startup_sound = self._create_sound(startup_entry)

        for soundentry in config['sounds']:
            sound = self._create_sound(soundentry)

            keys = soundentry['keys']
            name = soundentry['name']
            self.combinations[keys] = sound
            self.sounds[name] = sound

    def _create_sound(self, sound_cfg):
        sound = self.sounds_factory.by_name(sound_cfg['type'])
        attributes = sound_cfg['attributes']
        if 'name' in sound_cfg:
            sound.name = sound_cfg['name']
        sound.setup(**attributes)
        return sound

    def on_activate(self):
        if self.startup_sound:
            self.startup_sound.play()

    def play(self, buttons):
        if not buttons:
            return

        buttons = frozenset(buttons)
        sound = self.combinations.get(buttons)
        if not sound:
            return
        sound.play()

    def stop(self, released_buttons):
        for (buttons, sound) in self.combinations.items():
            if released_buttons & buttons and sound.running:
                sound.end()
