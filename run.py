#!/usr/bin/python3
import os
import sys
import glob
import logging

from soundboard.board import Board
from soundboard.controls import Joystick
from soundboard.sounds import SoundSet
from soundboard.config import settings
from soundboard.http import HTTPThread


def get_files(directory, extension):
    glob_path = os.path.join(directory, '*.%s' % extension)
    return glob.glob(glob_path)


def main():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    if '--debug' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)

    logger = logging.getLogger()
    settings.from_files(cfg='yaml', verbose=True)
    settings.from_args(sys.argv[1:])

    b = Board(settings)
    http = HTTPThread(b, settings)
    http.start()
    for file in get_files(settings.yaml_directory, 'yaml'):
        sound_set = SoundSet.from_yaml(file, settings=settings)
        b.register_sound_set(sound_set)

    joystick = Joystick(settings.device_path, backend=settings.input_type,
                        mapping=settings.physical_mapping,
                        offset=settings.scancode_offset)

    b.register_joystick(joystick)
    http_joystick = Joystick(http.queue, backend='queue')
    b.register_joystick(http_joystick)
    b.run()


if __name__ == "__main__":
    main()
