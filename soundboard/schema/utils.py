from collections import Iterable

from marshmallow import ValidationError


def comma_split(data, context):
    if isinstance(data, str):
        modifiers = [d.strip() for d in data.split(",")]
    elif isinstance(data, Iterable):
        modifiers = list(data)
    else:
        raise ValidationError(f"value '{data}' is invalid")

    unknown_modifiers = [m for m in modifiers if m not in context["modifiers"]]

    if unknown_modifiers:
        raise ValidationError(f"unknown modifiers: {unknown_modifiers}")
    return modifiers


def comma_join(data):
    if isinstance(data, Iterable):
        modifiers_list = data.join(", ")
    else:
        raise ValidationError(f"invalid data {data}")
    return modifiers_list
