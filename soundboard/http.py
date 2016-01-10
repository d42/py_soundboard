from threading import Thread
from six.moves.queue import Queue
from flask import Flask, render_template, url_for


class FlaskApp:
    def __init__(self, board, settings):
        """:type board: soundboard.board.Board"""
        self.board = board
        self.settings = settings
        self.queue = Queue()

        self.app = Flask(__name__)
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/joystick/<int:button_id>', 'push_joystick', self.push_joystick)
        self.app.add_url_rule('/board/<set_name>', 'sound_set', self.list_sound_set)
        self.app.add_url_rule('/board/<set_name>/<sound_name>', 'play_sound', self.play_sound)

    def run(self, *args, **kwargs):
        self.app.run(*args, **kwargs)

    def index(self):
        links = {key: url_for('sound_set', set_name=key)
                 for key in self.board.shared_online}
        return render_template('list.html', links=links, title='sound_sets')

    def list_sound_set(self, set_name):
        sound_set = self.board.shared_online.get(set_name)
        if not sound_set:
            return '>:'

        links = {sound.name: url_for('play_sound', set_name=set_name, sound_name=sound.name)
                 for sound in sound_set.sounds.values()}
        return render_template('list.html', links=links, title='SOUNDS')

    def push_joystick(self, button_id):
        self.queue.put(button_id)
        return ':3'

    def play_sound(self, set_name, sound_name):
        sound_set = self.board.shared_online.get(set_name)
        sound = next(s for s in sound_set.sounds.values() if s.name == sound_name)
        sound.play()
        return ':3'


class HTTPThread(Thread):

    def __init__(self, board, settings):
        super(HTTPThread, self).__init__()
        self.daemon = True
        self.settings = settings
        self.app = FlaskApp(board, settings)
        self.queue = self.app.queue

    def run(self):
        self.app.run(self.settings.http_ip, self.settings.http_port, False)
