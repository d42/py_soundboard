#!/usr/bin/python3
import os
import sys
import logging
import argparse

from soundboard.board import Board
from soundboard.controls import Joystick
from soundboard.constants import physical_mapping


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', default='evdev')
    parser.add_argument('device', default='/dev/input/event0')
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--scancode-offset', default=0)
    return parser.parse_args(sys.argv[1:])


def main():
    logger = logging.getLogger()
    options = parse_options()

    if options.verbose:
        logger.setLevel(logging.DEBUG)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    b = Board()
    b.register_sound_set('default')
    b.register_joystick(Joystick(options.device, backend=options.type,
                                 mapping=physical_mapping,
                                 offset=options.scancode_offset))
    b.run()


if __name__ == "__main__":
    main()
