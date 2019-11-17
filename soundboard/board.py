import logging

from .client_api import ApiManager
from .controls import ControlHandler
from .enums import ModifierTypes
from .mixer import SDLMixer
from .sounds import SoundFactory
from .sounds import SoundSet
from .types import states_tuple

logger = logging.getLogger("soundboard.board")


class Board:
    def __init__(self, settings):
        """
        :type settings: soundboard.config.settings
        """
        self.settings = settings
        self.mixer = SDLMixer()
        self.sound_factory = SoundFactory(
            mixer=self.mixer,
            directory=settings["wav_directory"],
        )
        self._dankness = False

        self.api_manager = ApiManager()
        self.combinations = {}
        self.shared_online = {}
        self.control = ControlHandler()
        self.running = False
        self.active_sound_set = None
        self.board_state = {"allow_dank_memes": False}

    def on_dankness(self, topic, payload):
        allow = {b"safe": False, b"engaged": True}[payload]
        self.dankness = allow

    @property
    def dankness(self):
        return self.board_state["allow_dank_memes"]

    @dankness.setter
    def dankness(self, new_dankness):
        if self.dankness == new_dankness:
            return
        self.board_state["allow_dank_memes"] = new_dankness
        mode = "engaged" if new_dankness else "disengaged"
        sound = self.sound_factory.vox("may may mode %s" % mode)
        sound.play()

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""
        self.control.register_controler(joystick)

    def register_sound_set(self, sound_set=None, yamlfile=None):
        if all([yamlfile, sound_set]) or not any([sound_set, yamlfile]):
            raise ValueError("provide SoundSet instance or yaml file path")
        if yamlfile and not sound_set:
            sound_set = SoundSet.from_yaml(
                yamlfile, settings=self.settings, base_sound_factory=self.sound_factory,
            )

        if ModifierTypes.floating not in sound_set.modifiers:
            self.register_on_keys(sound_set, sound_set.keys)
        if ModifierTypes.http in sound_set.modifiers:
            self.register_on_http(sound_set, sound_set.name)

    def register_on_http(self, sound_set: SoundSet, endpoint: str):
        self.shared_online[endpoint] = sound_set

    def register_on_keys(self, sound_set: SoundSet, keys: list):
        if keys in self.combinations:
            raise ValueError("combo %s is occupied" % list(keys))
        self.combinations[frozenset(keys)] = sound_set

    def on_buttons(self, buttons: states_tuple):
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
            sound_set.play(
                pushed,
                prometheus=self.settings.prometheus,
                board_state=self.board_state,
            )
        except Exception as e:
            logger.exception(e)

    def finish_sounds(self, released: frozenset):
        for sound_set in self.combinations.values():
            sound_set.stop(released)

    def run(self):
        self.running = True
        self.api_manager.start()

        buffers = {
            False: self.settings.button_poll_buffer / 100,
            True: self.settings.button_poll_active_buffer / 100,
        }
        is_active = False

        while self.running:
            buttons = self.control.poll_buffered(buffers[is_active])
            if not any(buttons):
                is_active = False
                continue

            is_active = True
            self.on_buttons(buttons)

        self.api_manager._stop()
