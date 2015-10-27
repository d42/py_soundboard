#!/uosr/bin/python3
import os
import sys
import glob
import logging
import argparse

from soundboard.board import Board
from soundboard.controls import Joystick
from soundboard.sounds import SoundSet
from soundboard.constants import (
    physical_mapping, sound_sets_directory, wav_directory)


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', default='evdev')
    parser.add_argument('device', default='/dev/input/event0')
    parser.add_argument('--yaml-dir', default=sound_sets_directory)
    parser.add_argument('--wav-dir', default=wav_directory)
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--scancode-offset', default=0, type=int)
    return parser.parse_args(sys.argv[1:])


def get_files(directory, extension):
    glob_path = os.path.join(directory, '*.%s' % extension)
    return glob.glob(glob_path)


def main():
    logger = logging.getLogger()
    options = parse_options()

    if options.verbose:
        logger.setLevel(logging.DEBUG)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    b = Board()
    for file in get_files(options.yaml_dir, 'yaml'):
        sound_set = SoundSet.from_yaml(file, options.wav_dir)
        b.register_sound_set(sound_set)

    joystick = Joystick(options.device, backend=options.type,
                        mapping=physical_mapping,
                        offset=options.scancode_offset)

    b.register_joystick(joystick)
    b.run()


if __name__ == "__main__":
    main()

