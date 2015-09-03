from soundboard.board import Board
from soundboard.controls import Joystick


def main():
    b = Board()
    b.register_sound_set('test')
    b.register_joystick(Joystick(0))
    b.run()


if __name__ == "__main__":
    main()
