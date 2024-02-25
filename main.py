from pygame_gui import UIManager
import os
from Scenes import *


def p(*args, **kwargs):
    pass


levels = [level_1, level_2, level_3, level_4, p, p, p, p, p, p, p, p, p, p, p, p, p, p, p, p]


def level_manager(level_num: int):
    return levels[level_num]


def main():
    if not os.path.isfile("level_completion.txt"):
        with open("level_completion.txt", "w") as file:
            for i in range(20):
                file.write('0')
    pygame.init()
    UI_manager: UIManager = pygame_gui.UIManager((1920, 1080))
    main_menu(level_manager, UI_manager)


if __name__ == "__main__":
    main()
