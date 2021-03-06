from textwrap import dedent

import pytest

from .mocks import NOPMixer
from soundboard import sounds
from soundboard.client_api import ApiManager


@pytest.fixture
def factory():
    return sounds.SoundFactory(NOPMixer, "soundboard/tests/testboard/files/")


class MockRequest:

    status_code = 200

    @property
    def text(self):
        return dedent(
            """
            {"coord":{"lon":21.01,"lat":52.23},"weather":
            [{"id":800,"main":"Clear","description":"Sky is Clear","icon":"01n"}],
            "base":"cmc stations","main":{"temp":21.37,"pressure":1018,"humidity":77,
            "temp_min":15.56,"temp_max":17.22},"wind":{"speed":1.5,"deg":290},
            "clouds":{"all":0},"dt":1442600185,"sys":{"type":1,"id":5374,"message":0.008,
            "country":"PL","sunrise":1442549747,"sunset":1442594587},
            "id":756135,"name":"Warsaw","cod":200}
            """
        )  # noqa


def test_sounds(monkeypatch, factory):
    simple = factory.simple("test/test.wav")
    simple.play()

    vox = factory.vox("alpha")
    vox.play()

    list = factory.list(["test/test2.wav", "test/test3.wav"])
    list.play()
    list.end()
    random = factory.random(["test/test2.wav", "test/test3.wav"])
    random.play()
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: MockRequest())
    _ = factory.weather("europe,warsaw")
    au = ApiManager()
    au.update()
    # assert weather.temperature == 21.37
