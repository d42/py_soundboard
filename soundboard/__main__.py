import os
import sys
import glob
import logging

from prometheus_client import start_http_server

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
    if settings.prometheus:
        start_http_server(settings.prometheus_port)

    b = Board(settings)
    if settings.http:
        http = HTTPThread(b, settings)
        http_joystick = Joystick(http.queue, backend='queue')
        b.register_joystick(http_joystick)
        http.start()
    for file in get_files(settings.yaml_directory, 'yaml'):
        # sound_set = SoundSet.from_yaml(file, settings=settings)
        b.register_sound_set(yamlfile=file)

    joystick = Joystick(settings.device_path, backend=settings.input_type,
                        mapping=settings.physical_mapping,
                        offset=settings.scancode_offset)

    b.register_joystick(joystick)
    b.run()


if __name__ == "__main__":
    main()
