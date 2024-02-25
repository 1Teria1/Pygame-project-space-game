import os
import sys
from math import e, sin, cos, pi, acos, asin
from Box2D import *
import pygame
import pygame_gui


def pythagorean(a, b):
    return (a ** 2 + b ** 2) ** 0.5


def load_image(name, colorkey=None):
    fullname = name
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def get_angle(point, axis):
    new_point = (point - axis)
    if new_point.length == 0:
        return 0

    new_point /= new_point.length
    if asin(new_point[1]) < 0:
        return -acos(new_point[0])

    return acos(new_point[0])


def rotate_point(self, phi, axis):
    new_point = axis - self
    return axis + Box2D.b2Vec2(cos(phi) * new_point.length, sin(phi) * new_point.length)


class Camera:
    def __init__(self, start_pos: Box2D.b2Vec2, start_zoom: float, start_angle: float = 0):
        self.pos = start_pos
        self.zoom = start_zoom
        self.angle = start_angle

    def move(self, left: float, top: float):
        self.pos += Box2D.b2Vec2(left, top)

    def set_angle(self, new_angle: float):
        self.angle = new_angle

    def get_screen_rect(self):
        a, b = self.zoom * 16 * 100, self.zoom * 9 * 100
        return self.pos, self.pos + Box2D.b2Vec2(a, b)

    def get_screen_size(self):
        a, b = self.zoom * 16 * 100, self.zoom * 9 * 100
        return Box2D.b2Vec2(a, b)

    def set_zoom(self, zoom: float):
        if zoom <= 0:
            raise ValueError("Negative zoom")
        self.zoom = zoom

    def change_zoom(self, value: float):
        if self.zoom + value <= 0.0001:
            self.zoom = abs(value)
            return
        self.zoom += value

    def get_screen_pos(self, global_pos: Box2D.b2Vec2, surface: pygame.Surface):
        a = ((global_pos - self.pos) / self.zoom) + Box2D.b2Vec2(*surface.get_size()) / 2
        angle = get_angle(global_pos, self.pos)
        return rotate_point(a, self.angle + angle, b2Vec2(surface.get_size()) / 2)

    def get_objects_size(self):
        return 1 / self.zoom

    def set_pos(self, left: float, top: float):
        self.pos = Box2D.b2Vec2(left, top)


class InGameUI:
    def __init__(self, game):
        self.game = game

    def render(self, surface):
        size = surface.get_size()

        self.show_fuel(surface, size)
        self.show_velocity(surface, size)
        self.show_power(surface, size)

    def show_fuel(self, surface, size):
        rem_fuel = self.game.fuel_cur / self.game.fuel_max
        font = pygame.font.Font(None, size[0] // 70)
        text = font.render(f"Топливо\n  {round(rem_fuel * 100)}%", True, (255, 255, 100))
        surface.blit(text, (size[0] - text.get_width(), size[1] - 300 - text.get_height()))
        pygame.draw.rect(surface, (40, 140, 30), (size[0] - 60, size[1] - 295 * rem_fuel - 5, 55, 295 * rem_fuel))
        pygame.draw.rect(surface, (255, 255, 255), (size[0] - 60, size[1] - 300, 55, 295), width=5)

    def show_velocity(self, surface, size):
        vec = self.game.ship.body.linearVelocity
        rel_vec = self.game.ship.relative_velocity
        velocity = f"      Скорость:\n      глобальная: {str(round((pythagorean(vec[0], vec[1]) * 50)) / 10)}\n" \
                   f"относительная: {str(round((pythagorean(rel_vec[0], rel_vec[1]) * 50)) / 10)}"
        color = (255, 255, 100)
        if self.game.ship.goal_achieved():
            color = (100, 255, 255)

        font = pygame.font.Font(None, size[0] // 30)
        text = font.render(velocity, True, color)
        text_x = size[0] // 2 - text.get_width() // 2
        text_y = size[1] - text.get_height()
        surface.blit(text, (text_x, text_y))



    def show_power(self, surface, size):
        power = self.game.power
        font = pygame.font.Font(None, size[0] // 70)
        text = font.render(f"Мощность\n{round(power * 100)}%", True, (255, 255, 100))
        surface.blit(text, (3, size[1] - 300 - text.get_height()))
        pygame.draw.rect(surface, (230, 100, 40), (5, size[1] - 295 * power - 5, 55, 295 * power))
        pygame.draw.rect(surface, (255, 255, 255), (5, size[1] - 300, 55, 295), width=5)

    @staticmethod
    def show_winning_message(surface, size):
        font = pygame.font.Font(None, size[0] // 20)
        text = font.render(f"Уровень пройден!", True, (255, 255, 100))
        surface.blit(text, (size[0] // 2 - text.get_width() // 2, 100))

    @staticmethod
    def show_failing_message(surface, size):
        font = pygame.font.Font(None, size[0] // 20)
        text = font.render(f"Корабль разбился!", True, (255, 255, 100))
        surface.blit(text, (size[0] // 2 - text.get_width() // 2, 100))

    @staticmethod
    def show_goal(string: str, surface, size):
        font = pygame.font.Font(None, size[0] // 40)
        text = font.render(f"Цель:\n{string}", True, (200, 255, 255))
        surface.blit(text, (15, 15))


def main_menu(level_manager, ui_manager):
    pygame.init()
    pygame.display.set_caption('Планетошки')
    size = width, height = 1920, 1080
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    background = pygame.sprite.Sprite()
    background.image = load_image("sprites/background3.jpg")
    background.rect = background.image.get_rect()
    background.rect.x, background.rect.y = 0, 0
    all_sprites.add(background)

    clock = pygame.time.Clock()
    play_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((width // 2 - 150, height // 2 - 100),
                                                                         (300, 100)), text="Играть")
    exit_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((width // 2 - 150, height // 2 + 100),
                                                                         (300, 100)), text="Выйти из игры")
    running = True
    while running:
        time_delta = clock.tick()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == play_button:
                        ui_manager.clear_and_reset()
                        a = level_select_menu(level_manager, ui_manager)
                        if a:
                            return
                        play_button = pygame_gui.elements.UIButton(
                            relative_rect=pygame.Rect((width // 2 - 150, height // 2 - 100),
                                                      (300, 100)), text="Играть")
                        exit_button = pygame_gui.elements.UIButton(
                            relative_rect=pygame.Rect((width // 2 - 150, height // 2 + 100),
                                                      (300, 100)), text="Выйти из игры")
                    if event.ui_element == exit_button:
                        sys.exit(0)
            ui_manager.process_events(event)
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        ui_manager.update(time_delta)
        ui_manager.draw_ui(screen)

        pygame.display.flip()


def escape_menu(level_manager, ui_manager):
    pygame.init()
    pygame.display.set_caption('Планетошки')
    size = width, height = 1920, 1080
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    background = pygame.sprite.Sprite()
    background.image = load_image("sprites/background2.jpg")
    background.rect = background.image.get_rect()
    background.rect.x, background.rect.y = 0, 0
    all_sprites.add(background)

    clock = pygame.time.Clock()
    continue_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((width // 2 - 150, height // 2 - 100),
                                                                             (300, 100)), text="Продолжить")
    exit_menu_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((width // 2 - 150, height // 2 + 100),
                                                                              (300, 100)), text="Выйти в главное меню")
    exit_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((width // 2 - 150, height // 2 + 200),
                                                                         (300, 100)), text="Выйти из игры")
    running = True
    while running:
        time_delta = clock.tick()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == continue_button:
                        ui_manager.clear_and_reset()
                        return
                    if event.ui_element == exit_menu_button:
                        ui_manager.clear_and_reset()
                        return True
                    if event.ui_element == exit_button:
                        sys.exit(0)
            ui_manager.process_events(event)
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        ui_manager.update(time_delta)
        ui_manager.draw_ui(screen)

        pygame.display.flip()


def level_select_menu(level_manager, ui_manager):
    pygame.init()
    pygame.display.set_caption('Планетошки')
    size = width, height = 1920, 1080
    screen = pygame.display.set_mode(size)

    all_sprites = pygame.sprite.Group()
    background = pygame.sprite.Sprite()
    background.image = load_image("sprites/background1.jpg")
    background.rect = background.image.get_rect()
    background.rect.x, background.rect.y = 0, 0
    all_sprites.add(background)
    level_buttons = []

    clock = pygame.time.Clock()
    back_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 10),
                                                                         (300, 100)), text="Назад")
    with open("level_completion.txt", "r") as file:
        q = file.read()
    for i in range(4):
        for j in range(5):
            msg = ''
            if q[len(level_buttons) - 1] == '0' and len(level_buttons) != 0:
                msg = "[Недоступен]"
            level_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((400 + j * 240, 100 + i * 240),
                                                                                  (230, 200)),
                                                        text=f"Уровень {len(level_buttons) + 1} {msg}")
            level_buttons.append(level_button)
    running = True
    while running:
        time_delta = clock.tick()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    ui_manager.clear_and_reset()
                    return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == back_button:
                        ui_manager.clear_and_reset()
                        return False
                    if event.ui_element in level_buttons:
                        ind = level_buttons.index(event.ui_element)
                        with open("level_completion.txt", "r") as file:
                            q = file.read()
                            if not q[ind - 1] == '1' and not ind == 0:
                                continue
                        ui_manager.clear_and_reset()
                        a = level_manager(level_buttons.index(event.ui_element))(level_manager, ui_manager)
                        return a
            ui_manager.process_events(event)
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        ui_manager.update(time_delta)
        ui_manager.draw_ui(screen)
        pygame.display.flip()


def failing_level_ui(current_level):
    current_level.exit_menu_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(
        (current_level.width // 2 - 150, current_level.height // 2 + 100),
        (300, 200)), text="Выйти в главное меню")


def passed_level_ui(current_level):
    current_level.next_level_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(
        (current_level.width // 2 + 150, current_level.height // 2),
        (300, 200)), text="Следующий уровень")
    current_level.exit_menu_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect(
        (current_level.width // 2 - 450, current_level.height // 2),
        (300, 200)), text="Выйти в главное меню")


def general_input_manager(keys, events, level):
    time_delta = level.clock.tick()
    if keys[pygame.K_a]:
        level.game.ship.body.angularVelocity -= 20 * level.game.time_interval
    if keys[pygame.K_d]:
        level.game.ship.body.angularVelocity += 20 * level.game.time_interval
    if keys[pygame.K_LSHIFT]:
        level.game.change_power(0.005)
    if keys[pygame.K_LCTRL]:
        level.game.change_power(-0.005)
    if keys[pygame.K_SPACE]:
        level.game.ship.boost(6)
    else:
        level.game.ship.is_fire = False
    if keys[pygame.K_LEFT]:
        level.game.camera.angle -= 0.01
        level.game.ship.phi -= 0.01
    if keys[pygame.K_RIGHT]:
        level.game.camera.angle += 0.01
        level.game.ship.phi += 0.01

    for event in events:
        if event.type == pygame.QUIT:
            sys.exit()

        level.ui_manager.process_events(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                level.game.change_time1(True)
            elif event.key == pygame.K_UP:
                level.game.change_time1(False)
            elif event.key == pygame.K_ESCAPE:
                level.ui_manager.clear_and_reset()
                a = escape_menu(level.level_manager, level.ui_manager)
                if a:
                    return False, 1
                else:
                    level.pause_button = pygame_gui.elements.UIButton(
                        relative_rect=pygame.Rect((level.width - 120, 20), (100, 100)),
                        text="Пауза")

        elif event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == level.pause_button:
                    level.ui_manager.clear_and_reset()
                    a = escape_menu(level.level_manager, level.ui_manager)
                    if a:
                        return False, 1
                    else:
                        level.pause_button = pygame_gui.elements.UIButton(
                            relative_rect=pygame.Rect((level.width - 120, 20), (100, 100)),
                            text="Пауза")
                if event.ui_element == level.next_level_button:
                    level.ui_manager.clear_and_reset()
                    level.level_manager(level.num)(level.level_manager, level.ui_manager)
                    return False, 1
                if event.ui_element == level.exit_menu_button:
                    level.ui_manager.clear_and_reset()
                    return False, 1

        elif event.type == pygame.MOUSEWHEEL:
            level.game.camera.change_zoom(event.y * -0.001)

    return True, time_delta
