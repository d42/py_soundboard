from .sounds import WeatherSound


def update_weather(board):
    for sound in board.sounds:
        if isinstance(sound, WeatherSound):
            temp = WeatherSound.get_temperature(sound.location)
            sound.update_temperature(temp)
        params = {"q": location, "units": "metric"}  # noqa
