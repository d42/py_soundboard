import pytest
import time

from soundboard.controls import Joystick


interactive = pytest.mark.interactive


def print_event(event):
    pytest.set_trace()
    print("new event %s" % event)


@interactive
def test_joystick_interactive():
    j = Joystick()
    j.set_callback(print_event)
    time.sleep(10)
    del j
