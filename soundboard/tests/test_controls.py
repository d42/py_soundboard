import pytest
from soundboard.controls import Joystick, RawSDLJoystick, RawEVDEVJoystick, StubJoystick
from soundboard.controls import EventTypes, event_tuple

joystick_plugged_in = pytest.mark.joystick_plugged_in


@joystick_plugged_in
def test_sdl():
    j = Joystick(0, backend=RawSDLJoystick)


@joystick_plugged_in
def test_evdev():
    j = Joystick("/dev/input/event0", backend=RawEVDEVJoystick)


def test_controls():
    j = Joystick(None, backend=StubJoystick)

    e1 = event_tuple(123, EventTypes.push)
    e2 = event_tuple(123, EventTypes.release)

    j.update_held_buttons([e1])
    j.update_held_buttons([e2])
