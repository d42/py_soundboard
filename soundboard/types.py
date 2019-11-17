from collections import namedtuple


event_tuple = namedtuple("event_tuple", "button type")
states_tuple = namedtuple("events_change_tuple", "pushed released held")
sound_state = namedtuple("sound_state", "chunk position")
api_state = namedtuple("api_state", "data status")
