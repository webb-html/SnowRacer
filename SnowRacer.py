import arcade

SCALE = 2.0
TILE_WIDTH = 16
SCREEN_WIDTH = 16 * TILE_WIDTH * SCALE
SCREEN_HEIGHT = 20 * TILE_WIDTH * SCALE
SCREEN_TITLE = 'Snow Racer'
RACER_SPEED = 100

class Racer(arcade.Sprite):
    def __init__(self,position_x, position_y):
        super().__init__()
        self.scale = SCALE
        self.speed = RACER_SPEED

        self.slow_texture = arcade.load_texture("images/character/character_slow.png")
        self.texture = self.slow_texture

        self.center_x = position_x
        self.center_y = position_y

    def update(self, boost, delta_time, keys_pressed):
        dx, dy = 0, 0
        if arcade.key.LEFT in keys_pressed or arcade.key.A in keys_pressed:
            dx -= self.speed * delta_time
        if arcade.key.RIGHT in keys_pressed or arcade.key.D in keys_pressed:
            dx += self.speed * delta_time
        if arcade.key.UP in keys_pressed or arcade.key.W in keys_pressed:
            pass
        dy -= self.speed * delta_time

        self.center_x += dx
        self.center_y += dy
        self.speed += boost
        self.center_x = max(self.width/2, min(SCREEN_WIDTH - self.width/2, self.center_x))
        self.center_y = max(self.height/2, min(SCREEN_HEIGHT - self.height/2, self.center_y))

class SnowRacerGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, antialiasing=True)

    def setup(self):
        self.racer_list = arcade.SpriteList()

        self.racer = Racer(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 2 * TILE_WIDTH * SCALE)
        self.racer_list.append(self.racer)

        self.keys_pressed = set()

    def on_key_press(self, key, modifiers):
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def on_update(self, delta_time):
        boost = 0.25
        self.racer_list.update(boost, delta_time, self.keys_pressed)

    def on_draw(self):
        self.clear()

        self.racer_list.draw()

def main():
    game = SnowRacerGame()
    game.setup()  # Запускаем начальную настройку игры
    arcade.run()


if __name__ == "__main__":
    main()