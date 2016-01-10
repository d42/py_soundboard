from marshmallow.fields import List


class Frozenset(List):
    def _serialize(self, value, attr, obj):
        serialized = super(Frozenset, self)._serialize(value, attr, obj)
        return frozenset(serialized)

    def _deserialize(self, value, attr, obj):
        serialized = super(Frozenset, self)._serialize(value, attr, obj)
        return frozenset(serialized)
