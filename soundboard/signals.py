from blinker import Namespace

ns = Namespace()

mqtt_message = ns.signal('mqtt-message')
