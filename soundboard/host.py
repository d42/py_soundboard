#!/usr/bin/env python2

import os
import time
import json
import logging
from datetime import datetime
from operator import itemgetter
from threading import Thread


from tornado import ioloop


def update_buttons(state):
    for event in pygame.event.get():
        if event.button not in PHYS_MAPPING:
            continue

        n = PHYS_MAPPING[event.button]
        if event.type == JOYBUTTONUP:
            state[n] = 0
            continue

        elif event.type == JOYBUTTONDOWN:
            state[n] = max(state) + 1

    mbuttons = list()
    for i, e in sorted(enumerate(state), key=itemgetter(1)):
        if e:
            mbuttons.append(i)
    return mbuttons


def select_board(mbuttons):

        if sorted(mbuttons[:3]) in CORNERS:
            corner_id = CORNERS.index(sorted(mbuttons[:3]))
            board = CORNER_BOARDS[corner_id]

            if board.name == 'papaj' and datetime.now().isoweekday() == 4:
                board = BOARDS['normal']

            mbuttons = mbuttons[3:]
        else:
            board = BOARDS['normal']

        return board, mbuttons


def react(board, buttons):
        if not buttons:
            for board in CORNER_BOARDS:
                board.end_sounds()
        else:
            board.play(buttons)
        return

#
# def main():
#     pygame_init()
#     boards_init()
#
#     logging.info("Ready!")
#
#     state = [0] * len(constants.PHYS_MAPPING)
#     loop = ioloop.IOLoop.current()
#
#     t = Thread(target=handle_io_forever, args=(state,))
#     t.daemon = True
#     t.start()
#
#     sounds.WeatherSound.update_temperature()
#     cb = ioloop.PeriodicCallback(sounds.WeatherSound.update_temperature,
#                                  constants.WEATH_T)
#     cb.start()
#
#     loop.start()
#
# if __name__ == '__main__':
#     main()


def main():
    pass


if __name__ == "__main__":
    main()
