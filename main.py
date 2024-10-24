import pygame
import cv2
import math

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("First Game")
clock = pygame.time.Clock()

SCALE = 5

# Define key mappings
DIRECTION_KEYS = {
    pygame.K_q: -1,
    pygame.K_w: 0,
    pygame.K_e: 1,
}

# JUMP_POWER_KEYS = {
#     pygame.K_1: 0.7,
#     pygame.K_2: 1.4,
#     pygame.K_3: 2.1,
#     pygame.K_4: 2.8,
#     pygame.K_5: 3.5,
#     pygame.K_6: 4.2,
#     pygame.K_7: 4.9,
#     pygame.K_8: 5.6,
#     pygame.K_9: 6.3,
#     pygame.K_0: 7,
# }

JUMP_POWER_KEYS = {
    pygame.K_1: 0.65,
    pygame.K_2: 0.85,
    pygame.K_3: 1.05,
    pygame.K_4: 1.25,
    pygame.K_5: 1.45,
    pygame.K_6: 1.65,
    pygame.K_7: 1.85,
    pygame.K_8: 2.05,
    pygame.K_9: 2.25,
    pygame.K_0: 2.45,
}

JUMP_KEY = pygame.K_SPACE

# player params
PLAYER_SIZE = (2, 3)
X_SPEED = 2
MAX_FALL_SPEED = 6
GRAVITY = 0.125

# Colors
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

FPS = 60


# def get_decimal(num):
#     _, decimal_part = math.modf(num)
#     if decimal_part
def col_round(x):
    frac = x - math.floor(x)
    if frac < 0.5:
        return math.floor(x)
    return math.ceil(x)


class Player(pygame.sprite.Sprite):
    def __init__(self, starting_pos, walls):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE[0], PLAYER_SIZE[1]))
        self.image.fill(GREEN)
        self.rectangle = self.image.get_rect()
        self.rectangle.topleft = (starting_pos[0], starting_pos[1])

        self.x_speed = 0
        self.x_delay = 2
        self.x_delay_counter = 0
        self.y_speed = 0

        self.jump_power = 1
        self.direction = 0
        self.jumping = False

        # TODO: check if standing on ground
        self.on_ground = False

        self.walls = walls

    def handle_key_presses(self):
        keys = pygame.key.get_pressed()
        for key, direction in DIRECTION_KEYS.items():
            if keys[key]:
                self.direction = direction
                break

        for key, power in JUMP_POWER_KEYS.items():
            if keys[key]:
                self.jump_power = power
                break

        self.jumping = keys[JUMP_KEY]

    def apply_gravity(self):
        if self.on_ground:
            return
        # positive y speed means falling
        if self.y_speed < MAX_FALL_SPEED:
            self.y_speed += GRAVITY

    def move(self):
        if self.on_ground:
            self.x_speed = 0
        if self.jumping:
            self.jumping = False
            if self.on_ground:
                self.y_speed = -self.jump_power
                self.x_speed = self.direction * X_SPEED
                self.on_ground = False

        if self.x_delay_counter < self.x_delay:
            self.x_delay_counter += 1
        else:
            self.rectangle.x += self.x_speed
            self.collide(self.x_speed, 0)
            self.x_delay_counter = 0

        # temp_y = self.rectangle.y
        # self.rectangle.y += self.y_speed
        # print(f"speed: {self.y_speed}, change: {self.rectangle.y - temp_y}")
        # self.collide(0, self.y_speed)
        for _ in range(int(abs(col_round(self.y_speed)))):
            if self.on_ground:
                break
            print(int(col_round(self.y_speed)))
            y_change = 1 if self.y_speed > 0 else -1
            self.rectangle.y += y_change
            self.collide(0, y_change)

    def collide(self, x_vel, y_vel):
        for wall in self.walls:
            if self.rectangle.colliderect(wall):
                if x_vel > 0:  # Moving right, bounce left
                    self.rectangle.right = wall.left
                    self.x_speed = -self.x_speed / 1.2
                if x_vel < 0:  # Moving left, bounce right
                    self.rectangle.left = wall.right
                    self.x_speed = -self.x_speed / 1.2
                if y_vel > 0:  # Moving down, stop the movement, set the onground
                    self.rectangle.bottom = wall.top
                    self.y_speed = 0
                    self.on_ground = True
                    self.x_delay_counter = 0
                if y_vel < 0:  # Moving up, hit the ceiling
                    self.rectangle.top = wall.bottom
                    self.y_speed = 0

    def update(self):
        # print(f"onground: {self.on_ground}, ")
        # print(f"Position: {self.rectangle.topleft}")
        # print(f"Speed: {self.x_speed, self.y_speed}")
        print(f"Jump power: {self.jump_power}")
        # print(f"Direction: {self.direction}")
        self.handle_key_presses()
        self.apply_gravity()
        self.move()


def extract_map(image_path):
    wall_rects = []
    player_spawn = None
    image = cv2.imread(image_path)
    for y in range(len(image)):
        for x in range(len(image[y])):
            pixel = image[y][x]
            # Parse walls
            if all(pixel == BLACK):
                # cv2 uses y,x but pygame uses x,y
                rect = pygame.Rect(x, y, 1, 1)
                wall_rects.append(rect)
            # Parse player
            elif all(pixel == GREEN) and player_spawn is None:
                player_spawn = [x, y]
    if player_spawn is None:
        raise Exception("Player not declared in the map")
    return wall_rects, player_spawn


def draw_walls(walls):
    for wall in walls:
        pygame.draw.rect(
            screen,
            BLACK,
            (wall[0] * SCALE, wall[1] * SCALE, SCALE, SCALE),
        )


def draw_player(player_group):
    for entity in player_group:
        scaled_rect = pygame.Rect(
            entity.rectangle.x * SCALE,
            entity.rectangle.y * SCALE,
            entity.rectangle.width * SCALE,
            entity.rectangle.height * SCALE,
        )
        screen.blit(
            pygame.transform.scale(
                entity.image, (scaled_rect.width, scaled_rect.height)
            ),
            scaled_rect,
        )


def draw_window(walls, player_group):
    screen.fill(GRAY)
    draw_walls(walls)
    draw_player(player_group)
    pygame.display.update()


def main():
    walls, player_location = extract_map("map.png")
    run = True
    player = Player(player_location, walls)
    player_group = pygame.sprite.Group()
    player_group.add(player)

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        player_group.update()

        draw_window(walls, player_group)
    pygame.quit()


if __name__ == "__main__":
    main()
