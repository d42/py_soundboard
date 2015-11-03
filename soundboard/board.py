import time
import glob
import logging
from threading import Thread

from soundboard.sounds import SoundSet

logger = logging.getLogger('board')


class Board(Thread):
    def __init__(self):
        super(Board, self).__init__()

        self.combo_sets = {}
        self.joystick = None
        self.running = False

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""

        self.joystick = joystick
        self.joystick.set_callback(self.on_buttons)

    def load_from_dir(self, directory):
        files = glob.glob("*.yaml")

    def register_sound_set(self, sound_set, combo=None):
        combo = sound_set.keys if not combo else combo

        if combo in self.combo_sets:
            raise ValueError("combo %s is already occupied" % list(combo))
        self.combo_sets[frozenset(combo)] = sound_set

    def on_buttons(self, buttons):
        """:type buttons: states_tuple"""
        logger.debug(buttons)
        pushed, held, released = buttons.pushed, buttons.held, buttons.released
        self.play_sounds(pushed, held)
        self.finish_sounds(released)

    def play_sounds(self, pushed, held):
        if not pushed: return  # noqa
        if held not in self.combo_sets: return  # noqa
        self.combo_sets[held].play(pushed)

    def finish_sounds(self, released):
        for sound_set in self.combo_sets.values():
            sound_set.stop(released)

    def run(self):
        self.running = True
        while self.running:
            time.sleep(0.3)
