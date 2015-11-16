import os

import colander


@colander.deferred
def deferred_delay_constant(node, kw):
    return kw['settings'].delay_constant


@colander.deferred
def deferred_delay_multiplier(node, kw):
    return kw['settings'].delay_multiplier


@colander.deferred
def deferred_wav_directory(node, kw):
    return kw['settings'].wav_directory


class KeySet(colander.Set):

    def deserialize(self, node, cstruct):
        value = super(KeySet, self).deserialize(node, cstruct)
        return frozenset(value) if isinstance(value, set) else value


class SoundInput:

    def serialize(self, node, appstruct):
        pass

    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return cstruct
        if isinstance(cstruct, (list, int, str)):
            return cstruct
        raise colander.Invalid(node, "%r is not a proper input" % cstruct)


class Sound(colander.MappingSchema):

    def deserialize(self, cstruct):
        sound_type = cstruct.get('type', None)
        if sound_type:
            input_key = self.bindings['sounds'].get_sound_attribute(sound_type)
            if input_key in cstruct:
                cstruct['input'] = cstruct.pop(input_key)

        return super(Sound, self).deserialize(cstruct)

    def preparer(self, value):
        value = value.copy()
        value['keys'] = frozenset(value['keys'])
        return value

    name = colander.SchemaNode(colander.String())
    keys = colander.SchemaNode(KeySet())
    type = colander.SchemaNode(colander.String())
    input = colander.SchemaNode(SoundInput())


class Sounds(colander.SequenceSchema):
    sound = Sound()


class SoundSet(colander.MappingSchema):

    def preparer(self, value):
        value = value.copy()
        if not value['vox_directory']:
            wav_directory = value['wav_directory']
            value['vox_directory'] = os.path.join(wav_directory, 'vox')
        return value

    name = colander.SchemaNode(colander.String())
    keys = colander.SchemaNode(KeySet(), missing=frozenset())
    wav_directory = colander.SchemaNode(
        colander.String(),
        missing=deferred_wav_directory)
    vox_directory = colander.SchemaNode(colander.String(), missing=None)
    delay_constant = colander.SchemaNode(
        colander.Float(),
        name='delay_constant',
        missing=deferred_delay_constant)
    delay_m = colander.SchemaNode(
        colander.Float(),
        name='delay_multiplier',
        missing=deferred_delay_multiplier)
    sounds = Sounds()
