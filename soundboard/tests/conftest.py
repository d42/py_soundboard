import pytest


def pytest_addoption(parser):
    parser.addoption("--interactive", action="store_true", default=False,
                     help="run slow tests")

    parser.addoption("--joystick", nargs=2, metavar=('sdl', 'evdev'),
                     default=False, help="run joystick tests")


def pytest_runtest_setup(item):
    is_interactive = 'interactive' in item.keywords
    js_is_plugged_in = 'joystick_plugged_in' in item.keywords
    run_interactive = item.config.getoption('--interactive')
    run_with_joystick = item.config.getoption('--joystick') is not False
    if run_with_joystick:
        sdl_id, evdev_path = item.config.getoption('--joystick')

    if is_interactive and not run_interactive:
        pytest.skip('needs --interactive option to run')
    if not is_interactive and run_interactive:
        pytest.skip('skipping noninteractive')

    if js_is_plugged_in and not run_with_joystick:
        pytest.skip('needs --joystick option to run')
