import json
import logging
import time
import traceback
from threading import Thread
from typing import Dict

import requests.exceptions

from soundboard.config import state
from soundboard.types import api_state

logger = logging.getLogger('api')
instances: Dict[type, type] = {}


class ApiManager(Thread):
    def __init__(self, instances=instances):
        super().__init__()
        self.daemon = True
        self.instances = instances

    def run(self):
        while True:
            time.sleep(1)
            self.update()

    def update(self):
        for instance in self.instances.values():
            if instance.stale and instance.cacheme:
                try:
                    instance.update()
                except Exception as es:
                    traceback.print_exc()
                    logger.critical('api exception: %s', es)


class ApiClient:

    OK = 'OK'
    DISCONNECTED = 'ERROR'
    UNAUTHORIZED = 'UNAUTHORIZED'
    UNKNOWN = 'MALFUNCTION'
    TIMEOUT = 'timeout'
    cacheme = True

    def __new__(cls, url, _interval=2137, _cacheme=True, **arguments):
        attrs = cls, url, tuple(arguments.items())
        if attrs in instances:
            return instances[attrs]
        instance = super().__new__(cls)
        instance.cacheme = _cacheme
        instance.interval = _interval
        instances[attrs] = instance
        return instance

    def __init__(self, url, **params):
        self.url = url
        self.params = params

        self.timestamp = 0
        self._status = self.UNKNOWN
        self._content = {}

    def fetch_update(self):
        pass

    def update(self):
        self._content, self._status = self.fetch_update()
        self.timestamp = time.time()

    def get(self):
        if self.stale or self._status != self.OK:
            self.update()
        return api_state(self._content, self._status)

    @property
    def stale(self):
        return (time.time() - self.timestamp) > self.interval or not self.cacheme

    @property
    def status(self):
        return self._status


@state.clients.register
class JSONApi(ApiClient):
    name = 'json'

    def fetch_update(self):
        http_to_status = {200: self.OK, 401: self.UNAUTHORIZED}
        logging.info(f'requesting {self.url} ({self.params})')
        try:
            req = requests.get(self.url, params=self.params, timeout=5)
        except requests.exceptions.ConnectionError:
            return None, self.DISCONNECTED
        except requests.exceptions.Timeout:
            return None, self.TIMEOUT

        status = http_to_status.get(req.status_code, self.UNKNOWN)
        if status != self.OK:
            return None, status

        return json.loads(req.text), status
