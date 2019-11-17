import pytest

from queue import Queue
from soundboard.controls import ControlHandler
from soundboard.controls import Joystick
from soundboard.enums import EventTypes
from soundboard.types import event_tuple

joystick_plugged_in = pytest.mark.joystick_plugged_in


@joystick_plugged_in
def test_sdl():
    j = Joystick(0, backend="sdl")
    assert j is not None


@joystick_plugged_in
def test_evdev():
    j = Joystick("/dev/input/event0", backend="evdev")
    assert j is not None


def test_controls():
    evt_queue = Queue()
    j = Joystick(evt_queue, backend='queue')
    evt_queue.put(event_tuple(123, EventTypes.push))
    evt_queue.put(event_tuple(123, EventTypes.release))
    evt_queue.put(event_tuple(100, EventTypes.push))
    ch = ControlHandler()
    ch.register_controler(j)
    states_tuple = ch.poll_buffered(0)
    assert states_tuple.pushed == frozenset([123])
    assert states_tuple.released == frozenset([])
    assert states_tuple.held == frozenset([100])
