import logging
from queue import Queue

import paho.mqtt.client as mqtt


logger = logging.getLogger('soundboard.mqtt')


class MQTT:
    queue = None
    topics = None

    def __init__(self, path, login, password):
        self.topics = dict()
        self.queue = Queue()

        self.server = path
        self.login = login
        self.password = password
        self._setup_mqtt()

    def add_topic_handler(self, topic, cb):
        self.topics[topic] = cb
        self.mqtt_client.subscribe(topic, qos=0)

    def _on_message(self, client, userdata, msg):
        cb = self.topics.get(msg.topic)
        if cb:
            cb(msg.topic, msg.payload)

    def _on_connect(self, client, userdata, flags, rc):
        for t in self.topics:
            self.mqtt_client.subscribe(t, qos=0)

    def _on_log(self, client, userdata, level, buf):
        print(client, userdata, level, buf)

    def send(self, topic, message):
        print('mqtt', topic, message)
        self.mqtt_client.publish(topic, message)

    def _setup_mqtt(self):
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.username_pw_set(self.login, self.password)
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_log = self._on_log
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.connect_async(self.server, 1883, 60)
        self.mqtt_client.loop_start()
