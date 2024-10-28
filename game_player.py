import pygame
import skimage
import math

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("First Game")
clock = pygame.time.Clock()

SCALE = 5

# Key mappings
DIRECTION_KEYS = {
    pygame.K_q: -1,
    pygame.K_w: 0,
    pygame.K_e: 1,
}

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

# Player params
PLAYER_SIZE = (2, 3)
X_SPEED = 2
MAX_FALL_SPEED = 6
GRAVITY = 0.125

# Colors
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
TEAL = (0, 255, 255)
RED = (255, 0, 0)
BROWN = (139, 69, 19)

FPS = 60


def col_round(x):
    frac = x - math.floor(x)
    if frac < 0.5:
        return math.floor(x)
    return math.ceil(x)


class FitnessRectangle(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((SCALE, SCALE))
        self.image.fill(TEAL)
        self.rectangle = pygame.Rect(0, 0, 0, 0)
        self.rectangle.topleft = (0, 0)

        self.points = []

    def add_point(self, point):
        self.points.append(point)

    def create_rectangle(self):
        if len(self.points) == 0:
            return
        min_x = min(self.points, key=lambda x: x[0])[0]
        max_x = max(self.points, key=lambda x: x[0])[0]
        min_y = min(self.points, key=lambda x: x[1])[1]
        max_y = max(self.points, key=lambda x: x[1])[1]
        self.rectangle = pygame.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        self.rectangle.topleft = (min_x, min_y)

    def update(self):
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self, starting_pos, walls, fitness_walls, killing_walls, platforms):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE[0], PLAYER_SIZE[1]))
        self.image.fill(GREEN)

        # TEMP:
        self.starting_pos = starting_pos

        self.rectangle = self.image.get_rect()
        self.rectangle.topleft = (starting_pos[0], starting_pos[1])

        self.x_speed = 0
        self.x_delay = 2
        self.x_delay_counter = 0
        self.y_speed = 0

        self.jump_power = 1
        self.direction = 0
        self.jumping = False

        self.on_ground = False

        self.walls = walls
        self.killing_walls = killing_walls
        self.platforms = platforms
        self.fitness_walls = fitness_walls
        self.fitness_score = 0

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
            self.x_delay_counter = 0
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

        for _ in range(int(abs(col_round(self.y_speed)))):
            if self.on_ground:
                break
            y_change = 1 if self.y_speed > 0 else -1
            self.rectangle.y += y_change
            self.collide(0, y_change)

    def collide(self, x_vel, y_vel):
        for wall in self.killing_walls:
            if self.rectangle.colliderect(wall):
                print("KILLED!")
                print(f"Score: {self.fitness_score}")
                self.rectangle.topleft = self.starting_pos
                self.x_speed = 0
                self.y_speed = 0
                # global run
                # run = False
                break
        for wall in self.walls:
            if self.rectangle.colliderect(wall):
                if x_vel > 0:  # Moving right, bounce left
                    self.rectangle.right = wall.left
                    self.x_speed = -X_SPEED
                if x_vel < 0:  # Moving left, bounce right
                    self.rectangle.left = wall.right
                    self.x_speed = X_SPEED
                if y_vel > 0:  # Moving down, stop the movement, set the onground
                    self.rectangle.bottom = wall.top
                    self.y_speed = 0
                    self.on_ground = True
                    self.x_delay_counter = 0
                if y_vel < 0:  # Moving up, hit the ceiling
                    self.rectangle.top = wall.bottom
                    self.y_speed = 0
        for wall in self.platforms:
            if self.rectangle.colliderect(wall):
                # On top of platform
                if y_vel > 0 and self.rectangle.bottom <= (wall.top + 1):
                    self.rectangle.bottom = wall.top
                    self.y_speed = 0
                    self.on_ground = True
                    self.x_delay_counter = 0
        for wall in self.fitness_walls:
            if self.rectangle.colliderect(wall.rectangle):
                self.fitness_score += 1
                self.fitness_walls.remove(wall)
                break

    def update(self):
        # print(f"onground: {self.on_ground}, ")
        # print(f"Position: {self.rectangle.topleft}")
        # print(f"Speed: {self.x_speed, self.y_speed}")
        # print(f"Jump power: {self.jump_power}")
        # print(f"Direction: {self.direction}")
        # print(f"Fitness score: {self.fitness_score}")
        self.handle_key_presses()
        self.apply_gravity()
        self.move()


def check_neighbours(pixel_cords, neighbour_list):
    for neighbour in neighbour_list:
        if pixel_cords[0] == neighbour[0] and pixel_cords[1] == (neighbour[1] + 1):
            return True
        if pixel_cords[0] == neighbour[0] and pixel_cords[1] == (neighbour[1] - 1):
            return True
        if pixel_cords[0] == (neighbour[0] + 1) and pixel_cords[1] == neighbour[1]:
            return True
        if pixel_cords[0] == (neighbour[0] - 1) and pixel_cords[1] == neighbour[1]:
            return True
    return False


def extract_map(image_path):
    wall_rects = []
    kill_rects = []
    fitness_rects = []
    platform_rects = []
    player_spawn = None
    image = skimage.io.imread(image_path)
    for y in range(len(image)):
        for x in range(len(image[y])):
            pixel = image[y][x][:3]
            # Parse walls
            if all(pixel == BLACK):
                # skimage uses y,x but pygame uses x,y
                rect = pygame.Rect(x, y, 1, 1)
                wall_rects.append(rect)
            # Parse killbricks
            elif all(pixel == RED):
                rect = pygame.Rect(x, y, 1, 1)
                kill_rects.append(rect)
            # Parse player
            elif all(pixel == GREEN) and player_spawn is None:
                player_spawn = [x, y]
            # Parse platforms
            elif all(pixel == BROWN):
                rect = pygame.Rect(x, y, 1, 1)
                platform_rects.append(rect)
            # Parse fitness points
            elif all(pixel == TEAL):
                found = False
                for rectangle in fitness_rects:
                    if check_neighbours((x, y), rectangle.points):
                        rectangle.add_point((x, y))
                        found = True
                        break
                if not found:
                    new_rect = FitnessRectangle()
                    new_rect.add_point((x, y))
                    fitness_rects.append(new_rect)
    for rectangle in fitness_rects:
        rectangle.create_rectangle()
    if player_spawn is None:
        raise Exception("Player not declared in the map")
    player = Player(player_spawn, wall_rects, fitness_rects, kill_rects, platform_rects)
    return player


def draw_walls(walls, color):
    for wall in walls:
        if wall.width == 1 and wall.height == 1:
            pygame.draw.rect(
                screen,
                color,
                (wall[0] * SCALE, wall[1] * SCALE, SCALE, SCALE),
            )
        else:
            pygame.draw.rect(
                screen,
                color,
                (wall[0] * SCALE, wall[1] * SCALE, wall[2] * SCALE, wall[3] * SCALE),
            )


def draw_player(player):
    scaled_rect = pygame.Rect(
        player.rectangle.x * SCALE,
        player.rectangle.y * SCALE,
        player.rectangle.width * SCALE,
        player.rectangle.height * SCALE,
    )
    screen.blit(
        pygame.transform.scale(player.image, (scaled_rect.width, scaled_rect.height)),
        scaled_rect,
    )


def draw_window(player):
    screen.fill(GRAY)
    draw_walls(player.walls, BLACK)
    draw_walls(player.killing_walls, RED)
    draw_walls([rectangle.rectangle for rectangle in player.fitness_walls], TEAL)
    draw_walls(player.platforms, BROWN)
    draw_player(player)
    pygame.display.update()


run = True


def main():
    player = extract_map("map.png")
    global run

    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        player.update()

        draw_window(player)
    pygame.quit()


if __name__ == "__main__":
    main()
