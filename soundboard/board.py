import time
from threading import Thread

from soundboard.sounds import SoundSet


class Board(Thread):
    def __init__(self):

        self._state = set()

        self.sets_combos = {}

    def register_joystick(self, joystick):
        """:type joystick: soundboard.controls.Joystick"""

        self.joystick = joystick
        self.joystick.set_callback(self.on_buttons_update)

    def register_sound_set(self, name, combo=frozenset()):
        if self.sets_combos.get(combo, None):
            raise ValueError("combo %s is already occupied" % combo)

        sound_set = SoundSet(name)
        self.sets_combos[frozenset(combo)] = sound_set

    def on_buttons_update(self, buttons):
        """:type buttons: list"""
        for (button, type) in buttons:
            if type == 'DOWN':
                self._state.add(button)
            elif type == 'UP':
                self._state.discard(button)
            elif type == 'HOLD':
                pass
            else:
                raise Exception("unknown button type %s" % type)

    def play_sounds(self):

        sorted_combos = sorted(self.sets_combos.keys(), key=len, reverse=True)

        sound_set_combo = next(c for c in sorted_combos if c <= self._state)
        sound_set = self.sets_combos[sound_set_combo]
        sound_combo = self._state - sound_set_combo
        if not sound_combo:
            return

        sound_set.play(sound_combo)

    @property
    def buttons(self):
        buttons_set = {i for i, value in enumerate(self._state) if value > 0}
        return buttons_set

    def run(self):
        self.running = True
        while self.running:
            self.play_sounds()
            time.sleep(0.3)
