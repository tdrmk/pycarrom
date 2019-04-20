from pygame import Rect
from pygame import Vector2
import pygame
from math import radians, sqrt
from coin import Coin


class Board:
    """ Length and mass of various components, in absolute units from Carrom Standard, (in cm and g) """
    BOARD_LENGTH = 74
    FRAME_LENGTH = 7.6
    TOTAL_LENGTH = BOARD_LENGTH + 2 * FRAME_LENGTH
    POCKET_RADIUS = 2.25
    STRIKER_MASS = 15
    STRIKER_RADIUS = 2.065
    COIN_RADIUS = 1.59
    COIN_MASS = 5.5
    BASE_LENGTH = 47
    BASE_HEIGHT = 3.18
    BASE_RADIUS = BASE_HEIGHT / 2
    BASE_DISTANCE = 10.15
    BASE_OFFSET = (BOARD_LENGTH - BASE_LENGTH) / 2
    BASE_INNER_RADIUS = 1.27
    CENTER_OUTER_RADIUS = 8.5
    CENTER_INNER_RADIUS = 1.59
    ARROW_DIAMETER = 6.35
    ARROW_RADIUS = ARROW_DIAMETER / 2
    ARROW_OFFSET = 5
    ARROW_LENGTH = 26.7

    def __init__(self, board: Rect):
        """ Construct all the carrom board parameters required to draw the carrom board layout """
        """ Board must be square in shape """
        assert board.width == board.height
        self.board = board
        self.frame_width = int(board.width * Board.FRAME_LENGTH / Board.TOTAL_LENGTH)
        """ Coins are restricted to the container """
        self.container = board.inflate(-2 * self.frame_width, -2 * self.frame_width)
        """ Calculate the multiplier by which to scale parameters to obtain values wrt board"""
        m = self.board.width / Board.TOTAL_LENGTH
        self.m = m
        """ Calculate the pocket radius and the center positions """
        self.pocket_radius = m * Board.POCKET_RADIUS
        self.coin_radius = m * Board.COIN_RADIUS
        self.striker_radius = m * Board.STRIKER_RADIUS
        self.pocket_centers = [
            Vector2(self.container.left + self.pocket_radius, self.container.top + self.pocket_radius),
            Vector2(self.container.right - self.pocket_radius, self.container.top + self.pocket_radius),
            Vector2(self.container.right - self.pocket_radius, self.container.bottom - self.pocket_radius),
            Vector2(self.container.left + self.pocket_radius, self.container.bottom - self.pocket_radius),
        ]
        """ These are solely defined for the purpose of rebounds """
        self.diagonal_pocket_opposite = [
            (self.container.right - self.striker_radius, self.container.bottom - self.striker_radius),
            (self.container.left + self.striker_radius, self.container.bottom - self.striker_radius),
            (self.container.left + self.striker_radius, self.container.top + self.striker_radius),
            (self.container.right - self.striker_radius, self.container.top + self.striker_radius),
        ]
        self.normal_vectors = [
            (Vector2(-1, 0), Vector2(0, -1)),
            (Vector2(1, 0), Vector2(0, -1)),
            (Vector2(1, 0), Vector2(0, 1)),
            (Vector2(-1, 0), Vector2(0, 1)),
        ]
        """ Calculate the base line positions, the lines defining the region where player places the striker """
        base_offset = m * Board.BASE_OFFSET
        base_distance = m * Board.BASE_DISTANCE
        base_height = m * Board.BASE_HEIGHT
        base_length = m * Board.BASE_LENGTH
        base_radius = m * Board.BASE_RADIUS

        self.base_lines = [((self.container.left + base_offset + base_radius, self.container.top + base_distance),
                            (self.container.left + base_offset + base_length - base_radius,
                             self.container.top + base_distance)),
                           ((self.container.left + base_offset + base_radius,
                             self.container.top + base_distance + base_height),
                            (self.container.left + base_offset + base_length - base_radius,
                             self.container.top + base_distance + base_height)),
                           ((self.container.left + base_offset + base_radius, self.container.bottom - base_distance),
                            (self.container.left + base_offset + base_length - base_radius,
                             self.container.bottom - base_distance)),
                           ((self.container.left + base_offset + base_radius,
                             self.container.bottom - base_distance - base_height),
                            (self.container.left + base_offset + base_length - base_radius,
                             self.container.bottom - base_distance - base_height)),
                           ((self.container.left + base_distance, self.container.top + base_offset + base_radius),
                            (self.container.left + base_distance,
                             self.container.top + base_offset + base_length - base_radius)),
                           ((self.container.left + base_distance + base_height,
                             self.container.top + base_offset + base_radius),
                            (self.container.left + base_distance + base_height,
                             self.container.bottom - base_offset - base_radius)),
                           ((self.container.right - base_distance, self.container.top + base_offset + base_radius),
                            (self.container.right - base_distance,
                             self.container.top + base_offset + base_length - base_radius)),
                           ((self.container.right - base_distance - base_height,
                             self.container.top + base_offset + base_radius),
                            (self.container.right - base_distance - base_height,
                             self.container.bottom - base_offset - base_radius))]
        """ Base circle centers, the circles at the end of base lines """
        self.base_circle_centers = [(int(self.container.left + base_offset + base_radius),
                                     int(self.container.top + base_distance + base_radius)),
                                    (int(self.container.left + base_offset + base_length - base_radius),
                                     int(self.container.top + base_distance + base_radius)),
                                    (int(self.container.left + base_offset + base_radius),
                                     int(self.container.bottom - base_distance - base_radius)),
                                    (int(self.container.left + base_offset + base_length - base_radius),
                                     int(self.container.bottom - base_distance - base_radius)),
                                    (int(self.container.left + base_distance + base_radius),
                                     int(self.container.top + base_offset + base_radius)),
                                    (int(self.container.left + base_distance + base_radius),
                                     int(self.container.bottom - base_offset - base_radius)),
                                    (int(self.container.right - base_distance - base_radius),
                                     int(self.container.top + base_offset + base_radius)),
                                    (int(self.container.right - base_distance - base_radius),
                                     int(self.container.bottom - base_offset - base_radius))]
        """ Arrow lines """
        arrow_start = self.pocket_radius * 2 + m * Board.ARROW_OFFSET / sqrt(2)
        arrow_end = arrow_start + m * Board.ARROW_LENGTH / sqrt(2)
        self.arrow_lines = [((int(self.container.left + arrow_start), int(self.container.top + arrow_start)),
                             (int(self.container.left + arrow_end), int(self.container.top + arrow_end))),
                            ((int(self.container.left + arrow_start), int(self.container.bottom - arrow_start)),
                             (int(self.container.left + arrow_end), int(self.container.bottom - arrow_end))),
                            ((int(self.container.right - arrow_start), int(self.container.bottom - arrow_start)),
                             (int(self.container.right - arrow_end), int(self.container.bottom - arrow_end))),
                            ((int(self.container.right - arrow_start), int(self.container.top + arrow_start)),
                             (int(self.container.right - arrow_end), int(self.container.top + arrow_end)))]
        arc_offset = int(arrow_end - m * Board.ARROW_RADIUS * (1 + 1 / sqrt(2)))
        arc_width = int(m * Board.ARROW_DIAMETER)
        """ Arrow Arcs"""
        self.arrow_arcs = [(Rect(self.container.left + arc_offset, self.container.top + arc_offset, arc_width,
                                 arc_width), radians(180), radians(90)),
                           (Rect(self.container.left + arc_offset, self.container.bottom - arc_offset, arc_width,
                                 -arc_width), radians(-90), radians(180)),
                           (Rect(self.container.right - arc_offset, self.container.bottom - arc_offset, -arc_width,
                                 -arc_width), radians(0), radians(-90)),
                           (Rect(self.container.right - arc_offset, self.container.top + arc_offset, -arc_width,
                                 arc_width), radians(90), radians(0))]

        self.base_radius = m * Board.BASE_RADIUS
        self.base_distance = m * Board.BASE_DISTANCE
        self.base_offset = m * Board.BASE_OFFSET
        self.base_inner_radius = m * Board.BASE_INNER_RADIUS
        self.center_outer_radius = m * Board.CENTER_OUTER_RADIUS
        self.center_inner_radius = m * Board.CENTER_INNER_RADIUS

    def draw(self, win):
        """ This function is called to draw the carrom board and its components on the given window"""
        """ Draw the board and the frame """
        pygame.draw.rect(win, (100, 0, 0), self.board)
        pygame.draw.rect(win, (128, 100, 100), self.container)
        """ Draw the pockets """
        for pocket_center in self.pocket_centers:
            pygame.draw.circle(win, (128, 128, 128), (int(pocket_center.x), int(pocket_center.y)),
                               int(self.pocket_radius))
        """ Draw the base lines """
        for index, base_line in enumerate(self.base_lines):
            pygame.draw.line(win, (100, 50, 50), base_line[0], base_line[1], 3 if index % 2 == 0 else 1)
        """ Draw the base circles """

        for base_circle_center in self.base_circle_centers:
            pygame.draw.circle(win, (100, 50, 50), base_circle_center, int(self.base_radius), 1)
            pygame.draw.circle(win, (100, 50, 50), base_circle_center, int(self.base_inner_radius))
        """ Draw the center circles """

        pygame.draw.circle(win, (100, 50, 50), self.container.center, int(self.center_outer_radius), 2)
        pygame.draw.circle(win, (100, 50, 50), self.container.center, int(self.center_inner_radius))
        """ Draw the arrow lines """
        for arrow_line in self.arrow_lines:
            pygame.draw.line(win, (100, 50, 50), arrow_line[0], arrow_line[1])

        """ Draw the arrow arcs """
        for arrow_arc in self.arrow_arcs:
            arrow_arc[0].normalize()
            pygame.draw.arc(win, (100, 50, 50), arrow_arc[0], arrow_arc[1], arrow_arc[2], 2)

    def get_container(self):
        """ Return the container to which the carrom coins are restricted to """
        return self.container

    def pocketed(self, coin: Coin):
        """ Returns True if the given coin is pocketed,
        that is coin completely lies within one of the pockets """
        for pocket_center in self.pocket_centers:
            if coin.position.distance_to(pocket_center) < self.pocket_radius - coin.radius:
                """ If coin is completely inside the pocket """
                return True
        return False

    def draw_captured_coins(self, win, player, captured_coins):
        """ This function draws the captured coins of the player on the frame """
        # print("Captured Coins,", player, captured_coins)
        for index, coin in enumerate(captured_coins):
            x_offset = int(self.m * (Board.FRAME_LENGTH + index * Board.COIN_RADIUS * 3))
            y_offset = int(self.board.bottom - 2 * self.coin_radius) if player == 0 else \
                int(self.board.top + 2 * self.coin_radius)
            pygame.draw.circle(win, coin.color, (x_offset, y_offset), int(self.coin_radius))

    """ Functions for striker positions """

    def get_striker_x_limits(self):
        """ Returns the min and max position of the striker along x axis """
        return self.container.left + self.base_offset + self.base_radius, \
               self.container.right - self.base_offset - self.base_radius

    def get_striker_y_position(self, player):
        """ Returns the position of the striker along y axis for the given player """
        return self.container.bottom - self.base_distance - self.base_radius if player == 0 \
            else self.container.top + self.base_distance + self.base_radius

    def get_striker_x_position(self):
        """ Returns the position of the striker along x axis for the any player (start position) """
        return self.container.centerx

    def get_striker_position(self, player):
        """ Returns the start position of the striker for the given player """
        return Vector2(self.get_striker_x_position(), self.get_striker_y_position(player))

    """ Function to display notification, draws at the bottom end"""

    def show_notification(self, win, message: str):
        font_size = self.frame_width // 3
        font = pygame.font.Font('freesansbold.ttf', font_size)
        text = font.render(message, True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = (self.board.right - self.frame_width - text_rect.width,
                            self.board.bottom - self.frame_width // 2)
        win.blit(text, text_rect)

    """ Function to draw the speed and angle indication of the striker """

    def draw_striker_arrow_pointer(self, win, striker, max_speed, draw_arrow=True):
        striker_center = striker.position
        if not draw_arrow:
            """ Draw a simple line, from striker along orientation of velocity """
            arrow_position = striker_center + striker.velocity * self.container.width / (3 * max_speed)
            pygame.draw.line(win, (0, 0, 0), (int(striker_center.x), int(striker_center.y)),
                             (int(arrow_position.x), int(arrow_position.y)))
        else:
            """ Draw a arrow """
            velocity_indicator = striker.velocity * self.container.width / (3 * max_speed)
            v_length = velocity_indicator.length()
            """ Added a length greater than 1 to prevent draw arc from throwing an exception """
            if v_length > 3:
                arrow_box = Rect(int(striker_center.x - v_length), int(striker_center.y - v_length),
                                 int(2 * v_length), int(2 * v_length))
                pygame.draw.arc(win, (255, 100, 0), arrow_box,
                                radians(velocity_indicator.angle_to(Vector2(1, 0)) - 30),
                                radians(velocity_indicator.angle_to(Vector2(1, 0)) + 30), 1)
                position_1 = striker_center + velocity_indicator * 1.1
                position_2 = striker_center + velocity_indicator * 0.2
                pygame.draw.line(win, (255, 100, 0), (int(position_1.x), int(position_1.y)),
                                 (int(position_2.x), int(position_2.y)))
