import time
import logging
from threading import Thread

from soundboard.sounds import SoundSet

logger = logging.getLogger('board')


class Board(Thread):
    def __init__(self):

        self._state = set()

        self.combo_sets = {}

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""

        self.joystick = joystick
        self.joystick.set_callback(self.on_buttons)

    def register_sound_set(self, name, combo=frozenset()):
        if self.combo_sets.get(combo, None):
            raise ValueError("combo %s is already occupied" % combo)

        sound_set = SoundSet(name)
        self.combo_sets[frozenset(combo)] = sound_set

    def on_buttons(self, buttons):
        """:type buttons: states_tuple"""
        logger.debug(buttons)
        pushed, released, held = buttons.pushed, buttons.released, buttons.held
        sound_set = self.combo_sets.get(held, None)
        if not sound_set:
            return
        sound_set.play(pushed)

    @property
    def buttons(self):
        buttons_set = {i for i, value in enumerate(self._state) if value > 0}
        return buttons_set

    def play_sounds(self):
        pass

    def run(self):
        self.running = True
        while self.running:
            self.play_sounds()
            time.sleep(0.3)
