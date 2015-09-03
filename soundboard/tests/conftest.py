import pytest


def pytest_addoption(parser):
    parser.addoption("--interactive", action="store_true", default=False,
                     help="run slow tests")


def pytest_runtest_setup(item):
    is_interactive = 'interactive' in item.keywords
    run_interactive = item.config.getoption('--interactive')

    if is_interactive and not run_interactive:
        pytest.skip('needs --interactive option to run')
    if not is_interactive and run_interactive:
        pytest.skip('skipping noninteractive')
