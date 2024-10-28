import pygame
import skimage
import math
import gc
from agents import reproduce, populate

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("First Game")
clock = pygame.time.Clock()

SCALE = 5

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

FPS = 1000000


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
        self.turn = 150

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
        self.restarting = False

        self.walls = walls
        self.killing_walls = killing_walls
        self.platforms = platforms
        self.original_fitness_walls = fitness_walls
        self.fitness_walls = fitness_walls.copy()
        self.fitness_score = 0

    # def handle_command(self, agent):
    #     if self.on_ground:
    #         step = agent.get_step()
    #         print(f"Step: {step}")
    #         if step is None:
    #             self.restarting = True
    #             return
    #         self.direction = step[0]
    #         self.jump_power = step[1]
    #         self.jumping = True

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
            self.turn -= 1
            if self.on_ground:
                self.y_speed = -self.jump_power
                self.x_speed = self.direction * X_SPEED
                self.on_ground = False

        if self.x_delay_counter < self.x_delay:
            self.x_delay_counter += 1
        else:
            self.rectangle.x += self.x_speed
            self.collide(self.x_speed, 0)
            if self.restarting:
                return
            self.x_delay_counter = 0

        for _ in range(int(abs(col_round(self.y_speed)))):
            if self.restarting:
                return
            if self.on_ground:
                break
            y_change = 1 if self.y_speed > 0 else -1
            self.rectangle.y += y_change
            self.collide(0, y_change)

    def restart(self):
        self.rectangle.topleft = self.starting_pos
        self.x_speed = 0
        self.y_speed = 0
        self.jump_power = 1
        self.direction = 0
        self.jumping = False
        self.on_ground = False
        self.restarting = False
        self.fitness_score = 0
        self.fitness_walls = self.original_fitness_walls.copy()
        self.turn = 150

    def collide(self, x_vel, y_vel):
        for wall in self.killing_walls:
            if self.rectangle.colliderect(wall):
                self.restarting = True
                return
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
                self.fitness_score += self.turn
                self.fitness_walls.remove(wall)
                break

    def update(self):
        # print(f"onground: {self.on_ground}, ")
        # print(f"Position: {self.rectangle.topleft}")
        # print(f"Speed: {self.x_speed, self.y_speed}")
        # print(f"Jump power: {self.jump_power}")
        # print(f"Direction: {self.direction}")
        # print(f"Fitness score: {self.fitness_score}")
        # self.handle_command(agent)
        self.apply_gravity()
        self.move()
        return self.on_ground


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


def save_fitness(fitness_tab, best_fitness_tab):
    with open("fitness.txt", "w") as f:
        for i, fitness in enumerate(fitness_tab):
            f.write(f"{i},{fitness},{best_fitness_tab[i]}\n")


def load_fitness(filename):
    avg_fitness = []
    best_fitness = []
    iteration = 0
    with open(filename, "r") as f:
        for line in f:
            line = line.strip().split(",")
            avg_fitness.append(float(line[1]))
            best_fitness.append(int(line[2]))
            iteration += 1
    return avg_fitness, best_fitness, iteration


run = True


def main():
    agents_filename = "agents_best.txt"
    fitness_filename = "fitness.txt"
    agents = populate(agents_filename)
    player = extract_map("map.png")

    global run
    next_move = True
    iteration = 1
    drawing = False
    fitness_tab = []
    best_fitness_tab = []

    if fitness_filename:
        fitness_tab, best_fitness_tab, iteration = load_fitness(fitness_filename)

    best_fitness = 0
    best_final_step = 0

    while run:
        print(f"Iteration: {iteration}, Best fitness: {best_fitness}")
        is_done = False
        this_run_fitness = 0

        for agent in agents:
            while not is_done:
                clock.tick(FPS)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            drawing = not drawing

                next_move = player.update()

                if player.restarting:
                    agent.fitness = player.fitness_score
                    agent.final_step = agent.current_step
                    if player.fitness_score > best_fitness:
                        best_fitness = player.fitness_score
                        best_final_step = agent.final_step
                    this_run_fitness += player.fitness_score
                    # print(f"Fitness: {player.fitness_score}")
                    player.restart()
                    is_done = True

                if next_move:
                    step = agent.get_step()
                    if step is None:
                        is_done = True
                        break
                    player.direction = step[0]
                    player.jump_power = step[1]
                    player.jumping = True
                if drawing:
                    draw_window(player)
            is_done = False
        gc.collect()

        print(f"This run avg fitness: {this_run_fitness / len(agents)}")
        fitness_tab.append(this_run_fitness / len(agents))
        best_fitness_tab.append(best_fitness)
        save_fitness(fitness_tab, best_fitness_tab)
        agents = reproduce(agents, best_final_step, iteration)
        iteration += 1

    pygame.quit()


if __name__ == "__main__":
    main()
