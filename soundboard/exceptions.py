class ControllerException(Exception):
    pass


class SoundException(Exception):
    def __init__(self, msg, filename):
        Exception.__init__(self)
        self.msg = msg
        self.filename = filename


class VoxException(SoundException):
    def __init__(self, msg, filename, sentence):
        SoundException.__init__(self, msg, filename)
        self.sentence = sentence
