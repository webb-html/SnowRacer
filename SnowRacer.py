import arcade
from arcade.gui import UIManager, UIFlatButton, UILabel,UITextureButtonStyle, UIInputText
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

SCALE = 1.5

TILE_WIDTH = 16

SCREEN_WIDTH = 16 * TILE_WIDTH * SCALE
SCREEN_HEIGHT = 20 * TILE_WIDTH * SCALE
SCREEN_TITLE = 'Snow Racer'

CAMERA_LERP = 1
CAMERA_DEAD_ZONE_W = int(SCREEN_WIDTH * 0.25)

class Racer(arcade.Sprite):
    def __init__(self, position_x, position_y, start_speed):
        super().__init__()
        self.scale = SCALE
        self.speed_y = start_speed
        self.speed_x = 200

        self.slow_texture = arcade.load_texture("images/character/character_slow.png")
        self.fast_texture = arcade.load_texture('images/character/character_fast.png')
        self.texture = self.slow_texture

        self.center_x = position_x
        self.center_y = position_y

    def update(self,delta_time, boost, keys_pressed, **kwargs):
        if kwargs:
            if type(kwargs['speed']) == type(0):
                self.speed_y = kwargs['speed']
            elif kwargs['speed'][0] == '/':
                self.speed_y /= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '-':
                self.speed_y -= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '*':
                self.speed_y *= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '+':
                self.speed_y += float(kwargs['speed'][1:])
        if self.speed_y < 0:
            self.speed_y = 0
        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed_x * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed_x * delta_time
        if arcade.key.UP in keys_pressed or arcade.key.W in keys_pressed:
            pass
        dy -= self.speed_y * delta_time

        self.center_x += dx
        self.center_y += dy
        self.speed_y += boost

    def update_texture(self):
        if self.speed_y > 200:
            self.texture = self.fast_texture
        else:
            self.texture = self.slow_texture


class Monster(arcade.Sprite):
    def __init__(self,position_x, position_y, prey, speed, distance_to_boost):
        super().__init__()
        self.scale = SCALE
        self.speed = speed

        self.run_textures = []
        self.run_textures.append(arcade.load_texture("images/monster/monster_run_1.png"))
        self.run_textures.append(arcade.load_texture("images/monster/monster_run_2.png"))
        self.attack_texture = arcade.load_texture('images/monster/monster_attack.png')
        self.texture = self.run_textures[0]

        self.center_x = position_x
        self.center_y = position_y

        self.prey = prey

        self.distance_to_boost = distance_to_boost

        self.current_texture = 0
        self.texture_change_time = 0
        self.texture_change_delay = 0.1
        self.is_running = False

    def update(self, delta_time):
        dx, dy = 0, 0
        if self.prey.center_x - self.center_x < 0.3 * TILE_WIDTH * SCALE:
            dx -= self.speed * delta_time
        if self.prey.center_x - self.center_x > -0.3 * TILE_WIDTH * SCALE:
            dx += self.speed * delta_time
        if self.prey.center_y - self.center_y < -1 * TILE_WIDTH * SCALE:
            dy -= self.speed * delta_time

        if dy != 0 or dx != 0:
            self.is_running = True
        else:
            self.is_running = False

        self.center_x += dx
        self.center_y += dy

        self.center_y = min(self.center_y, self.prey.center_y + TILE_WIDTH * SCALE * self.distance_to_boost)

    def update_animation(self, delta_time: float = 1/60):
        if self.is_running:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture >= len(self.run_textures):
                    self.current_texture = 0
                self.texture = self.run_textures[self.current_texture]
        else:
            self.texture = self.attack_texture


class SnowRacerGame(arcade.View):
    def __init__(self, difficulty='medium'):
        super().__init__()

        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()

        self.tile_map = None

        self.racer_list = arcade.SpriteList()
        self.racer: arcade.Sprite | None = None

        self.monster_list = arcade.SpriteList()
        self.monster: arcade.Sprite | None = None

        self.difficulty = difficulty

        self.setup()

    def setup(self):

        self.tile_map = arcade.load_tilemap('trace.tmx', scaling=SCALE)
        self.floar_list = self.tile_map.sprite_lists['floar']
        self.shadow_list = self.tile_map.sprite_lists['shadows']
        self.nature_list = self.tile_map.sprite_lists['nature']
        self.tramplins = self.tile_map.sprite_lists['tramplins']
        self.nets = self.tile_map.sprite_lists['nets']
        self.barriers = self.tile_map.sprite_lists['barriers']
        self.lap_list = self.tile_map.sprite_lists['laps']
        self.collision_list = self.tile_map.sprite_lists["collision"]

        self.world_width = int(self.tile_map.width * self.tile_map.tile_width * SCALE)
        self.world_height = int(self.tile_map.height * self.tile_map.tile_height * SCALE)

        if self.difficulty == 'easy':
            raser_start_speed = 150
            self.boost = 1
            monster_speed = 100
            monster_distance_to_boost = 8
        elif self.difficulty == 'hard':
            raser_start_speed = 155
            self.boost = 0.25
            monster_speed = 175
            monster_distance_to_boost = 4
        else:
            raser_start_speed = 100
            self.boost = 0.5
            monster_speed = 150
            monster_distance_to_boost = 6

        self.racer = Racer(SCALE * TILE_WIDTH * 23, SCALE * TILE_WIDTH * 158, raser_start_speed)
        self.racer_list.append(self.racer)

        self.monster = Monster(SCALE * TILE_WIDTH * 23, SCALE * TILE_WIDTH * 169, self.racer, monster_speed, monster_distance_to_boost)
        self.monster_list.append(self.monster)

        self.keys_pressed = set()

        self.physics_engine = arcade.PhysicsEngineSimple(
        self.racer, self.collision_list)

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_update(self, delta_time):
        boost = 1

        if self.racer.center_y < SCALE * TILE_WIDTH * 15:
            teleport_sprites(self.racer, self.monster)

        collision_with_barriers = arcade.check_for_collision_with_list(self.racer, self.barriers)
        collision_with_nets = arcade.check_for_collision_with_list(self.racer, self.nets)
        collision_with_tramplins = arcade.check_for_collision_with_list(self.racer, self.tramplins)
        if collision_with_tramplins:
            self.racer_list.update(delta_time, boost, self.keys_pressed, speed=f'+{boost * 5}')
        elif collision_with_nets:
            self.racer_list.update(delta_time, boost, self.keys_pressed, speed=f'-{boost * 5}')
        elif collision_with_barriers:
            self.racer_list.update(delta_time, 0, self.keys_pressed, speed=f'/1.5')
        else:
            self.racer_list.update(delta_time, boost, self.keys_pressed)

        self.racer.update_texture()

        self.monster.update(delta_time)
        self.monster.update_animation()

        collision_with_monster = arcade.check_for_collision(self.racer, self.monster)
        if collision_with_monster:
            self.window.show_view(GameOverView())

        self.physics_engine.update()

        cam_x, cam_y = self.world_camera.position
        dz_left = cam_x - CAMERA_DEAD_ZONE_W // 2
        dz_right = cam_x + CAMERA_DEAD_ZONE_W // 2

        px, py = self.racer.center_x, self.racer.center_y
        target_x, target_y = cam_x, cam_y

        if px < dz_left:
            target_x = px + CAMERA_DEAD_ZONE_W // 2
        elif px > dz_right:
            target_x = px - CAMERA_DEAD_ZONE_W // 2
        if py < cam_y:
            target_y = py
        elif py > cam_y:
            target_y = py

        half_w = self.world_camera.viewport_width / 2
        half_h = self.world_camera.viewport_height / 2
        target_x = max(half_w, min(self.world_width - half_w, target_x))
        target_y = max(half_h, min(self.world_height - half_h, target_y))

        smooth_x = (1 - CAMERA_LERP) * cam_x + CAMERA_LERP * target_x
        smooth_y = (1 - CAMERA_LERP) * cam_y + CAMERA_LERP * target_y
        self.cam_target = (smooth_x, smooth_y)

        self.world_camera.position = (self.cam_target[0], self.cam_target[1])

    def on_draw(self):
        self.clear()

        self.world_camera.use()

        self.floar_list.draw()
        self.shadow_list.draw()
        self.tramplins.draw()
        self.nets.draw()
        self.barriers.draw()
        self.nature_list.draw()
        self.monster_list.draw()
        self.racer_list.draw()
        self.lap_list.draw()

        self.gui_camera.use()


class MainView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((183,210,235, 255))

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        name_of_game = UILabel('Snow Racer', text_color=arcade.color.WHITE,
                       font_name='Karmatic Arcade', font_size=30)
        self.box_layout.add(name_of_game)

        button_style = {'hover': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'normal': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'press': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade',
                                                      font_color=(200, 200, 200, 255))}

        input_name = UIInputText(width=200, height=30, text="input name", font_name='Karmatic Arcade', font_size=15)
        self.box_layout.add(input_name)

        start_button = UIFlatButton(text='Start game', width=200, height=50, style=button_style)
        start_button.on_click = self.select_diffculty
        self.box_layout.add(start_button)

        score_button = UIFlatButton(text='Score table', width=200, height=50, style=button_style)
        self.box_layout.add(score_button)

        exit_button = UIFlatButton(text='Exit', width=200, height=50, style=button_style)
        exit_button.on_click = lambda event: arcade.exit()
        self.box_layout.add(exit_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def select_diffculty(self, event):
        select_difficulty = SelectDifficultyView()
        self.window.show_view(select_difficulty)
        '''
        game_view = SnowRacerGame()
        game_view.setup()
        self.window.show_view(game_view)
        '''


class SelectDifficultyView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color((183, 210, 235, 255))

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=False, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        button_style = {'hover': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'normal': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'press': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade',
                                                      font_color=(200, 200, 200, 255))}

        easy_difficulty_button = UIFlatButton(text='Easy', width=100, height=100, style=button_style)
        easy_difficulty_button.on_click = self.start_easy_game
        self.box_layout.add(easy_difficulty_button)

        medium_difficulty_button = UIFlatButton(text='Medium', width=100, height=100, style=button_style)
        medium_difficulty_button.on_click = self.start_medium_game
        self.box_layout.add(medium_difficulty_button)

        hard_difficulty_button = UIFlatButton(text='Hard', width=100, height=100, style=button_style)
        hard_difficulty_button.on_click = self.start_hard_game
        self.box_layout.add(hard_difficulty_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def start_easy_game(self, event):
        self.window.show_view(SnowRacerGame(difficulty='easy'))

    def start_medium_game(self, event):
        self.window.show_view(SnowRacerGame())

    def start_hard_game(self, event):
        self.window.show_view(SnowRacerGame(difficulty='hard'))


class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        button_style = {'hover': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'normal': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'press': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade',
                                                      font_color=(200, 200, 200, 255))}

        lose_text = UILabel("Game Over", font_size=30, font_name='Karmatic Arcade')
        self.box_layout.add(lose_text)

        to_menu_button = UIFlatButton(text='Back to main menu', width=250, height=50, style=button_style)
        to_menu_button.on_click = self.to_main_menu
        self.box_layout.add(to_menu_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def to_main_menu(self, event):
        self.window.show_view(MainView())

def teleport_sprites(*args):
    for sprite in args:
        sprite.center_y += SCALE * TILE_WIDTH * 144

def main():
    arcade.load_font('font.ttf')
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MainView())
    arcade.run()

if __name__ == "__main__":
    main()