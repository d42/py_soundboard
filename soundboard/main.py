from __future__ import annotations
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
from soundboard.mqtt import MQTT
from typing import Tuple


logger = logging.getLogger("soundboard.main")


def setup_signals(board: Board, mqtt: MQTT):

    @mqtt_message.connect
    def on_mqtt_message(sender, topic, message):
        logger.info('mqtt message')
        mqtt.send(topic, message)


def setup_mqtt_controller(board: Board, mqtt: MQTT):
    mqtt_queue: Queue[Tuple[int, int]] = Queue()
    mqtt_joystick = Joystick(mqtt_queue, backend="queue")

    def joystick_cb(topic, msg):
        btn, _, state = msg.partition(b"=")
        joystick_data = int(btn), int(state)
        mqtt_queue.put(joystick_data)

    board.register_joystick(mqtt_joystick)
    mqtt.add_topic_handler("hswaw/soundboard/state", joystick_cb)


def setup_http(board: Board):
    http = HTTPThread(board, settings)
    http.start()


def main():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    if "--debug" in sys.argv:
        logging.basicConfig(level=logging.DEBUG)

    settings.from_files(cfg="yaml", verbose=True)
    settings.from_args(sys.argv[1:])
    if settings.prometheus:
        start_http_server(settings.prometheus_port)

    board = Board(settings)
    for file in Path(settings.yaml_directory).glob("*.yaml"):
        board.register_sound_set(yamlfile=file)

    if settings.http:
        setup_http(board)

    if settings.device_path:
        joystick = Joystick(
            settings.device_path,
            backend=settings.input_type,
            mapping=settings.physical_mapping,
            offset=settings.scancode_offset,
        )

        board.register_joystick(joystick)
    else:
        logger.warning("no hardware soundboard")

    if settings.mqtt:
        mqtt = MQTT(
            path=settings.mqtt_path,
            login=settings.mqtt_login,
            password=settings.mqtt_password,
        )
        mqtt.add_topic_handler("hswaw/dank/state", board.on_dankness)
        setup_mqtt_controller(board, mqtt)
    board.run()


if __name__ == "__main__":
    main()
