import pytest
from soundboard.controls import Joystick
from soundboard.enums import EventTypes
from soundboard.types import event_tuple, states_tuple

joystick_plugged_in = pytest.mark.joystick_plugged_in


class StubJoystick:
    def __init__(self, device_path, mapping=None, offset=0):
        pass

    def wait(self):
        return True

    def get_events(self):
        e1 = event_tuple(4, EventTypes.push)
        e2 = event_tuple(4, EventTypes.release)
        return [e1, e2]


@joystick_plugged_in
def test_sdl():
    j = Joystick(0, backend='sdl')


@joystick_plugged_in
def test_evdev():
    j = Joystick("/dev/input/event0", backend='evdev')


def test_controls():
    j = Joystick(None, backend=StubJoystick)
    e1 = event_tuple(123, EventTypes.push)
    e2 = event_tuple(123, EventTypes.release)
    e3 = event_tuple(100, EventTypes.push)
    state = frozenset([123]), frozenset(), frozenset([100])

    assert j.postprocess([e1, e2, e2, e3]) == states_tuple(*state)
