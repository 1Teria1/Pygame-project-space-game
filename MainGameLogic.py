import pygame.sprite

from GameTools import *


class Game:
    def __init__(self, camera, sprites):
        self.tps = 200
        self.fps = 144
        self.time_interval = 0.001
        self.TPS_S = [50, 100, 200, 300, 500, 1000, 10000]
        self.INTERVALS = [0.05, 0.01, 0.006, 0.002, 0.001]

        self.camera = camera
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1920, 1080
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), 0, 32)
        self.fps_clock = pygame.time.Clock()
        self.tps_clock = pygame.time.Clock()
        self.world = b2World(contactListener=b2ContactListener(), gravity=(0.0, 0.0))
        self.all_sprites = sprites
        self.is_invincible = True
        self.frame_counter = 0

        self.G = 0.5
        self.planets = []
        self.power = 0

    def change_time(self, speed_up: bool):
        current = self.TPS_S.index(self.tps)

        if current == 0 and not speed_up:
            return

        if current == len(self.TPS_S) - 1 and speed_up:
            return

        self.tps = self.TPS_S[current + (1 if speed_up else -1)]

    def change_power(self, value: float):
        self.power += value
        self.power = 1 if self.power > 1 else self.power
        self.power = 0 if self.power < 0 else self.power

    def change_time1(self, speed_up: bool):
        current = self.INTERVALS.index(self.time_interval)

        if current == 0 and not speed_up:
            return

        if current == len(self.INTERVALS) - 1 and speed_up:
            return

        self.time_interval = self.INTERVALS[current + (1 if speed_up else -1)]

    def step(self):
        for bi in self.world.bodies:
            if isinstance(bi, Planet):
                if bi.static:
                    continue
            for bk in self.world.bodies:
                if bi == bk:
                    continue

                pi, pk = bi.worldCenter, bk.worldCenter
                mi, mk = bi.mass, bk.mass
                delta = pk - pi
                r = delta.length
                if abs(r) < 1.0:
                    r = 1.0

                force = self.G * mi * mk / (r * r)
                delta.Normalize()
                bi.ApplyForce(force * delta, pi, True)
        a = self.ship.body.linearVelocity.copy()
        self.world.Step(self.time_interval, 10, 100)
        b = self.ship.body.linearVelocity
        self.player_acceleration = pythagorean((a - b)[0], (a - b)[1])
        self.tps_clock.tick(self.tps)
        if self.frame_counter < 1000:
            self.frame_counter += 1
        if self.player_acceleration > 1.5 and self.frame_counter > 990:
            return True

    def init_player(self, ship, fuel_max, fuel_start):
        self.ship: Ship = ship
        self.fuel_max: float = fuel_max
        self.fuel_cur: float = fuel_start
        self.all_sprites.add(ship.current_flame_sprite)
        self.all_sprites.add(ship.current_sprite)
        self.player_acceleration = 0

    def add_planet(self, planet):
        self.planets.append(planet)

    def use_fuel(self, value):
        if self.fuel_cur <= 0:
            self.fuel_cur = 0
            return False

        self.fuel_cur -= value * self.time_interval
        return True

    def position_camera(self, gameobject):
        self.camera.set_pos(*gameobject.body.transform.position)


class GameObject:
    def __init__(self, left, top, game, sprite_name=None, static=False):
        self.static = static
        self.game = game
        self.create_fixture(b2Vec2(left, top), 1)
        self.sprite_name = sprite_name

    def create_fixture(self, pos, mass):
        pass

    def update(self):
        pass

    def render(self, surface: pygame.Surface, camera: Camera):
        pass


class Ship(GameObject):
    def __init__(self, x0, y0, phi, game, sprite_name=None, flame_sprite=None, goal=None):
        super().__init__(x0, y0, game=game, sprite_name=sprite_name)

        self.goal = goal
        self.is_fire = False

        self.sprite0 = pygame.sprite.Sprite()
        self.sprite0.image = load_image(sprite_name, colorkey=-1)
        self.sprite0.rect = self.sprite0.image.get_rect()
        self.current_sprite = pygame.sprite.Sprite()
        self.current_sprite.image = self.sprite0.image
        self.current_sprite.rect = self.sprite0.image.get_rect()

        self.flame_sprite0 = pygame.sprite.Sprite()
        self.flame_sprite0.image = load_image(flame_sprite, colorkey=-1)
        self.flame_sprite0.rect = self.flame_sprite0.image.get_rect()
        self.current_flame_sprite = pygame.sprite.Sprite()
        self.current_flame_sprite.image = self.flame_sprite0.image
        self.current_flame_sprite.rect = self.flame_sprite0.image.get_rect()

        self.phi = phi
        self.relative_velocity = self.body.linearVelocity - self.goal.linearVelocity

    def create_fixture(self, pos, mass):
        self.body = self.game.world.CreateDynamicBody(position=pos)
        self.body.CreatePolygonFixture(vertices=[(-0.25, -0.17), (0.25, -0.05), (0.25, 0.05), (-0.25, 0.17)], density=1, friction=0.3)

    def get_pos(self):
        return self.body.transform.position

    def boost(self, power: float):
        self.is_fire = True
        angle = self.body.transform.angle
        power = power * self.body.mass * self.game.power

        if self.game.use_fuel(power):
            self.body.ApplyForce(power * b2Vec2(cos(angle), sin(angle)), self.body.worldCenter, True)

    def render(self, surface: pygame.Surface, camera: Camera):
        screen_pos = camera.get_screen_pos(self.get_pos(), surface)
        size = camera.get_objects_size()
        angle = self.body.transform.angle
        self.update_sprite(screen_pos, self.phi + angle, size)

    def update_sprite(self, screen_pos, angle, size):
        a = self.current_sprite.image.get_rect()
        self.current_sprite.image = pygame.transform.scale(self.sprite0.image, (size / 1.8, size / 2.5))
        self.current_sprite.image = pygame.transform.rotate(self.current_sprite.image, -angle / pi * 180)
        self.current_sprite.rect.x = screen_pos[0] - a[2] // 2
        self.current_sprite.rect.y = screen_pos[1] - a[3] // 2
        if self.is_fire:
            b = self.current_flame_sprite.image.get_rect()
            self.current_flame_sprite.image = pygame.transform.scale(self.flame_sprite0.image, (size / 4, size / 4))
            self.current_flame_sprite.image = pygame.transform.rotate(self.current_flame_sprite.image, -angle / pi * 180)
            rotated_point = rotate_point(screen_pos + b2Vec2(0, size * 0.3), pi * 1.03 + angle, screen_pos)
            self.current_flame_sprite.rect.x = rotated_point[0] - b[2] // 2
            self.current_flame_sprite.rect.y = rotated_point[1] - b[3] // 2
        else:
            self.current_flame_sprite.rect.x = 100000
            self.current_flame_sprite.rect.y = 100000

    def update(self):
        self.relative_velocity = self.body.linearVelocity - self.goal.linearVelocity
        self.body.angularVelocity -= self.body.angularVelocity * 0.01

    def goal_achieved(self):
        if abs(pythagorean(self.relative_velocity[0], self.relative_velocity[1])) < 0.005\
                and len(self.body.contacts) != 0:
            return True
        return False


class Planet(GameObject):
    def __init__(self, left, top, speedx=0, speedy=0, /, density=3, radius=10, game=None, sprite_name=None, static=False):
        self.left = left
        self.top = top
        self.density = density
        self.radius = radius
        super().__init__(left, top, game=game, sprite_name=sprite_name, static=static)
        self.acc = b2Vec2()
        self.speed = b2Vec2(speedx, speedy)
        game.add_planet(self)

    def create_fixture(self, pos, mass):
        self.circle = b2FixtureDef(shape=b2CircleShape(radius=self.radius), density=self.density, friction=0.8, restitution=0.1)
        self.body = self.game.world.CreateDynamicBody(type=b2_dynamicBody, position=b2Vec2(self.left, self.top), fixtures=self.circle)

    def render(self, surface, camera, /, color=(255, 255, 255)):
        screen_pos = camera.get_screen_pos(self.body.transform.position, surface)
        size = camera.get_objects_size()
        radius = self.circle.shape.radius
        self.body.angularVelocity = 0
        if self.sprite_name is None:
            pygame.draw.circle(surface, color, (screen_pos[0], screen_pos[1]), radius * size)

    def __repr__(self):
        return f"Planet({self.body.transform.position}, mass={self.body.mass})"


class MainLevelInitializer:
    def __init__(self, level_manager, ui_manager, num, goal_message):
        self.size = self.width, self.height = 1920, 1080
        self.goal_message = goal_message
        self.explosion_sprite0 = pygame.sprite.Sprite()
        self.explosion_sprite0.image = load_image("sprites/boom.png")
        self.explosion_sprite0.rect = self.explosion_sprite0.image.get_rect()
        self.explosion_sprite0.rect.x, self.explosion_sprite0.rect.y = self.width // 2 - 100, self.height // 2 - 100
        self.explosion_sprite = pygame.sprite.Sprite()
        self.explosion_sprite.image = self.explosion_sprite0.image
        self.explosion_sprite.rect = self.explosion_sprite.image.get_rect()
        self.explosion_sprite.rect.x, self.explosion_sprite.rect.y = self.width // 2 - 100, self.height // 2 - 100
        self.level_manager = level_manager
        self.ui_manager = ui_manager
        self.num = num
        pygame.init()
        pygame.display.set_caption(f'Уровень {num}')

        self.screen = pygame.display.set_mode(self.size)
        self.camera = Camera(b2Vec2(self.width, self.height), 0.01)

        self.all_sprites = pygame.sprite.Group()
        background = pygame.sprite.Sprite()
        background.image = load_image("sprites/background3.jpg")
        background.rect = background.image.get_rect()
        background.rect.x, background.rect.y = 0, 0
        self.all_sprites.add(background)

        self.game = Game(self.camera, self.all_sprites)
        self.ui = InGameUI(self.game)

        self.clock = pygame.time.Clock()
        self.pause_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((self.width - 120, 20), (100, 100)),
                                                         text="Пауза")
        self.exit_menu_button = None
        self.next_level_button = None

        self.running = True
        self.failed = False
        self.passed = False
        self.restart = False

    def init_player(self, x0, y0, phi, sprite_name, flame_sprite, goal, fuel_max, fuel_start):
        self.ship = Ship(x0, y0, phi, self.game, sprite_name, flame_sprite, goal)
        self.ship.body.angle = -pi / 2
        self.game.init_player(self.ship, fuel_max, fuel_start)

    def on_frame(self, planets: list[Planet], colors):
        events = pygame.event.get()
        self.running, time_delta = general_input_manager(pygame.key.get_pressed(), events, self)
        if not self.running:
            self.pause_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((self.width - 120, 20), (100, 100)),
                text="Пауза")
        self.screen.fill((0, 0, 0))
        self.all_sprites.draw(self.screen)
        if not self.failed and not self.passed:
            a = self.game.step()
            if a:
                self.game.all_sprites.add(self.explosion_sprite)
                self.game.all_sprites.remove(self.game.ship.current_sprite)
                pygame.display.flip()
                self.failed = True
                self.ui_manager.clear_and_reset()
                failing_level_ui(self)
        elif self.failed:
            screen_pos = self.camera.get_screen_pos(self.ship.get_pos(), self.screen)
            size = self.camera.get_objects_size()
            a = self.explosion_sprite.image.get_rect()
            self.explosion_sprite.image = pygame.transform.scale(self.explosion_sprite0.image, (size, size))
            self.explosion_sprite.rect.x = screen_pos[0] - a[2] // 2
            self.explosion_sprite.rect.y = screen_pos[1] - a[3] // 2
            self.ui.show_failing_message(self.screen, self.screen.get_size())
        elif self.passed:
            self.ui.show_winning_message(self.screen, self.screen.get_size())

        self.game.position_camera(self.ship)
        for i, planet in enumerate(planets):
            planet.render(self.screen, self.camera, color=colors[i])
        self.ship.update()
        self.ship.render(self.screen, self.camera)
        self.ui.render(self.screen)
        self.ui.show_goal(f"{self.goal_message}", self.screen, self.screen.get_size())
        self.ui_manager.update(time_delta)
        self.ui_manager.draw_ui(self.screen)

        pygame.display.flip()
        if self.game.ship.goal_achieved() and not self.passed:
            with open("level_completion.txt", "r") as file:
                q = file.read()
            with open("level_completion.txt", "w") as file:
                for i, value in enumerate(q):
                    if i == self.num - 1:
                        file.write('1')
                    else:
                        file.write(value)
            self.passed = True
            self.ui_manager.clear_and_reset()
            passed_level_ui(self)


def render_rules(level):
    font = pygame.font.Font(None, level.width // 30)
    text = font.render("Пробел - включение двигателя,\n\n"
                       "Shift/Ctrl - установка мощности двигателя (индикатор слева-снизу)\n\n"
                       "A/D - поворот ракеты\n\n"
                       "По центру скорость: глобальная и относительная (относительно цели)\n\n"
                       "Колёсико мыши - приближение/отдаление камеры\n\n"
                       "Стрелочки вверх/вниз - ускорение/замедление времени\n\n"
                       "Стрелочки вправо/влево - вращение камеры", True, (255, 255, 100))
    text_x = level.width // 2 - text.get_width() // 2
    text_y = level.height // 2 - text.get_height() // 2
    level.screen.blit(text, (text_x, text_y))