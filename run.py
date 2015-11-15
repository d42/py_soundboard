#!/usr/bin/python3
import os
import sys
import glob
import logging

from soundboard.board import Board
from soundboard.controls import Joystick
from soundboard.sounds import SoundSet
from soundboard.config import settings


def get_files(directory, extension):
    glob_path = os.path.join(directory, '*.%s' % extension)
    return glob.glob(glob_path)


def main():
    logger = logging.getLogger()
    settings.from_args(sys.argv[1:])

    if settings.debug:
        logger.setLevel(logging.DEBUG)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    b = Board()
    for file in get_files(settings.yaml_directory, 'yaml'):
        sound_set = SoundSet.from_yaml(file, settings=settings)
        b.register_sound_set(sound_set)

    joystick = Joystick(settings.device_path, backend=settings.input_type,
                        mapping=settings.physical_mapping,
                        offset=settings.scancode_offset)

    b.register_joystick(joystick)
    b.run()


if __name__ == "__main__":
    main()
