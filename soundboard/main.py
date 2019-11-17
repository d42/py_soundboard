import logging
import os
import sys
from queue import Queue
from pathlib import Path

from prometheus_client import start_http_server

from soundboard.board import Board
from soundboard.config import settings
from soundboard.controls import Joystick
from soundboard.http import HTTPThread
from soundboard.signals import mqtt_message


logger = logging.getLogger("soundboard.main")


def setup_signals(board: Board):
    @mqtt_message.connect
    def on_mqtt_message(sender, topic, message):
        logger.info('mqtt message')
        board.mqtt_send(topic, message)


def main():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    if "--debug" in sys.argv:
        logging.basicConfig(level=logging.DEBUG)

    settings.from_files(cfg="yaml", verbose=True)
    settings.from_args(sys.argv[1:])
    if settings.prometheus:
        start_http_server(settings.prometheus_port)

    b = Board(settings)
    http = HTTPThread(b, settings)
    http.start()
    for file in Path(settings.yaml_directory).glob("*.yaml"):
        b.register_sound_set(yamlfile=file)

    if b.settings.device_path:
        joystick = Joystick(
            settings.device_path,
            backend=settings.input_type,
            mapping=settings.physical_mapping,
            offset=settings.scancode_offset,
        )

        b.register_joystick(joystick)
    else:
        logger.warning("no hardware soundboard")

    if b.settings.mqtt:
        mqtt_queue = Queue()
        mqtt_joystick = Joystick(mqtt_queue, backend="queue")

        def joystick_cb(topic, msg):
            btn, _, state = msg.partition(b"=")
            joystick_data = int(btn), int(state)
            mqtt_queue.put(joystick_data)

        b.register_joystick(mqtt_joystick)
        b.mqtt_client.add_topic_handler("hswaw/soundboard/state", joystick_cb)
    b.run()


if __name__ == "__main__":
    main()
