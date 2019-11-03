import glob
import logging
import os
import sys
from queue import Queue

from prometheus_client import start_http_server

from soundboard.board import Board
from soundboard.config import settings
from soundboard.controls import Joystick
from soundboard.http import HTTPThread


def get_files(directory, extension):
    glob_path = os.path.join(directory, '*.%s' % extension)
    return glob.glob(glob_path)


logger = logging.getLogger('soundboard.main')


def main():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    if '--debug' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)

    settings.from_files(cfg='yaml', verbose=True)
    settings.from_args(sys.argv[1:])
    if settings.prometheus:
        start_http_server(settings.prometheus_port)

    b = Board(settings)
    http = HTTPThread(b, settings)
    http.start()
    for file in get_files(settings.yaml_directory, 'yaml'):
        b.register_sound_set(yamlfile=file)

    joystick = Joystick(
        settings.device_path, backend=settings.input_type,
        mapping=settings.physical_mapping,
        offset=settings.scancode_offset,
    )

    b.register_joystick(joystick)

    if b.settings.mqtt:
        mqtt_queue = Queue()
        mqtt_joystick = Joystick(mqtt_queue, backend='queue')

        def joystick_cb(topic, msg):
            btn, _, state = msg.partition(b'=')
            joystick_data = int(btn), int(state)
            mqtt_queue.put(joystick_data)

        b.register_joystick(mqtt_joystick)
        b.mqtt_client.add_topic_handler('hswaw/soundboard/state', joystick_cb)
    b.run()


if __name__ == '__main__':
    main()
