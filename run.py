#!/usr/bin/python3
import os
from soundboard.board import Board
from soundboard.controls import Joystick
from soundboard.constants import physical_mapping


def main():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    b = Board()
    b.register_sound_set('default')
    b.register_joystick(Joystick('/dev/input/event5',
                                 mapping=physical_mapping,
                                 offset=1))
    b.run()


if __name__ == "__main__":
    main()
