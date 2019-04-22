import pygame
from board import Board
from pygame import Rect


def draw_text(surface, message, font_size, center_position, color=(0, 0, 255)):
    font = pygame.font.Font('freesansbold.ttf', font_size)
    text = font.render(message, True, color)
    text_rect = text.get_rect()
    text_rect.center = center_position
    surface.blit(text, text_rect)


def create_button(width, height, message, selected=False):
    surf = pygame.Surface((width, height))
    if selected:
        surf.fill((0, 120, 255))
    else:
        surf.fill((120, 120, 120))
    pygame.draw.rect(surf, (0, 0, 0), surf.get_rect(), 1)
    draw_text(surf, message, height // 3, surf.get_rect().center, (0, 0, 0))
    return surf


def start_window(width, fps=60):
    """ Create a pygame window for the start screen """
    pygame.init()
    win = pygame.display.set_mode((width, width))
    pygame.display.set_caption("PyCarrom: Start")
    win_rect = win.get_rect()
    clock = pygame.time.Clock()
    """ Create a board to draw on the initial menu screen """
    board = Board(win_rect)
    run = True
    chosen = ["human", "human"]
    while run:
        clock.tick(fps)

        human_button_1 = create_button(width // 5, width // 10, "Human", chosen[0] == "human")
        human_button_1_rect = Rect(width * 2 // 10, width * 4 // 10, width * 2 // 10, width // 10)
        ai_button_1 = create_button(width // 5, width // 10, "AI", chosen[0] == "ai")
        ai_button_1_rect =  Rect(width * 2 // 10, width * 5 // 10, width * 2 // 10, width // 10)
        random_button_1 = create_button(width // 5, width // 10, "Random", chosen[0] == "random")
        random_button_1_rect = Rect(width * 2 // 10, width * 6 // 10, width * 2 // 10, width // 10)

        human_button_2 = create_button(width // 5, width // 10, "Human", chosen[1] == "human")
        human_button_2_rect = Rect(width * 6 // 10, width * 4 // 10, width * 2 // 10, width // 10)
        ai_button_2 = create_button(width // 5, width // 10, "AI", chosen[1] == "ai")
        ai_button_2_rect = Rect(width * 6 // 10, width * 5 // 10, width * 2 // 10, width // 10)
        random_button_2 = create_button(width // 5, width // 10, "Random", chosen[1] == "random")
        random_button_2_rect =  Rect(width * 6 // 10, width * 6 // 10, width * 2 // 10, width // 10)

        play_button = create_button(width * 4 // 10, width // 10, "Play")
        play_button_rect = Rect(width * 3 // 10, width * 8 // 10, width * 4 // 10, width // 10)

        board.draw(win)
        win.blit(human_button_1, human_button_1_rect)
        win.blit(ai_button_1, ai_button_1_rect)
        win.blit(random_button_1, random_button_1_rect)
        win.blit(human_button_2, human_button_2_rect)
        win.blit(ai_button_2, ai_button_2_rect)
        win.blit(random_button_2, random_button_2_rect)
        win.blit(play_button, play_button_rect)
        draw_text(win, "V/S", width//20, (width//2, width*11//20), (255, 255, 0))
        draw_text(win, "PyCarrom", width//10, (width//2, width*2//10))
        draw_text(win, "Two Player Carrom Game", width//30, (width//2, width*3//10), (0, 0, 0))
        draw_text(win, "Built on Python", width//30, (width//2, width*7//20), (0, 0, 0))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if human_button_1_rect.collidepoint(*mouse_pos):
                    chosen[0] = "human"
                elif ai_button_1_rect.collidepoint(*mouse_pos):
                    chosen[0] = "ai"
                elif random_button_1_rect.collidepoint(*mouse_pos):
                    chosen[0] = "random"

                if human_button_2_rect.collidepoint(*mouse_pos):
                    chosen[1] = "human"
                elif ai_button_2_rect.collidepoint(*mouse_pos):
                    chosen[1] = "ai"
                elif random_button_2_rect.collidepoint(*mouse_pos):
                    chosen[1] = "random"

                if play_button_rect.collidepoint(*mouse_pos):
                    run = False
    return chosen
