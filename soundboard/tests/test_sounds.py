from textwrap import dedent

import pytest

from .mocks import NOPMixer

from soundboard import sounds


@pytest.fixture
def factory():
    return sounds.SoundFactory(NOPMixer, 'sounds/')


class MockRequest:

    @property
    def text(self):
        return dedent("""
            {"coord":{"lon":21.01,"lat":52.23},"weather":
            [{"id":800,"main":"Clear","description":"Sky is Clear","icon":"01n"}],
            "base":"cmc stations","main":{"temp":21.37,"pressure":1018,"humidity":77,
            "temp_min":15.56,"temp_max":17.22},"wind":{"speed":1.5,"deg":290},
            "clouds":{"all":0},"dt":1442600185,"sys":{"type":1,"id":5374,"message":0.008,
            "country":"PL","sunrise":1442549747,"sunset":1442594587},
            "id":756135,"name":"Warsaw","cod":200}
            """)  # noqa


def test_sounds(monkeypatch, factory):
    simple = factory.simple("test/test.wav")
    simple.play()

    vox = factory.vox("test")
    vox.play()

    list = factory.list(["test/test2.wav", "test/test3.wav"])
    list.play()
    list.end()

    random = factory.random(["test/test.wav", "test/test3.wav"])
    random.play()
    monkeypatch.setattr('requests.get', lambda *args, **kwargs: MockRequest())
    weather = factory.weather("europe,warsaw")
    weather.update_temperature()
    assert weather.temperature == 21.37


def test_transport_humanize():
    assert sounds.ZTMSound._line_humanize('13') == 'topside train number 13'
    assert sounds.ZTMSound._line_humanize('M3') == 'subsurface train'
    assert sounds.ZTMSound._line_humanize('123') == 'day bust number 123'
    assert sounds.ZTMSound._line_humanize('S2') == 'transportation'
