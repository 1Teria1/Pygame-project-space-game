from MainGameLogic import *


def level_1(level_manager, ui_manager):
    level = MainLevelInitializer(level_manager, ui_manager, 1, "Приземлится на луну\n(желательно не разбиться)")
    flag = False
    while not flag:
        flag = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                flag = True
        level.screen.fill((0, 0, 125))
        render_rules(level)
        level.game.fps_clock.tick(level.game.fps)
        pygame.display.flip()

    a = Planet(100, 100, 0, -0.1, game=level.game, density=4, radius=1.6)
    b = Planet(120, 120, 100, game=level.game, density=4, radius=1)
    level.init_player(100, 98.2, 0, sprite_name="sprites/ship1.png", flame_sprite="sprites/flame.png",
                      goal=b.body, fuel_max=3, fuel_start=3)
    force = 8000
    b.body.ApplyForce(force * b2Vec2(1, -0.9), b.body.worldCenter, True)

    while level.running:
        answer = level.on_frame([a, b], [(60, 125, 60), (125, 125, 125)])
        if level.restart:
            level_1(level_manager, ui_manager)
        if answer is not None:
            return answer


def level_2(level_manager, ui_manager):
    level = MainLevelInitializer(level_manager, ui_manager, 2, "Вернуться и приземлиться на землю")

    a = Planet(100, 100, 0, -0.1, game=level.game, density=4, radius=1.6)
    b = Planet(120, 120, 100, game=level.game, density=4, radius=1)
    level.init_player(120, 119.8, 0, sprite_name="sprites/ship1.png", flame_sprite="sprites/flame.png",
                      goal=a.body, fuel_max=2, fuel_start=2)
    force = 8000
    b.body.ApplyForce(force * b2Vec2(1, -0.9), b.body.worldCenter, True)

    while level.running:
        answer = level.on_frame([a, b], [(60, 125, 60), (125, 125, 125)])
        if level.restart:
            level_1(level_manager, ui_manager)
        if answer is not None:
            return answer


def level_3(level_manager, ui_manager):
    level = MainLevelInitializer(level_manager, ui_manager, 3, "Взлететь и приземлится на марсе\n"
                                                               "(Подсказка: дождитесь пока марс станет ближе к земле)")

    sun = Planet(100, 100, 0, -0.1, game=level.game, density=12, radius=3.6)
    earth = Planet(113, 113, 100, game=level.game, density=4, radius=1)
    mars = Planet(130, 130, 0, -0.1, game=level.game, density=4, radius=0.6)
    level.init_player(113, 112, 0, sprite_name="sprites/ship1.png", flame_sprite="sprites/flame.png",
                      goal=mars.body, fuel_max=3, fuel_start=3)

    force = 30000
    earth.body.ApplyForce(force * 1.1 * b2Vec2(1, -1), earth.body.worldCenter, True)
    mars.body.ApplyForce(force / 4 * b2Vec2(1, -1), earth.body.worldCenter, True)

    while level.running:
        answer = level.on_frame([sun, earth, mars], [(255, 240, 90), (60, 125, 60), (200, 100, 30)])
        if level.restart:
            level_1(level_manager, ui_manager)
        if answer is not None:
            return answer


def level_4(level_manager, ui_manager):
    level = MainLevelInitializer(level_manager, ui_manager, 4, "Вернуться на землю")

    sun = Planet(100, 100, 0, -0.1, game=level.game, density=12, radius=3.6)
    earth = Planet(113, 113, 100, game=level.game, density=4, radius=1)
    mars = Planet(130, 130, 0, -0.1, game=level.game, density=4, radius=0.6)
    level.init_player(130, 129.8, 0, sprite_name="sprites/ship1.png", flame_sprite="sprites/flame.png",
                      goal=earth.body, fuel_max=3, fuel_start=3)

    force = 30000
    earth.body.ApplyForce(force * 1.1 * b2Vec2(1, -1), earth.body.worldCenter, True)
    mars.body.ApplyForce(force / 4 * b2Vec2(1, -1), earth.body.worldCenter, True)

    while level.running:
        answer = level.on_frame([sun, earth, mars], [(255, 240, 90), (60, 125, 60), (200, 100, 30)])
        if level.restart:
            level_1(level_manager, ui_manager)
        if answer is not None:
            return answer