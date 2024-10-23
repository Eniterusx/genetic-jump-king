import pygame
import cv2

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
WIN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("First Game")

SCALE = 5

# Define key mappings
DIRECTION_KEYS = {
    pygame.K_q: "Left",
    pygame.K_w: "Up",
    pygame.K_e: "Right",
}

JUMP_POWER_KEYS = {
    pygame.K_1: 1,
    pygame.K_2: 2,
    pygame.K_3: 3,
    pygame.K_4: 4,
    pygame.K_5: 5,
    pygame.K_6: 6,
    pygame.K_7: 7,
    pygame.K_8: 8,
    pygame.K_9: 9,
    pygame.K_0: 10,
}

JUMP_KEY = pygame.K_SPACE

# player params
PLAYER_SIZE = (2, 3)
X_SPEED = 2
MAX_FALL_SPEED = 10
GRAVITY = 0.5

# Colors
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

FPS = 60


class Player:
    def __init__(self, starting_pos, walls):
        self.height = PLAYER_SIZE[1]
        self.width = PLAYER_SIZE[0]
        self.rectangle = pygame.Rect(
            starting_pos[0], starting_pos[1], self.width, self.height
        )

        self.x_speed = 0
        self.y_speed = 0

        self.jump_power = 0
        self.direction = "Up"
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
        if self.jumping:
            self.jumping = False
            if self.on_ground:
                self.y_speed = -self.jump_power

        self.rectangle.x += self.x_speed
        self.collide(self.x_speed, 0)

        self.rectangle.y += self.y_speed
        self.collide(0, self.y_speed)

    def collide(self, x_vel, y_vel):
        for wall in self.walls:
            if self.rectangle.colliderect(wall):
                if x_vel > 0:  # Moving right, bounce left
                    self.rectangle.right = wall.left
                    self.x_speed = -self.x_speed / 2
                if x_vel < 0:  # Moving left, bounce right
                    self.rectangle.left = wall.right
                    self.x_speed = -self.x_speed / 2
                if y_vel > 0:  # Moving down, stop the movement, set the onground
                    self.rectangle.bottom = wall.top
                    self.y_speed = 0
                    self.on_ground = True
                if y_vel < 0:  # Moving up, hit the ceiling
                    self.rectangle.top = wall.bottom
                    self.y_speed = 0

    def update(self):
        self.handle_key_presses()
        self.apply_gravity()
        self.move()


def extract_map(image_path):
    walls = []
    image = cv2.imread(image_path)
    for y in range(len(image)):
        for x in range(len(image[y])):
            pixel = image[y][x]
            if all(pixel == BLACK):
                # cv2 uses y,x but pygame uses x,y
                walls.append((x, y))
            elif all(pixel == GREEN):
                player_spawn = [x, y]
    return walls, player_spawn


def draw_map(walls):
    print(walls[0])
    for wall in walls:
        pygame.draw.rect(
            WIN,
            BLACK,
            (wall[0] * SCALE, wall[1] * SCALE, SCALE, SCALE),
        )


def draw_player(player_loc):
    pygame.draw.rect(
        WIN,
        GREEN,
        (
            player_loc[0] * SCALE,
            player_loc[1] * SCALE,
            SCALE * PLAYER_SIZE[0],
            SCALE * PLAYER_SIZE[1],
        ),
    )


def draw_window(walls, player_location):
    WIN.fill(GRAY)
    draw_map(walls)
    draw_player(player_location)
    pygame.display.update()


def main():
    walls, player_location = extract_map("map.png")
    run = True
    clock = pygame.time.Clock()
    player = Player(player_location, walls)
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            player.update()

        draw_window(walls, player_location)
    pygame.quit()


if __name__ == "__main__":
    main()
