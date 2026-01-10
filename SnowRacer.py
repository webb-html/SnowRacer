from random import sample

import arcade
from arcade.gui import UIManager, UIFlatButton, UILabel, UITextureButtonStyle, UIInputText, UITextArea, UISlider
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

from pyglet.graphics import Batch

SCALE = 1.5

TILE_WIDTH = 16

SCREEN_WIDTH = 16 * TILE_WIDTH * SCALE
SCREEN_HEIGHT = 20 * TILE_WIDTH * SCALE
SCREEN_TITLE = 'Snow Racer'

CAMERA_LERP = 1
CAMERA_DEAD_ZONE_W = int(SCREEN_WIDTH * 0.25)

class Racer(arcade.Sprite):
    def __init__(self, position_x, position_y, start_speed, schore_modificator):
        super().__init__()
        self.scale = SCALE
        self.speed_y = start_speed
        self.speed_x = 200

        self.slow_texture = arcade.load_texture("images/character/character_slow.png")
        self.fast_texture = arcade.load_texture('images/character/character_fast.png')
        self.texture = self.slow_texture

        self.center_x = position_x
        self.center_y = position_y

        self.score = 0
        self.score_modificator = schore_modificator

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

        self.score +=0.001 * self.speed_y * self.score_modificator

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
    def __init__(self, name, media_player=None ,difficulty='medium'):
        super().__init__()

        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()

        self.tile_map = None

        self.racer_list = arcade.SpriteList()
        self.racer: arcade.Sprite | None = None

        self.monster_list = arcade.SpriteList()
        self.monster: arcade.Sprite | None = None

        self.difficulty = difficulty
        self.name = name

        self.media_player = media_player

        self.setup()

        self.keys_pressed = set()

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
            score_modificator = 0.5
        elif self.difficulty == 'hard':
            raser_start_speed = 155
            self.boost = 0.25
            monster_speed = 175
            monster_distance_to_boost = 4
            score_modificator = 1
        else:
            raser_start_speed = 100
            self.boost = 0.5
            monster_speed = 150
            monster_distance_to_boost = 6
            score_modificator = 1.5

        self.racer = Racer(SCALE * TILE_WIDTH * 23, SCALE * TILE_WIDTH * 158, raser_start_speed, score_modificator)
        self.racer_list.append(self.racer)

        self.monster = Monster(SCALE * TILE_WIDTH * 23, SCALE * TILE_WIDTH * 169, self.racer, monster_speed,
                               monster_distance_to_boost)
        self.monster_list.append(self.monster)

        self.batch = Batch()
        self.score = arcade.Text('0', 20, SCREEN_HEIGHT - 34, arcade.color.BLACK, 14,
                             font_name='Karmatic Arcade', batch=self.batch)

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

        self.score = arcade.Text(str(round(self.racer.score)), 20, SCREEN_HEIGHT - 34, arcade.color.BLACK,
                                 14, font_name='Karmatic Arcade', batch=self.batch)


        self.monster.update(delta_time)
        self.monster.update_animation()

        collision_with_monster = arcade.check_for_collision(self.racer, self.monster)
        if collision_with_monster:
            self.window.show_view(GameOverView(str(round(self.racer.score)), self.name, media_player=self.media_player))

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
        self.batch.draw()


class MainView(arcade.View):
    def __init__(self, media_player=None):
        super().__init__()
        arcade.set_background_color((183,210,235, 255))

        self.name = 'Incognito'

        self.media_player = media_player

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
        input_name.on_change = self.write_name
        self.box_layout.add(input_name)

        start_button = UIFlatButton(text='Start game', width=200, height=50, style=button_style)
        start_button.on_click = self.select_diffculty
        self.box_layout.add(start_button)

        score_button = UIFlatButton(text='Score table', width=200, height=50, style=button_style)
        score_button.on_click = self.to_score_table
        self.box_layout.add(score_button)

        settings_button = UIFlatButton(text='Settings', width=200, height=50, style=button_style)
        settings_button.on_click = self.to_settings
        self.box_layout.add(settings_button)

        exit_button = UIFlatButton(text='Exit', width=200, height=50, style=button_style)
        exit_button.on_click = lambda event: arcade.exit()
        self.box_layout.add(exit_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def select_diffculty(self, event):
        select_difficulty = SelectDifficultyView(self.name, self.media_player)
        self.window.show_view(select_difficulty)

    def to_score_table(self, event):
        score_table = ScoreTableView(media_player=self.media_player)
        self.window.show_view(score_table)

    def to_settings(self, event):
        settings = SettingsView(media_player=self.media_player)
        self.window.show_view(settings)

    def write_name(self, text):
        if text != 'input name':
            self.name= text.new_value.strip()


class SelectDifficultyView(arcade.View):
    def __init__(self, name, media_player=None):
        super().__init__()
        arcade.set_background_color((183, 210, 235, 255))

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=False, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

        self.name = name
        self.media_player = media_player


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
        self.window.show_view(SnowRacerGame(self.name, difficulty='easy', media_player=self.media_player))

    def start_medium_game(self, event):
        self.window.show_view(SnowRacerGame(self.name, media_player=self.media_player))

    def start_hard_game(self, event):
        self.window.show_view(SnowRacerGame(self.name, difficulty='hard', media_player=self.media_player))


class GameOverView(arcade.View):
    def __init__(self, score, name, media_player=None):
        super().__init__()

        self.score = score
        write_score(score, name)

        self.media_player = media_player

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

        score_text = UILabel(f"Score: {self.score}", font_size=15, font_name='Karmatic Arcade')
        self.box_layout.add(score_text)

        to_menu_button = UIFlatButton(text='Back to main menu', width=250, height=50, style=button_style)
        to_menu_button.on_click = self.to_main_menu
        self.box_layout.add(to_menu_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def to_main_menu(self, event):
        self.window.show_view(MainView(media_player=self.media_player))


class ScoreTableView(arcade.View):
    def __init__(self, media_player=None):
        super().__init__()

        self.media_player = media_player

        with open('score_table.txt', 'r', encoding='utf-8') as file:
            self.scores = file.readlines()

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

        text_area = UITextArea(text=''.join(self.scores), width=350, height=300, font_size=16,
                               font_name='Karmatic Arcade')
        self.box_layout.add(text_area)

        to_menu_button = UIFlatButton(text='Back to main menu', width=250, height=50, style=button_style)
        to_menu_button.on_click = self.to_main_menu
        self.box_layout.add(to_menu_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def to_main_menu(self, event):
        self.window.show_view(MainView(media_player=self.media_player))


class SettingsView(arcade.View):
    def __init__(self, media_player=None):
        super().__init__()

        self.media_player: None | MediaPlayer = media_player

        with open('settings.txt', 'r', encoding='utf-8') as file:
            self.settings = file.readlines()

        self.manager = UIManager()
        self.manager.enable()
        self.anchor_layout = UIAnchorLayout()
        self.box_layout = UIBoxLayout(vertical=True, space_between=20)

        self.volume_layout = UIBoxLayout(vertical=False, space_between=10)

        self.select_track_layout = UIBoxLayout(vertical=True, space_between=5)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)
        self.manager.add(self.anchor_layout)

    def setup_widgets(self):
        button_style = {'hover': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'normal': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade'),
                        'press': UITextureButtonStyle(font_size=12, font_name='Karmatic Arcade',
                                                      font_color=(200, 200, 200, 255))}
        switch_music_button = UIFlatButton(text='switch music', width=300, height=50, style=button_style)
        switch_music_button.on_click = self.switch_music
        self.box_layout.add(switch_music_button)

        volume_text = UILabel(text='volume: ', width=100, height=20, font_size=14,
                               font_name='Karmatic Arcade')
        self.volume_layout.add(volume_text)

        volume_slider = UISlider(width=200, height=20, min_value=0, max_value=1.0, value=self.media_player.volume,
                                 step=0.1)
        volume_slider.on_change = self.set_volume
        self.volume_layout.add(volume_slider)

        self.box_layout.add(self.volume_layout)

        select_track_text = UILabel(text='select track: ', width=300, height=20, font_size=14,
                              font_name='Karmatic Arcade')
        self.select_track_layout.add(select_track_text)

        first_track_button = UIFlatButton(text='Abnormal Circumstances', width=300, height=50, style=button_style)
        first_track_button.on_click = self.set_first_track
        self.select_track_layout.add(first_track_button)

        second_track_button = UIFlatButton(text='Chase Scene', width=300, height=50, style=button_style)
        second_track_button.on_click = self.set_second_track
        self.select_track_layout.add(second_track_button)

        third_track_button = UIFlatButton(text='Steer Clear', width=300, height=50, style=button_style)
        third_track_button.on_click = self.set_third_track
        self.select_track_layout.add(third_track_button)

        self.box_layout.add(self.select_track_layout)

        to_menu_button = UIFlatButton(text='Back to main menu', width=300, height=50, style=button_style)
        to_menu_button.on_click = self.to_main_menu
        self.box_layout.add(to_menu_button)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def switch_music(self, event):
        if self.media_player.player:
            self.media_player.stop()
            write_settings('False', self.media_player.volume)
        else:
            self.media_player.run()
            write_settings('True', self.media_player.volume)

    def set_volume(self, value):
        self.media_player.change_volume(float(value.new_value))
        if self.media_player.player:
            write_settings('True', self.media_player.volume)
        else:
            write_settings('False', self.media_player.volume)

    def set_first_track(self, event):
        self.media_player.change_track(track='music/Abnormal Circumstances.mp3')

    def set_second_track(self, event):
        self.media_player.change_track(track='music/Chase Scene.mp3')

    def set_third_track(self, event):
        self.media_player.change_track(track='music/Steer Clear.mp3')

    def to_main_menu(self, event):
        self.window.show_view(MainView(media_player=self.media_player))

class MediaPlayer:
    def __init__(self, track='', volume=1.0, file=None):
        self.track = track
        self.track_list = []

        self.player: arcade.Sound | None = None

        self.track_list.append(arcade.load_sound('music/Abnormal Circumstances.mp3'))
        self.track_list.append(arcade.load_sound('music/Chase Scene.mp3'))
        self.track_list.append(arcade.load_sound('music/Steer Clear.mp3'))

        if file:
            with open(file, 'r', encoding='utf-8') as _file:
                settings = _file.readlines()
                self.volume = float(settings[-1].split()[-1].strip())
                if settings[0].split()[-1].strip() == 'True':
                    self.run()
        else:
            self.volume = volume

    def run(self):
        if self.track:
            self.player = arcade.play_sound(arcade.load_sound(self.track), volume=self.volume)
            self.track = ''
        else:
            self.player = arcade.play_sound(sample(self.track_list, 1)[0])
        self.player.push_handlers(on_eos=self.run)

    def change_volume(self, volume):
        try:
            self.player.volume = volume
            self.volume = volume
        except AttributeError:
            pass

    def stop(self):
        try:
            arcade.stop_sound(self.player)
            self.player = None
        except TypeError:
            pass

    def change_track(self, track=''):
        self.stop()
        self.track = track
        self.run()

def write_score(score, name):
    with open('score_table.txt', 'r', encoding='utf-8') as file:
        score_list = file.readlines()
    score_list.append(f'{name} - {score}\n')
    score_list.sort(reverse=True, key=lambda x: int(x.split()[-1]))
    with open('score_table.txt', 'w', encoding='utf-8') as file:
        file.writelines(score_list)

def write_settings(is_playng, volume):
    with open('settings.txt', 'w', encoding='utf-8') as file:
        file.writelines([f'playing {is_playng}\n', f'volume {volume}'])

def teleport_sprites(*args):
    for sprite in args:
        sprite.center_y += SCALE * TILE_WIDTH * 144

def main():
    arcade.load_font('font.ttf')

    media_player = MediaPlayer(file='settings.txt')

    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.show_view(MainView(media_player=media_player))

    arcade.run()

if __name__ == "__main__":
    main()