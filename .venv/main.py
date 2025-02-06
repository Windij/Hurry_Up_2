import sys
import pygame
import os
import time
import math
import sqlite3
pygame.init()
conn = sqlite3.connect('gamer.db')
cursor = conn.cursor()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 850
BOARD_WIDTH = 9
BOARD_HEIGHT = 9
TILE_SIZE = 60
BROWN = (123, 63, 0)
RED = (255, 0, 0)
GREEN = (21, 71, 52)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GOLD = (255, 215, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
LIGHT_YELLOW = (255, 255, 150)
WHITE = (255, 255, 255)
GRID_LINE_COLOR = BLACK
LEVEL1_FILE = 'level1.txt'
LEVEL2_FILE = "level2.txt"
TRAJECTORY1_FILE = 'trajectory1.txt'
TRAJECTORY2_FILE = 'trajectory2.txt'
size = SCREEN_WIDTH, SCREEN_HEIGHT
screen = pygame.display.set_mode(size)
pygame.display.set_caption('Level Mover')
all_sprites = pygame.sprite.Group()
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
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
pictures = {
    '#': load_image('стены.png'),
    '1': load_image('плитка 1.png'),
    '2': load_image('плитка 2.png'),
    '3': load_image('плитка 3.png'),
    '4': load_image('плитка черепки.png'),
    'Z': load_image('стены с зеленью.png'),
    'C': load_image('стены с цепями.png'),
    '.': load_image('простая плитка.png'),
    'y': load_image('ключ белый и жёлтый.png', colorkey=-1),
    'b': load_image('ключ белый и синий.png', colorkey=-1),
    'g': load_image('ключ белый и зелёный.png', colorkey=-1),
    'r': load_image('ключ белый и красный.png', colorkey=-1),
    'Y': load_image('дверь жёлтый.png'),
    'B': load_image('дверь синий.png'),
    'G': load_image('дверь зелёный.png'),
    'R': load_image('дверь красный.png'),
    'W': load_image('water_.png'),
    'S': load_image('sand.png'),
    '*': load_image('сундук.png'),
    'P': load_image('rog_run_.png', colorkey=-1),
    'O': load_image('none_activated_portal.png', colorkey=-1),
    'M': load_image('skeleton_run.png', colorkey=-1)
}
class Base(pygame.sprite.Sprite):
    def __init__(self, x, y, color, indicator=0, columns=1, rows=1):
        super().__init__(all_sprites)
        self.indicator = indicator
        self.frames = []
        self.cut_sheet(color, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE
        self.flag_for_reverse = -1
    def move(self, dx, dy):
        self.rect.x += dx * TILE_SIZE
        self.rect.y += dy * TILE_SIZE
    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns, sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(frame_location, self.rect.size)))
    def reverse_image(self, dx):
        if dx == 0:
            return
        if dx != self.flag_for_reverse:
            for i, frame in enumerate(self.frames):
                self.frames[i] = pygame.transform.flip(frame, True, False)
            self.flag_for_reverse = dx
    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
        self.image = self.frames[self.cur_frame]
class Player(Base):
    def __init__(self, x, y, color, columns):
        super().__init__(x, y, color, columns=columns)
        self.mask = pygame.mask.from_surface(self.image)
    def move(self, dx, dy):
        pass
    def is_collide(self, all_tiles):
        return pygame.sprite.spritecollideany(self, all_tiles)
class Door(Base):
    def __init__(self, x, y, color, indicator, columns):
        super().__init__(x, y, color, indicator=indicator, columns=columns)
        self.is_open = False
class Monster(Base):
    def __init__(self, color, trajectory_file, columns):
        self.trajectory = self.load_trajectory(trajectory_file)
        self.current_point_index = 0
        self.next_point_index = 1
        self.speed = 5
        self.x, self.y = self.trajectory[0]
        super().__init__(self.x, self.y, color, columns=columns)
        self.mask = pygame.mask.from_surface(self.image)
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
        self.reverse_image(dx)
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance == 0:
            return 0, 0
        speed_x = self.speed * dx / distance
        speed_y = self.speed * dy / distance
        return speed_x, speed_y
    def update_monster(self):
        speed_x, speed_y = self.calculate_movement()
        self.x += speed_x
        self.y += speed_y
        self.rect.x = self.x
        self.rect.y = self.y
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
        if self.x == next_x and self.y == next_y:
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
            if tile_type in '#ZC':
                wall.add(tile)
            elif tile_type == 'P':
                p1 = Player(x, y, pictures['P'], columns=6)
                player.add(p1)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type in 'rbgy':
                tile.indicator = 'rbgy'.index(tile_type)
                keys.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type in 'RBGY':
                tile.indicator = 'RBGY'.index(tile_type)
                doors.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == '*':
                chips.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'W':
                water.add(Base(x, y, pictures[tile_type], columns=6))
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'S':
                sand.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'O':
                portal.add(tile)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type == 'M':
                monster = Monster(pictures['M'], trajectory, columns=6)
                monsters.add(monster)
                floor.add(Base(x, y, pictures['.']))
            elif tile_type in '.1234':
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
        self.p1.reverse_image(dx)
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
                if any(pygame.sprite.collide_mask(block, tile) for block in self.sand if tile != block):
                    tile.move(dx, dy)
                    flag = True
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
            self.p1.reverse_image(dx)
        return chips_left
    def move_monsters(self):
        for monster in self.monsters:
            monster.update_monster()
    def draw_level(self, screen):
        self.screen_2.fill((0, 0, 0, 0))
        self.render(self.screen_2)
        self.wall.draw(self.screen_2)
        self.floor.draw(self.screen_2)
        self.keys.draw(self.screen_2)
        self.doors.draw(self.screen_2)
        self.chips.draw(self.screen_2)
        self.sand.draw(self.screen_2)
        self.portal.draw(self.screen_2)
        self.player.draw(self.screen_2)
        self.water.draw(self.screen_2)
        self.monsters.draw(self.screen_2)
        screen.blit(self.screen_2, (self.left, self.top))
    def check_portal_collision(self, chips_left, time_left, screen, inventory):
        if self.p1.is_collide(self.portal) and chips_left == 0:
            total_score = 1000 + time_left * 10
            record = self.load_record()  # Call using self
            improvement = total_score - record if record != 0 else "——"
            self.save_record(time_left, total_score)  # Call using self, passing in values
            inventory.items = []
            return True
        return False
    def check_monster_collision(self, monsters):
        for monster in monsters:
            if pygame.sprite.collide_mask(self.p1, monster):
                return True
        return False
    def load_record(self):
        try:
            sqlite_connection = sqlite3.connect('gamer.db')
            cursor = sqlite_connection.cursor()  # Establish cursor
            cursor.execute("SELECT MAX(score) FROM gamer WHERE level_name=1")  # Select highest score for level 1
            record = cursor.fetchone()[0]
            sqlite_connection.close()
            return record if record is not None else 0
        except sqlite3.Error as error:
            print(f"Error loading record: {error}")
            return 0
    def save_record(self, time_left, total_score):
        try:
            sqlite_connection = sqlite3.connect('gamer.db')
            cursor = sqlite_connection.cursor()
            # Check if a record with level_name = 1 exists
            cursor.execute("SELECT id FROM gamer WHERE level_name=1")
            existing_record = cursor.fetchone()
            if existing_record:
                # Update the existing record
                cursor.execute('UPDATE gamer SET time = ?, score = ? WHERE level_name = 1', (time_left, total_score))
            # else:
            # # Insert a new record
            #      cursor.execute('INSERT INTO gamer (time, score, level_name) VALUES (?, ?, ?)', (time_left, total_score, 1))
            sqlite_connection.commit()
            sqlite_connection.close()
        except sqlite3.Error as error:
            print(f"Error saving record: {error}")
            return 0
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
    def __init__(self, text, x, y, width, height, color, hover_color, action=None, nonpress_image=None,
                 press_image=None):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.action = action
        if self.text != '':
            self.font = pygame.font.Font(None, 36)
            self.text_surface = self.font.render(text, True, BLACK)
            self.text_rect = self.text_surface.get_rect(center=(x + width // 2, y + height // 2))
        self.image = nonpress_image
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(x, y)
        self.pressed_image = press_image
        self.nonpress_image = nonpress_image
    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        if self.image:
            if self.rect.collidepoint(mouse_pos):
                screen.blit(self.image, self.rect)
                self.image = self.pressed_image
            else:
                screen.blit(self.image, self.rect)
                self.image = self.nonpress_image
        else:
            if self.rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, self.hover_color, self.rect)
            else:
                pygame.draw.rect(screen, self.color, self.rect)
        if self.text != '':
            screen.blit(self.text_surface, self.text_rect)
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos) and self.action:
                self.action()
class PopupWindow:
    def __init__(self, screen, text, width, height, background_image=None, close_image=None, pressed_close_image=None):
        self.screen = screen
        self.width = width
        self.height = height
        self.text = text
        self.font = pygame.font.Font(None, 24)
        self.text_surface = self.font.render(text, True, BLACK)
        self.text_rect = self.text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - width // 2, SCREEN_HEIGHT // 2 - height // 2, width, height)
        self.running = True
        self.close_button = Button('', self.rect.x + self.width - 140, self.rect.y + self.height, 120, 30,
                                   RED, (200, 0, 0), self.close, nonpress_image=close_image,
                                   press_image=pressed_close_image)
        self.background_image = background_image
        self.line_spacing = 5
        self.text_surfaces = self.render_text()
    def close(self):
        self.running = False
    def render_text(self):
        lines = self.text.split('\n')
        text_surfaces = []
        y = self.rect.y + 20
        for line in lines:
            text_surface = self.font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y))
            text_surfaces.append((text_surface, text_rect))
            y += text_surface.get_height() + self.line_spacing
        return text_surfaces
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
            for text_surface, text_rect in self.text_surfaces:
                self.screen.blit(text_surface, text_rect)
            self.close_button.draw(self.screen)
            pygame.display.flip()
class StartWindow:
    def __init__(self, screen):
        self.screen = screen
        self.buttons = []
        self.running = True
        self.background_image = load_image('dungeon_entrance.jpg')
        self.play = load_image('play_.png', colorkey=-1)
        self.pressed_play = load_image('pressed_play_.png', colorkey=-1)
        self.about = load_image('about_.png', colorkey=-1)
        self.pressed_about = load_image('pressed_about_.png', colorkey=-1)
        self.rule = load_image('rule_.png', colorkey=-1)
        self.pressed_rule = load_image('pressed_rule_.png', colorkey=-1)
        self.beton_image = pygame.transform.scale(load_image('wallpaper_.png', colorkey=-1), (450, 300))
        self.exit = load_image('exit_.png', colorkey=-1)
        self.pressed_exit = load_image('pressed_exit_.png', colorkey=-1)
        self.start_game_table_rect = None
        self.create_buttons()
        self.popup_window = None
        self.animation_start_time = 0
        self.animation_duration = 2
        self.animating = False
    def create_buttons(self):
        button_width = 200
        button_height = 50
        start_x = SCREEN_WIDTH // 2
        button_y = 200
        space = 80
        self.buttons.append(
            Button('', start_x - 100, button_y, button_width, button_height, GREEN, (0, 200, 0), self.start_game,
                   self.play, self.pressed_play))
        self.start_game_table_rect = self.buttons[0].rect
        button_y += space
        self.buttons.append(
            Button('', start_x - 90, button_y, button_width, button_height, BLUE, (0, 0, 200), self.show_about,
                   nonpress_image=self.rule, press_image=self.pressed_rule))
        button_y += space
        self.buttons.append(Button('', start_x - 100, button_y, button_width, button_height, GOLD, (200, 170, 0),
                                   self.show_authors, nonpress_image=self.about, press_image=self.pressed_about))
    def start_game(self):
        self.running = False
    def show_about(self):
        self.popup_window = PopupWindow(self.screen,
                                        '\n\n\nУправляйте персонажем с помощью WASD.'
                                        '\n\nИзбегайте опасностей.\n\nСледи за временем.'
                                        '\n\nСобирайте сундуки.',
                                        450, 300,
                                        self.beton_image, self.exit, self.pressed_exit)
        self.popup_window.run()
        self.popup_window = None
    def show_authors(self):
        self.popup_window = PopupWindow(self.screen,
                                        '\n\n\n\n\nНад проектом работали:\nСпивак Максим Игоревич - @Maxusmini\n'
                                        'Кривова Полина Дмитриевна - @polly_kriv\n2024-2025\n', 450, 300,
                                        self.beton_image, self.exit, self.pressed_exit)
        self.popup_window.run()
        self.popup_window = None
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.running:
                    for button in self.buttons:
                        button.handle_event(event)
            self.screen.fill(BLACK)
            self.screen.blit(self.background_image, ((SCREEN_WIDTH - self.background_image.get_width()) // 2, 0))
            if self.running:
                for button in self.buttons:
                    button.draw(self.screen)
            pygame.display.flip()

class DB():
    def __init__(self, main_screen):
        self.WIDTH = 500
        self.HEIGHT = 250
        self.modal = pygame.Surface((self.WIDTH, self.HEIGHT))
        self.modal.fill(GRAY)
        self.screen = main_screen
        self.font3 = pygame.font.Font(None, 24)

        try:
            self.conn = sqlite3.connect('gamer.db')
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            sys.exit()

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS gamer (
            id INTEGER PRIMARY KEY,
            level_name INTEGER,
            score INTEGER,
            time INTEGER
        )''')
        self.conn.commit()
        self.cursor.execute("SELECT COUNT(*) FROM gamer")
        count = self.cursor.fetchone()[0]
        if count == 0:
            initial_data = [
                (1, 1, None, None),
                (2, 2, None, None),  # Убедитесь, что здесь нет 'lesson3'
            ]
            self.cursor.executemany("INSERT INTO gamer (id, level_name, score, time) VALUES (?, ?, ?, ?)", initial_data)
            self.conn.commit()

    def draw_text(self, text, font, color, x, y, align="left"):
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if align == "left":
            text_rect.topleft = (x, y)
        elif align == "center":
            text_rect.center = (x, y)
        elif align == "right":
            text_rect.topright = (x, y)
        self.modal.blit(text_surface, text_rect)
        return text_rect

    def draw_table(self):
        header_y = 40
        row_height = 30
        column_spacing = 150
        level_x = 50
        score_x = level_x + column_spacing
        time_x = score_x + column_spacing
        pygame.draw.line(self.modal, BLACK, (level_x - 10, header_y + 20), (time_x + 100, header_y + 20), 1)
        self.draw_text("Level", self.font3, BLACK, level_x, header_y)
        self.draw_text("Score", self.font3, BLACK, score_x + 40, header_y + 6, align="center")
        self.draw_text("Time", self.font3, BLACK, time_x + 20, header_y + 6, align="center")
        self.cursor.execute("SELECT level_name, score, time FROM gamer")
        scores = self.cursor.fetchall()
        y_pos = header_y + row_height
        lesson_rects = {}
        for lesson_number, score, time in scores:
            pygame.draw.line(self.modal, GRAY, (level_x - 10, y_pos + 20), (time_x + 100, y_pos + 20), 1)
            level_text = f"{lesson_number}    LESSON {lesson_number}"
            lesson_rects[lesson_number] = self.draw_text(level_text, self.font3, BLACK, level_x, y_pos)
            score_text = str(score) if score is not None else "---"
            self.draw_text(score_text, self.font3, BLACK, score_x + 40, y_pos + 6, align="center")
            time_text = str(time) if time is not None else "---"
            self.draw_text(time_text, self.font3, BLACK, time_x + 20, y_pos + 6, align="center")
            y_pos += row_height

        pygame.draw.line(self.modal, BLACK, (level_x - 10, y_pos + 20), (time_x + 100, y_pos + 20), 1)
        self.draw_text("LEVEL SET TOTAL", self.font3, BLACK, level_x, y_pos)

        # Подсчет и вывод общего счета
        self.cursor.execute("SELECT sum(score) FROM gamer WHERE score IS NOT NULL")
        total = self.cursor.fetchone()[0]
        if total is None:
            total = 0
        self.draw_text(str(total), self.font3, BLACK, score_x + 40, y_pos + 6, align="center")

        # Добавление текста для закрытия таблицы
        self.draw_text("To close the table, press the 'm' key", self.font3, BLACK, level_x, y_pos + 40)

        return lesson_rects

    def run(self):
        running = True
        lesson_rects = {}
        while running:
            self.modal.fill(GRAY)  # Заливаем модальное окно
            lesson_rects = self.draw_table()  # Рисуем таблицу
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                    running = False  # Закрыть модальное окно при нажатии 'm'

            self.screen.blit(self.modal, (100, 100))
            pygame.display.flip()

    def close(self):
        self.conn.close()

class Level_button(pygame.sprite.Sprite):
    def __init__(self, level_image, center):
        super().__init__()
        self.image_normal = level_image
        self.image_pressed = pygame.transform.scale(level_image, (level_image.get_width(), level_image.get_height()))  # Используйте то же изображение или другое
        self.image = self.image_normal
        self.rect = self.image.get_rect(center=center)
        self.is_pressed = False
    def update(self, mouse_pos, mouse_click):
        if self.rect.collidepoint(mouse_pos):
            if mouse_click:
                self.is_pressed = not self.is_pressed
                if self.is_pressed:
                    self.image = self.image_pressed  # Если нажат, меняем изображение
                    self.open_new_window()  # вызываем метод для открытия нового окна
                else:
                    self.image = self.image_normal  # Если не нажат, возвращаем оригинальное изображение
    def open_new_window(self):
        # Здесь происходит логика открытия нового окна или уровня
        print("Кнопка нажата! Открывается новое окно.")
    def draw(self, surface):
        surface.blit(self.image, self.rect)
pygame.init()
font_size = 40
font1 = pygame.font.Font(None, font_size)
font2 = pygame.font.Font("data/DS-DIGIB.TTF", font_size)
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()
game_duration = 100
level = 1
digit_width = 20
digit_height = 20
PAUSE_BUTTON_X = 700
PAUSE_BUTTON_Y = 760
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
class Music_button(pygame.sprite.Sprite):
    def __init__(self, image_normal, image_pressed, center):
        super().__init__()
        self.image_normal = image_normal
        self.image_pressed = image_pressed
        self.image = self.image_normal
        self.rect = self.image.get_rect(center=center)
        self.is_pressed = False
    def update(self, mouse_pos, mouse_click):
        if self.rect.collidepoint(mouse_pos):
            if mouse_click:
               self.is_pressed = not self.is_pressed
               if self.is_pressed:
                   self.image = self.image_pressed
               else:
                   self.image = self.image_normal
    def draw(self, surface):
        surface.blit(self.image, self.rect)
class Pause_button(Button):
    def __init__(self, text, x, y, width, height, color, hover_color, nonpress_image=None
                 , press_image=None):
        super().__init__(text, x, y, width, height, color, hover_color, nonpress_image=nonpress_image,
                         press_image=press_image)
        self.is_paused = False
    def pause(self, is_paused):
        self.is_paused = is_paused
        self.image = self.pressed_image if self.is_paused else self.nonpress_image
    def draw(self, screen):
        screen.blit(self.image, self.rect)


# Основная функция игры
def main():
    pygame.init()  # Инициализация Pygame
    screen = pygame.display.set_mode((1000, 850))  # Установите размер экрана

    # Определение переменных
    current_level = 1
    chips_left = 5
    time_left = 100
    clock = pygame.time.Clock()
    start_window = StartWindow(screen)
    start_window.run()
    dataBase = DB(screen)  # Создаем экземпляр БД

    running = True
    is_paused = False
    last_time = 0
    game_over = False
    level_complete = False
    win_screen_active = False
    trajectory = TRAJECTORY1_FILE
    time_for_animation = pygame.time.get_ticks()  # Используем таймер Pygame
    image_normal = load_image('music_but.png', colorkey=-1)
    image_pressed = load_image('pressed_music_but.png', colorkey=-1)
    level_image = load_image('level_but.png', colorkey=-1)

    level_center = (50, 150)
    level_button = Level_button(level_image, level_center)

    button_center = (50, 50)
    music_button = Music_button(image_normal, image_pressed, button_center)

    all_sprites = pygame.sprite.Group(music_button, level_button)
    pygame.mixer.music.load("music.mp3")

    if not start_window.running:
        board = Board(BOARD_WIDTH, BOARD_HEIGHT)
        board.load_level(LEVEL1_FILE, trajectory)
        inventory = Inventory(7, 1)
        inventory.set_view(board.left + TILE_SIZE,
                           board.top + board.cell_size * board.height + TILE_SIZE,
                           board.cell_size)

        pause_button = Pause_button('', PAUSE_BUTTON_X, PAUSE_BUTTON_Y, PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT,
                                    GRAY, BLUE, nonpress_image=load_image('pause_.png', colorkey=-1),
                                    press_image=load_image('pressed_pause_.png', colorkey=-1))

        is_music_playing = False
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                mouse_pos = pygame.mouse.get_pos()
                if pause_button.rect.collidepoint(mouse_pos) and pygame.mouse.get_pressed()[0]:
                    is_paused = not is_paused
                    pause_button.pause(is_paused)

                mouse_click = False
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_click = True
                    music_button.update(mouse_pos, mouse_click)

                if music_button.is_pressed:
                    if is_music_playing:
                        is_music_playing = True
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.pause()
                        is_music_playing = False
                elif mouse_click and is_music_playing == False:
                    pygame.mixer.music.play(-1)  # Повтор музыкального сопровождения

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
                    if chips_left == 0:
                        for tile in board.portal:
                            tile.image = load_image('activated_portal.png', colorkey=-1)
                    if board.p1.is_collide(board.water):
                        game_over = True
                    if board.check_portal_collision(chips_left, time_left, screen, inventory):
                        level_complete = True
                        board.portal_active = True

                if event.type == pygame.KEYDOWN:
                    if game_over and event.key == pygame.K_RETURN:
                        game_over = False
                        board.load_level(LEVEL1_FILE, trajectory)
                        chips_left = 5
                        time_left = 100

                if level_complete:
                    if current_level == 2:
                        win_screen_active = True
                        level_complete = False
                    else:
                        level_complete = False
                        current_level += 1
                        if current_level == 2:
                            board.load_level(LEVEL2_FILE, TRAJECTORY2_FILE)
                        chips_left = 5
                        time_left = 100

                if win_screen_active and event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        current_level = 1
                        chips_left = 5
                        time_left = 100
                        win_screen_active = False
                        board.load_level(LEVEL1_FILE, TRAJECTORY1_FILE)

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if level_button.rect.collidepoint(mouse_pos):
                        dataBase.run()  # Запустить модальное окно БД

            if not is_paused and chips_left > 0 and not game_over and not level_complete:
                current_time = time.time()
                if last_time == 0:
                    last_time = current_time
                if current_time - last_time >= 1:
                    time_left -= 1
                    last_time = current_time
                if time_left <= 0:
                    game_over = True
            if not is_paused and not game_over and not level_complete:
                board.move_monsters()
                if board.check_monster_collision(board.monsters):
                    game_over = True

            screen.fill(BLACK)

            if win_screen_active:
                win_image = load_image("win.png")
                win_rect = win_image.get_rect(center=screen.get_rect().center)
                screen.blit(win_image, win_rect)
            else:
                draw_text(screen, "TIME:", 700, 740 - font_size, YELLOW)
                draw_clock_face(screen, 790, 690, 70, 40, GREEN)
                draw_digit(screen, time_left, 794, 700, LIGHT_YELLOW)
                draw_text(screen, "LEVEL:", 90, 780, YELLOW)
                draw_clock_face(screen, 275, 775, 70, 40, GREEN)
                draw_digit(screen, current_level, 282, 782, LIGHT_YELLOW)
                draw_text(screen, "STARS LEFT:", 90, 740 - font_size, YELLOW)
                draw_clock_face(screen, 275, 690, 70, 40, GREEN)
                draw_digit(screen, chips_left, 280, 700, LIGHT_YELLOW)
                pause_button.draw(screen)
                board.draw_level(screen)
                inventory.render(screen)

                if time_for_animation < current_time:
                    board.player.update()
                    board.monsters.update()
                    time_for_animation = current_time + 0.1
                    board.water.update()

                if game_over:
                    die_image = load_image("die_window_.png")
                    die_rect = die_image.get_rect()
                    die_rect.topleft = (325, 107)
                    inventory.items = []
                    screen.blit(die_image, die_rect)

                clock.tick(30)
                all_sprites.draw(screen)

            pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()