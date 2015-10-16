import logging
import yaml

logger = logging.getLogger('config')


class YAMLConfig:
    def __init__(self, path):
        self.load(path)

    def load(self, path):
        self._path = path
        with open(path, 'r') as file:
            self._data = yaml.load(file.read())

    def reload(self):
        self.load(self._path)
        self._validate()

    def _validate(self):
        errors = []
        if 'delay_constant' not in self._data:
            logger.warn('delay_constant MISSING, defaulting to %d', self.dc)

        if 'delay_multi' not in self._data:
            logger.warn('delay_multiplier MISSING, defaulting to %d', self.dm)

        if 'name' not in self._data:
            errors.append("name parameter missing")

        if 'sounds' not in self._data:
            errors.append("sounds list missing")
        else:
            for sound_id, sound in enumerate(self._data['sounds']):
                if 'name' not in sound:
                    errors.append("%s sound is missing name" % sound_id)
                else:
                    sound_id = "%s(%d)" % (sound_id, sound['name'])

                if 'position' not in sound:
                    errors.append("%s sound is missing position" % sound_id)

                if 'type' not in sound:
                    errors.append("%s sound is missing type" % sound_id)

        if errors:
            raise Exception(errors)

    @property
    def sounds(self):
        return self._data['sounds']

    @property
    def name(self):
        return self._data['name']

    @property
    def delay_const(self):
        return self._data.getattr('delay_constant', 0)

    def delay_multi(self):
        return self._data.getattr('delay_multiplier', 1)
