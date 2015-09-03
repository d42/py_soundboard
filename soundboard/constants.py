from itertools import count

wav_directory = "sounds/"
sound_sets_directory = "configs/"
srs_debugging = False


button_interval = 10
weather_interval = 15 * (60*1000)

physical_mapping = dict(zip([
    8, 7, 6, 5,
    1, 2, 3, 4,
    9, 10, 11, 0],
    count()))

buttons_count = len(physical_mapping)

top_left = {0, 1, 4}
top_right = {2, 3, 7}
bottom_left = {4, 8, 9}
bottom_right = {7, 10, 11}

weather_url = 'http://api.openweathermap.org/data/2.5/weather'
city_id = 756135
