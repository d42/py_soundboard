from marshmallow.fields import List


class Frozenset(List):
    def _serialize(self, value, attr, obj, **kwargs):
        serialized = super()._serialize(value, attr, obj)
        return frozenset(serialized)

    def _deserialize(self, value, attr, obj, **kwargs):
        serialized = super()._serialize(value, attr, obj)
        return frozenset(serialized)
