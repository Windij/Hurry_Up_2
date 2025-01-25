import sys
import pygame
import os
import time
import math

pygame.init()

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 850
BOARD_WIDTH = 9
BOARD_HEIGHT = 9
TILE_SIZE = 60
BROWN = (123, 63, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
LIGHT_YELLOW = (255, 255, 150)
WHITE = (255, 255, 255)
GRID_LINE_COLOR = BLACK
LEVEL_FILE = 'level.txt'
RECORD_FILE = 'record.txt'
TRAJECTORY_FILE = 'trajectory.txt'

pictures = {
    '#': 'стены.png',
    '.': 'простая плитка.png',
    'K': GOLD,
    'k': BLUE,
    'D': GOLD,
    'd': BLUE,
    'W': BLUE,
    'S': YELLOW,
    '*': LIGHT_YELLOW,
    'P': GREEN,
    'O': BLUE,
    'M': BLACK
}


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    return image


class Base(pygame.sprite.Sprite):
    def __init__(self, x, y, color, indicator=0):
        super().__init__()
        self.indicator = indicator
        if type(color) is tuple:
            self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
            self.image.fill(color)
        else:
            self.image = load_image(color)
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

    def move(self, dx, dy):
        self.rect.x += dx * TILE_SIZE
        self.rect.y += dy * TILE_SIZE


class Player(Base):
    def __init__(self, x, y):
        super().__init__(x, y, GREEN)

    def move(self, dx, dy):
        pass

    def is_collide(self, all_tiles):
        return pygame.sprite.spritecollideany(self, all_tiles)


class Door(Base):
    def __init__(self, x, y, color, indicator=0):
        super().__init__(x, y, color, indicator)
        self.is_open = False


class Monster(Base):
    def __init__(self, color, trajectory_file):
        self.trajectory = self.load_trajectory(trajectory_file)
        print(self.trajectory)
        self.current_point_index = 0
        self.next_point_index = 1
        self.speed = 4
        self.x, self.y = self.trajectory[0]
        super().__init__(self.x, self.y, color)

    def load_trajectory(self, filename):
        trajectory = []
        with open(f'data/{filename}', 'r') as file:
            for line in file:
                x, y = map(float, line.strip().split(','))
                trajectory.append([x, y])
        return trajectory

    def calculate_movement(self):
        x1, y1 = self.trajectory[self.current_point_index]
        x2, y2 = self.trajectory[self.next_point_index]

        dx = x2 - x1
        dy = y2 - y1

        distance = math.sqrt(dx ** 2 + dy ** 2)

        if distance == 0:
            return 0, 0

        speed_x = self.speed * dx / distance
        speed_y = self.speed * dy / distance

        return speed_x, speed_y

    def update(self):
        speed_x, speed_y = self.calculate_movement()

        self.x += speed_x
        self.y += speed_y
        self.rect.x = self.x
        self.rect.y = self.y

        current_x, current_y = self.trajectory[self.current_point_index]
        next_x, next_y = self.trajectory[self.next_point_index]

        # Проверка достижения точки
        if speed_x > 0:
            if self.x >= next_x:
                self.x = next_x
        elif speed_x < 0:
            if self.x <= next_x:
                self.x = next_x

        if speed_y > 0:
            if self.y >= next_y:
                self.y = next_y
        elif speed_y < 0:
            if self.y <= next_y:
                self.y = next_y

        if (self.x == next_x and self.y == next_y):
            self.current_point_index = self.next_point_index
            self.next_point_index = (self.next_point_index + 1) % len(self.trajectory)

    def move(self, dx, dy):
        self.x += dx * TILE_SIZE
        self.y += dy * TILE_SIZE
        for pos in self.trajectory:
            pos[0] += dx * TILE_SIZE
            pos[1] += dy * TILE_SIZE
        self.update()


def load_level(filename):
    level_data = []
    try:
        with open(f'data/{filename}', 'r') as file:
            for line in file:
                level_data.append(line.strip())
    except FileNotFoundError:
        print(f"File {filename} not found")
        return []
    return level_data


def create_level(level_data, trajectory):
    wall = pygame.sprite.Group()
    floor = pygame.sprite.Group()
    player = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    chips = pygame.sprite.Group()
    water = pygame.sprite.Group()
    sand = pygame.sprite.Group()
    portal = pygame.sprite.Group()
    monsters = pygame.sprite.Group()
    p1 = None
    for y, row in enumerate(level_data):
        for x, tile_type in enumerate(row):
            if tile_type == '[' or tile_type == '>':
                continue
            if tile_type != 'M':
                tile = Base(x, y, pictures[tile_type])
            if tile_type == '#':
                wall.add(tile)
            elif tile_type == 'P':
                p1 = Player(x, y)
                player.add(p1)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'K':
                tile.indicator = 1
                keys.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'k':
                tile.indicator = 2
                keys.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'D':
                tile.indicator = 1
                doors.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'd':
                tile.indicator = 2
                doors.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == '*':
                chips.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'W':
                water.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'S':
                sand.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'O':
                portal.add(tile)
            elif tile_type == 'M':
                monster = Monster(pictures['M'], trajectory)
                monsters.add(monster)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == '.':
                floor.add(tile)
    return wall, floor, player, p1, keys, doors, chips, water, sand, portal, monsters


class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.board = [[0] * width for _ in range(height)]
        self.left = (SCREEN_WIDTH - width * TILE_SIZE) // 2
        self.top = 0
        self.cell_size = TILE_SIZE
        self.screen_2 = pygame.Surface((self.width * self.cell_size,
                                        self.height * self.cell_size))

    def set_view(self, left, top, cell_size):
        self.left = left
        self.top = top
        self.cell_size = cell_size
        self.screen_2 = pygame.Surface((self.width * self.cell_size, self.height * self.cell_size))

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(screen, GRAY, (
                    x * self.cell_size,
                    y * self.cell_size, self.cell_size,
                    self.cell_size), width=1)
                pygame.draw.rect(screen, BLACK, (
                    x * self.cell_size + 1,
                    y * self.cell_size + 1, self.cell_size - 2,
                    self.cell_size - 2))

    def get_click(self, mouse_pos):
        cell = self.get_cell(mouse_pos)
        self.on_click(cell)

    def get_cell(self, mouse_pos):
        if self.left <= mouse_pos[0] < self.left + self.width * self.cell_size and \
                self.top <= mouse_pos[1] < self.top + self.height * self.cell_size:
            return (int((mouse_pos[1] - self.top) / self.cell_size),
                    int((mouse_pos[0] - self.left) / self.cell_size))
        else:
            return None

    def on_click(self, cell_coords):
        pass

    def load_level(self, filename, trajectory):
        level_data = load_level(filename)
        (self.wall, self.floor, self.player, self.p1, self.keys, self.doors, self.chips, self.water,
         self.sand, self.portal, self.monsters) = create_level(level_data, trajectory)
        delta_x = self.width // 2 * self.cell_size - self.p1.rect.x
        delta_y = self.height // 2 * self.cell_size - self.p1.rect.y
        for tile in self.wall:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.floor:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.keys:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.doors:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.chips:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.water:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.sand:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.portal:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.player:
            tile.rect.x += delta_x
            tile.rect.y += delta_y
        for tile in self.monsters:
            tile.rect.x += delta_x
            tile.rect.y += delta_y

    def move_level(self, dx, dy, inventory, chips_left):
        flag = False
        for tile in self.wall:
            tile.move(dx, dy)
        for tile in self.water:
            tile.move(dx, dy)
        for tile in self.portal:
            tile.move(dx, dy)
        for tile in self.floor:
            tile.move(dx, dy)
        for tile in self.monsters:
            tile.move(dx, dy)
        for tile in self.sand:
            tile.move(dx, dy)
            if self.p1.rect.colliderect(tile.rect):
                tile.move(-dx, -dy)
                if pygame.sprite.spritecollideany(tile, self.wall):
                    tile.move(dx, dy)
                    flag = True
                if pygame.sprite.spritecollideany(tile, self.water):
                    for water in self.water:
                        if tile.rect.colliderect(water.rect):
                            self.water.remove(water)
                            break
                    self.sand.remove(tile)

        for tile in self.keys:
            tile.move(dx, dy)
            if self.p1.rect.colliderect(tile.rect):
                inventory.add_to_inventory(tile)
                self.keys.remove(tile)
        for tile in self.doors:
            tile.move(dx, dy)
            if self.p1.rect.colliderect(tile.rect):
                if any(item.indicator == tile.indicator for item in inventory.items):
                    tile.is_open = True
                    self.doors.remove(tile)
                else:
                    # Блокируем проход, если дверь не открыта
                    flag = True
        for tile in self.chips:
            tile.move(dx, dy)
            if self.p1.rect.colliderect(tile.rect):
                self.chips.remove(tile)
                chips_left -= 1
        if flag or self.p1.is_collide(self.wall):
            self.move_level(-dx, -dy, inventory, chips_left)
        return chips_left

    def move_monsters(self):
        for monster in self.monsters:
            monster.update()

    def draw_level(self, screen):
        self.screen_2.fill((0, 0, 0, 0))
        self.render(self.screen_2)
        self.wall.draw(self.screen_2)
        self.floor.draw(self.screen_2)
        self.player.draw(self.screen_2)
        self.keys.draw(self.screen_2)
        self.doors.draw(self.screen_2)
        self.chips.draw(self.screen_2)
        self.water.draw(self.screen_2)
        self.sand.draw(self.screen_2)
        self.portal.draw(self.screen_2)
        self.monsters.draw(self.screen_2)
        screen.blit(self.screen_2, (self.left, self.top))

    def check_portal_collision(self, chips_left, time_left, screen, inventory):
        if self.p1.is_collide(self.portal) and chips_left == 0:
            total_score = 1000 + time_left * 10
            record = load_record()
            improvement = total_score - record if record != 0 else "——"
            save_record(max(total_score, record))
            inventory.items = []
            PopupWindow(screen, f"Total Score: {total_score}      Record: {record}     Improvement: {improvement}", 600,
                        200).run()
            return True
        return False

    def check_monster_collision(self, monsters):
        for monster in monsters:
            if self.p1.rect.colliderect(monster.rect):
                return True
        return False


def load_record():
    try:
        with open(RECORD_FILE, 'r') as f:
            return int(f.read())
    except FileNotFoundError:
        return 0


def save_record(record):
    with open(RECORD_FILE, 'w') as f:
        f.write(str(record))


class Inventory(Board):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.items = []

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                pygame.draw.rect(screen, 'white', (
                    x * self.cell_size + self.left, y * self.cell_size + self.top,
                    self.cell_size, self.cell_size), width=1)
                pygame.draw.rect(screen, GRAY, (
                    x * self.cell_size + self.left + 1, y * self.cell_size + self.top + 1,
                    self.cell_size - 2, self.cell_size - 2))
        for i, item in enumerate(self.items):
            item.rect.x = self.left + i * self.cell_size
            item.rect.y = self.top
            screen.blit(item.image, item.rect)

    def add_to_inventory(self, item):
        if len(self.items) < self.width:
            self.items.append(item)


class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, action=None, image=None):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.font = pygame.font.Font(None, 36)
        self.text_surface = self.font.render(text, True, BLACK)
        self.text_rect = self.text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.rect = pygame.Rect(x, y, width, height)
        self.image = image

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.image:
            if self.rect.collidepoint(mouse_pos):
                screen.blit(self.image, self.rect)
                pygame.draw.rect(screen, self.hover_color, self.rect, 2)  # add outline to image
            else:
                screen.blit(self.image, self.rect)
        else:
            if self.rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, self.hover_color, self.rect)
            else:
                pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.text_surface, self.text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.action:
                self.action()


class PopupWindow:
    def __init__(self, screen, text, width, height, background_image=None, close_image=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.text = text
        self.font = pygame.font.Font(None, 24)
        self.text_surface = self.font.render(text, True, BLACK)
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - width // 2, SCREEN_HEIGHT // 2 - height // 2, width, height)
        self.running = True
        self.close_button = Button('Закрыть', self.rect.x + self.width - 140, self.rect.y + self.height - 40, 120, 30,
                                   RED, (200, 0, 0), self.close, close_image)
        self.background_image = background_image

    def close(self):
        self.running = False

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.close_button.handle_event(event)
            if self.background_image:
                self.screen.blit(self.background_image, self.rect)
            else:
                pygame.draw.rect(self.screen, GRAY, self.rect)
            self.screen.blit(self.text_surface, self.text_rect)
            self.close_button.draw(self.screen)
            pygame.display.flip()


class StartWindow:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []
        self.running = True
        self.background_image = load_image('dungeon_entrance.png')
        self.table_image = load_image('tables.png')
        self.table_image = pygame.transform.scale(self.table_image, (200, 50))
        self.start_game_table_rect = None
        self.create_buttons()
        self.popup_window = None
        self.animation_start_time = 0
        self.animation_duration = 2
        self.animating = False

    def create_buttons(self):
        button_width = 200
        button_height = 50
        start_x = SCREEN_WIDTH // 2 - button_width // 2
        button_y = 200
        space = 80
        self.buttons.append(
            Button('Начать игру', start_x, button_y, button_width, button_height, GREEN, (0, 200, 0), self.start_game,
                   self.table_image))
        self.start_game_table_rect = self.buttons[0].rect
        button_y += space
        self.buttons.append(
            Button('О игре', start_x, button_y, button_width, button_height, BLUE, (0, 0, 200), self.show_about,
                   self.table_image))
        button_y += space
        self.buttons.append(Button('Об авторах', start_x, button_y, button_width, button_height, GOLD, (200, 170, 0),
                                   self.show_authors, self.table_image))

    def start_game(self):
         self.running = False
         self.animating = True
         self.animation_start_time = time.time()


    def show_about(self):
        beton_image = load_image('beton.png')
        return_image = load_image('return.png', -1)
        self.popup_window = PopupWindow(self.screen, "Здесь будет информация об игре", 400, 200, beton_image, return_image)
        self.popup_window.run()
        self.popup_window = None

    def show_authors(self):
         beton_image = load_image('beton.png')
         return_image = load_image('return.png', -1)
         self.popup_window = PopupWindow(self.screen, "Здесь информация об авторах", 400, 200, beton_image, return_image)
         self.popup_window.run()
         self.popup_window = None

    def run(self):
        while self.running or self.animating:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.running:
                  for button in self.buttons:
                      button.handle_event(event)

            self.screen.blit(self.background_image, (0, 0))
            if self.running:
                for button in self.buttons:
                    button.draw(self.screen)
            if self.animating:
                animation_time = time.time() - self.animation_start_time
                if animation_time < self.animation_duration:
                    progress = animation_time / self.animation_duration
                    
                    target_x = SCREEN_WIDTH // 2 - self.background_image.get_width() // 2
                    target_y = SCREEN_HEIGHT // 2 - self.background_image.get_height() // 2
                    
                    current_x = int(target_x * progress)
                    current_y = int(target_y * progress)

                    current_width = int(SCREEN_WIDTH + (self.background_image.get_width() - SCREEN_WIDTH) * progress)
                    current_height = int(SCREEN_HEIGHT + (self.background_image.get_height() - SCREEN_HEIGHT) * progress)

                    scaled_background = pygame.transform.scale(self.background_image, (current_width, current_height))
                    self.screen.blit(scaled_background, (current_x , current_y))

                    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                    alpha_value = int(255 * progress)
                    overlay.fill((255, 255, 255, alpha_value))
                    self.screen.blit(overlay, (0, 0))
                else:
                    self.animating = False
            pygame.display.flip()


font_size = 40

font1 = pygame.font.Font(None, font_size)
font2 = pygame.font.Font("data/DS-DIGIB.TTF", font_size)

clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
game_duration = 100

level = 1
digit_width = 20
digit_height = 20

PAUSE_BUTTON_X = 720
PAUSE_BUTTON_Y = 780
PAUSE_BUTTON_WIDTH = 120
PAUSE_BUTTON_HEIGHT = 40

y_offset = SCREEN_HEIGHT - digit_height


def draw_digit(screen, number, x, y, color):
    num_str = str(number).zfill(3)
    for i, digit in enumerate(num_str):
        digit_surface = font2.render(digit, True, color)
        digit_rect = digit_surface.get_rect(center=(x + digit_width * i + digit_width // 2, y + digit_height // 2))
        screen.blit(digit_surface, digit_rect)


def draw_text(screen, text, x, y, color):
    text_surface = font1.render(text, True, color)
    screen.blit(text_surface, (x, y))


def draw_clock_face(screen, x, y, width, height, color):
    pygame.draw.rect(screen, color, (x, y, width, height))


def draw_pause_button(screen, is_paused):
    text = "PAUSE" if not is_paused else "RESUME"
    text_surface = font1.render(text, True, WHITE)
    button_rect = pygame.Rect(PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT)
    pygame.draw.rect(screen, GRAY, button_rect)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen.blit(text_surface, text_rect)
    return button_rect


def main():
    level = 1
    chips_left = 1
    time_left = 100
    clock = pygame.time.Clock()
    size = SCREEN_WIDTH, SCREEN_HEIGHT
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption('Level Mover')

    start_window = StartWindow(screen)
    start_window.run()

    is_paused = False
    last_time = 0
    game_over = False
    level_complete = False
    trajectory = 'trajectory.txt'

    if not start_window.running:
        board = Board(BOARD_WIDTH, BOARD_HEIGHT)
        board.load_level(LEVEL_FILE, trajectory)

        inventory = Inventory(7, 1)
        inventory.set_view(board.left + TILE_SIZE,
                           board.top + board.cell_size * board.height + TILE_SIZE, TILE_SIZE)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                mouse_pos = pygame.mouse.get_pos()
                pause_button_rect = draw_pause_button(screen, is_paused)
                if pause_button_rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                    is_paused = not is_paused
                if event.type == pygame.KEYDOWN and not is_paused and not game_over and not level_complete:
                    dx = 0
                    dy = 0
                    if event.key == pygame.K_d:
                        dx = -1
                    if event.key == pygame.K_s:
                        dy = -1
                    if event.key == pygame.K_w:
                        dy = 1
                    if event.key == pygame.K_a:
                        dx = 1
                    chips_left = board.move_level(dx, dy, inventory, chips_left)
                    if board.p1.is_collide(board.water):
                        game_over = True
                    level_complete = board.check_portal_collision(chips_left, time_left, screen, inventory)

                if event.type == pygame.KEYDOWN and game_over:
                    if event.key == pygame.K_RETURN:
                        game_over = False
                        board.load_level(LEVEL_FILE, trajectory)
                        chips_left = 1
                        time_left = 100
                if event.type == pygame.KEYDOWN and level_complete:
                    if event.key == pygame.K_RETURN:
                        level_complete = False
                        board.load_level(LEVEL_FILE, trajectory)
                        chips_left = 1
                        time_left = 100

            if not is_paused and chips_left > 0 and not game_over and not level_complete:
                current_time = time.time()
                if last_time == 0:
                    last_time = current_time
                if current_time - last_time >= 1:
                    time_left -= 1
                    last_time = current_time
                if time_left < 0:
                    time_left = 100

            if not is_paused and not game_over and not level_complete:
                board.move_monsters()
                if board.check_monster_collision(board.monsters):
                    game_over = True

            screen.fill(BLACK)

            draw_text(screen, "TIME:", 700, 760 - font_size, YELLOW)
            draw_clock_face(screen, 790, 710, 70, 40, BLUE)
            draw_digit(screen, time_left, 794, 720, LIGHT_YELLOW)

            draw_text(screen, "LEVEL:", 90, 780, YELLOW)
            draw_clock_face(screen, 275, 775, 70, 40, BLUE)
            draw_digit(screen, level, 282, 782, LIGHT_YELLOW)

            draw_text(screen, "STARS LEFT:", 90, 760 - font_size, YELLOW)
            draw_clock_face(screen, 275, 710, 70, 40, BLUE)
            draw_digit(screen, chips_left, 280, 720, LIGHT_YELLOW)
            draw_pause_button(screen, is_paused)
            board.draw_level(screen)
            inventory.render(screen)
            if game_over:
                draw_text(screen, "GAME OVER!",
                          SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 50, RED)
                draw_text(screen, "Press Enter to restart", SCREEN_WIDTH // 2 - 150,
                          SCREEN_HEIGHT // 2, RED)
                inventory.items = []
            clock.tick(60)
            pygame.display.flip()