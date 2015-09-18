import pytest
from soundboard.controls import Joystick, RawSDLJoystick, RawEVDEVJoystick

joystick_plugged_in = pytest.mark.joystick_plugged_in


@joystick_plugged_in
def test_sdl():
    j = Joystick(0, backend=RawSDLJoystick)

@joystick_plugged_in
def test_evdev():
    j = Joystick("/dev/input/event0", backend=RawEVDEVJoystick)
