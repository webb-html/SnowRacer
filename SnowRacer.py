import arcade

SCALE = 1.5

TILE_WIDTH = 16

SCREEN_WIDTH = 16 * TILE_WIDTH * SCALE
SCREEN_HEIGHT = 20 * TILE_WIDTH * SCALE
SCREEN_TITLE = 'Snow Racer'

RACER_SPEED = 100

CAMERA_LERP = 1
CAMERA_DEAD_ZONE_W = int(SCREEN_WIDTH * 0.25)

class Racer(arcade.Sprite):
    def __init__(self,position_x, position_y):
        super().__init__()
        self.scale = SCALE
        self.speed_x = RACER_SPEED
        self.speed_y = 200

        self.slow_texture = arcade.load_texture("images/character/character_slow.png")
        self.texture = self.slow_texture

        self.center_x = position_x
        self.center_y = position_y

    def update(self, boost, delta_time, keys_pressed, **kwargs):
        if kwargs:
            if type(kwargs['speed']) == type(0):
                self.speed_x = kwargs['speed']
            elif kwargs['speed'][0] == '/':
                self.speed_x /= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '-':
                self.speed_x -= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '*':
                self.speed_x *= float(kwargs['speed'][1:])
            elif kwargs['speed'][0] == '+':
                self.speed_x += float(kwargs['speed'][1:])
        if self.speed_x < 0:
            self.speed_x = 0
        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed_y * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed_y * delta_time
        if arcade.key.UP in keys_pressed or arcade.key.W in keys_pressed:
            pass
        dy -= self.speed_x * delta_time

        self.center_x += dx
        self.center_y += dy
        if self.center_y < SCALE * TILE_WIDTH * 15:
            teleport_sprites(self)
        self.speed_x += boost

class SnowRacerGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, antialiasing=True)

        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()

        self.tile_map = None

        self.racer_list = arcade.SpriteList()

        self.racer: arcade.Sprite | None = None

    def setup(self):

        self.tile_map = arcade.load_tilemap('trace.tmx', scaling=SCALE)
        self.floar_list = self.tile_map.sprite_lists['floar']
        self.shadow_list = self.tile_map.sprite_lists['shadows']
        self.nature_list = self.tile_map.sprite_lists['nature']
        self.tramplins = self.tile_map.sprite_lists['tramplins']
        self.nets = self.tile_map.sprite_lists['nets']
        self.barriers = self.tile_map.sprite_lists['barriers']
        self.collision_list = self.tile_map.sprite_lists["collision"]

        self.world_width = int(self.tile_map.width * self.tile_map.tile_width * SCALE)
        self.world_height = int(self.tile_map.height * self.tile_map.tile_height * SCALE)

        self.racer = Racer(SCALE * TILE_WIDTH * 24, SCALE * TILE_WIDTH * 159)
        self.racer_list.append(self.racer)

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

        collision_with_barriers = arcade.check_for_collision_with_list(self.racer, self.barriers)
        collision_with_nets = arcade.check_for_collision_with_list(self.racer, self.nets)
        collision_with_tramplins = arcade.check_for_collision_with_list(self.racer, self.tramplins)
        if collision_with_tramplins:
            self.racer_list.update(boost, delta_time, self.keys_pressed, speed=f'+{boost * 5}')
        elif collision_with_nets:
            self.racer_list.update(boost, delta_time, self.keys_pressed, speed=f'-{boost * 5}')
        elif collision_with_barriers:
            self.racer_list.update(0, delta_time, self.keys_pressed, speed=f'/1.5')
        else:
            self.racer_list.update(boost, delta_time, self.keys_pressed)

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
        self.racer_list.draw()
        self.nature_list.draw()
        self.barriers.draw()

        #self.collision_list.draw()

        self.gui_camera.use()

def teleport_sprites(*args):
    for sprite in args:
        sprite.center_y += SCALE * TILE_WIDTH * 144

def main():
    game = SnowRacerGame()
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()