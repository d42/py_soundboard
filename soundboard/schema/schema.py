import os

from marshmallow import (Schema, fields, validates, pre_load,
                         ValidationError, validates_schema)

from .fields import Frozenset

from soundboard.enums import ModifierTypes


class SettingsMixin:

    def set_missing_from_context_settings(self, data):
        settings = self.context['settings']
        for key in self.fields.keys():
            if key not in data and key in settings:
                data[key] = settings[key]


class SoundSchema(Schema):
    name = fields.Str(required=True)
    keys = Frozenset(fields.Int())
    type = fields.Str(required=True)
    dank = fields.Boolean(missing=False)
    is_async = fields.Boolean(missing=False)
    attributes = fields.Dict(required=True)

    @pre_load
    def pre_load(self, data):
        self.validate_name(data)
        self.read_attributes(data)

    def validate_name(self, data):
        sound_type = data['type']
        if sound_type not in self.context['sounds']:
            raise ValidationError('Unknown type {}'.format(data['type']))

    def validate_attributes(self, data):
        pass

    def read_attributes(self, data):
        """:type data: dict"""
        found_attributes = {}
        sound_type = data['type']
        attributes, defaults = self.context['sounds'][sound_type].attributes
        for attr in attributes:
            if attr not in data and attr not in defaults:
                raise ValidationError(
                    "type {} missing {}".format(sound_type, attr))
            found_attributes[attr] = data.pop(attr, defaults.get(attr))

        data['attributes'] = found_attributes


class StartupSchema(Schema):
    sound = fields.Nested(SoundSchema())


class SoundSet(Schema, SettingsMixin):
    name = fields.Str(required=True)
    keys = Frozenset(fields.Int(), missing=frozenset())
    modifiers = Frozenset(fields.Raw(), missing=frozenset())
    wav_directory = fields.Str(required=True)
    vox_directory = fields.Str(required=True)
    delay_constant = fields.Float(required=True)
    delay_multiplier = fields.Float(required=True)
    sounds = fields.Nested(SoundSchema, many=True, required=True)
    startup = fields.Nested(StartupSchema)

    @validates('modifiers')
    def validate_modifiers(self, mods):
        for mod in mods:
            if mod not in ModifierTypes:
                raise ValidationError("Unknown modifier {}".format(mod))

    @validates('sounds')
    def validate_sounds(self, sounds):
        pass

    def enumify_modifiers(self, data):
        modifiers = data.get('modifiers', None)
        if modifiers:
            data['modifiers'] = [ModifierTypes(m) for m in modifiers]

    @pre_load
    def pre_load(self, data):
        self.set_missing_from_context_settings(data)
        self.enumify_modifiers(data)
        self.default_vox_directory(data)

    @validates_schema
    def validate_schema(self, data):
        if ModifierTypes.floating not in data['modifiers']:
            self.validate_sound_keys(data)

    def default_vox_directory(self, data):
        if 'vox_directory' not in data:
            wav_directory = data['wav_directory']
            data['vox_directory'] = os.path.join(wav_directory, 'vox')

    def validate_sound_keys(self, data):
        pass
