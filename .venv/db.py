import pygame
import sqlite3
import time
import sys

pygame.init()

WIDTH = 500
HEIGHT = 250
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Scores")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

font = pygame.font.Font(None, 24)

conn = sqlite3.connect('gamer.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS gamer (
        id INTEGER PRIMARY KEY,
        level_name INTEGER,
        score INTEGER,
        time INTEGER
    )
''')
conn.commit()

cursor.execute("SELECT COUNT(*) FROM gamer")
count = cursor.fetchone()[0]
if count == 0:
    initial_data = [
        (1, 1, None, None),
        (2, 2, None, None),
        (3, 3, None, None)
    ]
    cursor.executemany("INSERT INTO gamer (id, level_name, score, time) VALUES (?, ?, ?, ?)", initial_data)
    conn.commit()


def draw_text(text, font, color, x, y, align="left"):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "left":
        text_rect.topleft = (x, y)
    elif align == "center":
        text_rect.center = (x, y)
    elif align == "right":
        text_rect.topright = (x, y)
    screen.blit(text_surface, text_rect)
    return text_rect


def draw_table():
    header_y = 40
    row_height = 30
    column_spacing = 150
    level_x = 50
    score_x = level_x + column_spacing
    time_x = score_x + column_spacing

    pygame.draw.line(screen, BLACK, (level_x - 10, header_y + 20), (time_x + 100, header_y + 20), 1)
    header_rect = draw_text("Level", font, BLACK, level_x, header_y)
    score_header_rect = draw_text("Score", font, BLACK, score_x+40, header_y+6, align="center")
    time_header_rect = draw_text("Time", font, BLACK, time_x+20, header_y+6, align="center")

    cursor.execute("SELECT level_name, score, time FROM gamer")
    scores = cursor.fetchall()

    y_pos = header_y + row_height
    lesson_rects = {}
    for lesson_number, score, time in scores:
        pygame.draw.line(screen, GRAY, (level_x - 10, y_pos + 20), (time_x + 100, y_pos + 20),
                         1)
        level_text = f"{lesson_number}    LESSON {lesson_number}"
        lesson_rects[lesson_number] = draw_text(level_text, font, BLACK, level_x, y_pos)
        score_text = str(score) if score is not None else "---"
        draw_text(score_text, font, BLACK, score_x+40, y_pos+6, align="center")
        time_text = str(time) if time is not None else "---"
        draw_text(time_text, font, BLACK, time_x+20, y_pos+6, align="center")
        y_pos += row_height

    pygame.draw.line(screen, BLACK, (level_x - 10, y_pos + 20), (time_x + 100, y_pos + 20), 1)
    draw_text("LEVEL SET TOTAL", font, BLACK, level_x, y_pos)
    cursor.execute("SELECT sum(score) FROM gamer WHERE score IS NOT NULL")
    total = cursor.fetchone()[0]
    if total is None:
        total = 0
    draw_text(str(total), font, BLACK, score_x+40, y_pos+6, align="center")
    return lesson_rects


def handle_click(lesson_rects, mouse_pos):
    for lesson_number, rect in lesson_rects.items():
        if rect.collidepoint(mouse_pos):
            run_level(lesson_number)


def run_level(level_number):
    level_running = True
    level_count = 0
    while level_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                level_running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    level_running = False

        screen.fill(WHITE)
        pygame.display.flip()


running = True
lesson_rects = {}
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            handle_click(lesson_rects, mouse_pos)

    screen.fill(WHITE)
    lesson_rects = draw_table()

    pygame.display.flip()

conn.close()
pygame.quit()