import pygame
import skimage
import math
import time
from collections import deque # Import deque from collections module

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("First Game")
clock = pygame.time.Clock()

SCALE = 5

# Key mappings
DIRECTION_KEYS = { pygame.K_q: -1, pygame.K_w: 0, pygame.K_e: 1,}

JUMP_POWER_KEYS = {pygame.K_1: 0.65, pygame.K_2: 0.85, pygame.K_3: 1.05, pygame.K_4: 1.25, pygame.K_5: 1.45, pygame.K_6: 1.65, pygame.K_7: 1.85, pygame.K_8: 2.05, pygame.K_9: 2.25, pygame.K_0: 2.45,}

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

FPS = 1000000
SCORE = -1
KILLED = False
POSITION = (0, 0)

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
    def __init__(self, starting_pos, walls, fitness_walls, killing_walls, platforms, moves=None):
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

        # New attributes for predefined moves
        self.moves = moves if moves is not None else []  # List of (direction, jump_power)
        self.move_index = 0  # Tracks the current move index

    def handle_key_presses(self):
        # Only jump if on the ground and moves remain
        if self.on_ground and self.move_index < len(self.moves):
            # Get the current move (direction, jump_power)
            move = self.moves[self.move_index]
            # print(f"Move: {move}")
            if move == 'restart':
                self.restarting = True
                return self.fitness_score
            
            self.direction = move[0]
            self.jump_power = move[1]
            self.jumping = True  # Start the jump
            self.move_index += 1  # Move to the next move for the next frame
        else:
            self.jumping = False  # No moves left or not on ground, stop jumping


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
        global SCORE, KILLED, POSITION
        # print("End of moves")
        # print(f"Score: {self.fitness_score}")
        if KILLED:
            SCORE = 0
        else:
            SCORE = self.fitness_score
            POSITION = self.rectangle.topleft
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
        self.move_index = 0  # Reset to start of moves

    def collide(self, x_vel, y_vel):
        global KILLED
        for wall in self.killing_walls:
            if self.rectangle.colliderect(wall):
                KILLED = True
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

POSSIBLE_MOVES = [
    (-1, 0.65), (0, 0.65), (1, 0.65),
    (-1, 0.85), (0, 0.85), (1, 0.85),
    (-1, 1.05), (0, 1.05), (1, 1.05),
    (-1, 1.25), (0, 1.25), (1, 1.25),
    (-1, 1.45), (0, 1.45), (1, 1.45),
    (-1, 1.65), (0, 1.65), (1, 1.65),
    (-1, 1.85), (0, 1.85), (1, 1.85),
    (-1, 2.05), (0, 2.05), (1, 2.05),
    (-1, 2.25), (0, 2.25), (1, 2.25),
    (-1, 2.45), (0, 2.45), (1, 2.45),
]

# Define run_moves to run the provided moves and set SCORE after restart
def run_moves(player, moves):
    global SCORE, KILLED, POSITION
    KILLED = False
    while True:
        clock.tick(FPS)
        player.moves = moves
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        player.update()
        if player.restarting:
            SCORE = player.fitness_score  # Set the global SCORE on restart
            player.restart()
            break
    # print(f'path: {player.moves}, score: {SCORE}') 
    return (player.moves, SCORE, POSITION)

def remove_suboptimal_paths(valid_paths):
    # find the path with the highest score, remove all paths with lower scores
    scores = [path[1] for path in valid_paths]
    max_score = max(scores)
    print(f'max_score: {max_score}')

    #save all the paths (valid_paths[i][0]) with the highest score in a new list
    best_paths = [valid_paths[i][0] for i in range(len(valid_paths)) if valid_paths[i][1] == max_score]
    print(f'best_paths: {best_paths}')
    new_queue = deque()
    new_valid_paths = []
    for path in best_paths:
        current_path = path[:-1]
        # print(f'current_path: {current_path}')
        for move in POSSIBLE_MOVES:
            new_path = current_path + [move] + ['restart']
            new_queue.append(new_path)
    return new_queue

# BFS to explore move lists and find optimal path
def bfs_optimal_path(player):
    global SCORE
    queue = deque()
    best_score = -1
    best_path = []
    valid_paths = []
    idx = 0
    
    # Start BFS with initial empty path
    initial_path = []
    queue.append(initial_path)

    while queue:
        # Get the next path from the queue
        current_path = queue.popleft()
        path_length = len(current_path)

        # Append 'restart' to simulate running the moves
        moves_to_run = current_path + ['restart']

        # Run the moves and get the score
        result = run_moves(player, moves_to_run)
        if not result:
            break  # Exit if the window is closed

        # Calculate minimum score threshold based on path length
        threshold_score = get_threshold_score(path_length)
        if SCORE >= threshold_score:
            # Only keep paths that meet the threshold score
            if SCORE > best_score:
                best_score = SCORE
                best_path = current_path

            # # if the current path is longer than the last valid path, call the remove_suboptimal_paths function
            # if len(valid_paths) > 1 and len(current_path) + 1 > len(valid_paths[-1][0]):
            #     print(f'lenght changed, current path: {current_path}, last path saved: {valid_paths[-1][0]}')
            #     queue = remove_suboptimal_paths(valid_paths)
            #     print(f'queue len after removing suboptimal paths: {len(queue)}, last element: {queue[-1]}')
            #     valid_paths = []
            # else:
            #     #that five lines below

            valid_paths.append(result)
            # Generate new paths by appending each possible move
            for move in POSSIBLE_MOVES:
                new_path = current_path + [move]
                queue.append(new_path)
        else:
            # print(f"Pruning path with length {path_length} and score {SCORE} (threshold {threshold_score})")
            pass

        idx += 1
        if idx % 1000 == 0:
            print(f"Processed {idx} paths, {len(valid_paths)} valid, {len(queue)} remaining")
            print(f'last checked path: {current_path}, score: {SCORE}')
            print(f'\n valid_paths len: {len(valid_paths)}, \n last valid path: {valid_paths[-1][0]}\n, Best Path: {best_path}, Best Score: {best_score}')


    print(f"Best Path: {best_path}")
    print(f"Best Score: {best_score}")
    return best_path

def get_threshold_score(path_length):
    # Threshold score is the minimum score needed to reach the goal
     # 150 * path_length - 1 - 2 - 3 - ... - path_length
    return 150 * path_length - sum(range(1, path_length + 1))
# Initialize and run the game
def main():
    player = extract_map("map.png")  

    # Run BFS to find the optimal path
    best_path = bfs_optimal_path(player)

    # Assign best path to player and display final run
    player.moves = best_path + ['restart']  # Add restart at the end to complete the path
    run_moves(player, player.moves)

    pygame.quit()


if __name__ == "__main__":
    main()