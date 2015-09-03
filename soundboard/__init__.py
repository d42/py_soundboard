from soundboard.board import Board
from soundboard.sounds import SoundSet
from soundboard.controls import Joystick


def main():
    board = Board()
    board.register_sound_set(SoundSet('default'))


if __name__ == "__main__":
    main()
