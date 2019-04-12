from coin import CarromMen, Queen, Striker
from pygame import Rect
from pygame import Vector2
import pygame
from math import radians, sqrt
from itertools import combinations
""" Striker must have at-least three and a half runs when struck with maximum force """


class Carrom:
    """ Defines a carrom board """
    """ Length of various components """
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
        """ Must be a squared """
        assert board.width == board.height
        self.board = board
        frame_width = int(board.width * Carrom.FRAME_LENGTH / Carrom.TOTAL_LENGTH)
        self.container = board.inflate(-2 * frame_width, -2 * frame_width)
        self.__init_board_params__()
        self.__init_pieces__()
        self.player_coins = [[], []]
        self.pocketed_coins = [[], []]
        self.foul_count = [0, 0]
        self.has_queen = [False, False]
        for coin in self.coins:
            self.player_coins[coin.get_player()].append(coin)
        self.pocketed_queen = False
        self.queen_on_hold = False
        self.continue_turn = False
        self.pocketed_striker = False
        self.current_pocketed = []
        self.player_turn = 0
        self.game_over = False
        self.winner = None
        self.reason = None

    def update(self, dt, decelerate, e):
        coins = self.player_coins[0] + self.player_coins[1]
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)

        for coin1, coin2 in combinations(coins, 2):
            if coin1.check_collision(coin2):
                coin1.collide(coin2, e)

        for coin in coins:
            coin.update(dt, decelerate)
            """ Now check if pocketed """
            for pocket_center in self.pocket_centers:
                if coin.position.distance_to(pocket_center) < self.pocket_radius - coin.radius:
                    """ If coin is inside the pocket, then pocketed """
                    if coin == self.striker:
                        self.pocketed_striker = True
                    elif coin == self.queen:
                        self.pocketed_queen = True
                    else:
                        self.current_pocketed.append(coin)
                        """ Move coins to pocketed coins for that player """
                        self.player_coins[coin.get_player()].remove(coin)
                        self.pocketed_coins[coin.get_player()].append(coin)

    def init_turn(self):
        self.current_pocketed = []
        self.pocketed_striker = False

    def update_turn(self, change: bool):
        """ Update foul for all players """
        for _ in range(self.foul_count[self.player_turn]):
            """ If any foul by the player """
            if self.pocketed_coins[self.player_turn]:
                """ If any coin was pocketed by the player, place it back """
                coin = self.pocketed_coins[self.player_turn].pop()
                self.player_coins[self.player_turn].append(coin)
                coin.reset()
                self.foul_count[self.player_turn] -= 1
            else:
                """ No coin to remove foul """
                break
        other_player = (self.player_turn + 1) % 2
        for _ in range(self.foul_count[other_player]):
            """ If any foul by the player """
            if self.pocketed_coins[other_player]:
                """ If any coin was pocketed by the player, place it back """
                coin = self.pocketed_coins[other_player].pop()
                self.player_coins[other_player].append(coin)
                coin.reset()
                self.foul_count[other_player] -= 1
            else:
                """ No coin to remove foul """
                break
        if not self.player_coins[self.player_turn]:
            print("No coins for the player")
            if not self.pocketed_queen:
                """ If queen was not pocketed, penalty occurs of two  """
                print("Queen not pocketed")
                self.foul_count[self.player_turn] += 2
                print("Call with updated penalty")
                self.update_turn(True)
                return
            else:
                """ Game over """
                print("Game over")
                self.winner = self.player_turn
                self.reason = "Hit all pawns"
                self.game_over = True
        if not self.player_coins[(self.player_turn + 1) % 2]:
            """ If all coins of other player were hit """
            if not self.pocketed_queen:
                print("Queen not hit but other player coins hit")
                """ Get the other players coin """
                other_player = (self.player_turn + 1) % 2
                coin = self.pocketed_coins[other_player].pop()
                self.player_coins[other_player].append(coin)
                coin.reset()
                print("Adding foul to current player for hitting other players coin")
                self.foul_count[self.player_turn] += 2
                """ Change the turn of the player """
                self.update_turn(True)
                return
            else:
                self.winner = (self.player_turn + 1) % 2
                self.reason = "Other player finished it for you"
                self.game_over = True
        self.current_pocketed = []
        # self.pocketed_striker = False
        if change:
            self.player_turn = (self.player_turn + 1) % 2

    def apply_rules(self):
        """ After all coins stopped moving, now check if turn needs to be updated or not """
        if self.pocketed_striker:
            """ If striker is pocketed, then whatever was pocketed this turn (player coins) goes 
            back along a foul """
            if self.pocketed_queen and not self.has_queen[0] and not self.has_queen[1]:
                """ If queen was pocketed, then place it back """
                self.queen_on_hold = False
                self.pocketed_queen = False
                self.queen.reset()
            for coin in self.current_pocketed:
                if coin.get_player() == self.player_turn:
                    """ If pocketed coin belongs to player, then place it back """
                    self.player_coins[coin.get_player()].append(coin)
                    self.pocketed_coins[coin.get_player()].remove(coin)
                    coin.reset()
            """ Add a foul """
            self.foul_count[self.player_turn] += 1
            self.update_turn(True)

        elif self.pocketed_queen and not self.has_queen[0] and not self.has_queen[1]:
            for coin in self.current_pocketed:
                if coin.get_player() == self.player_turn:
                    """ If also player coin was pocketed """
                    self.has_queen[self.player_turn] = True
                    self.queen_on_hold = False
                    self.update_turn(False)
                    break
            else:
                """ If no player coin was pocketed """
                if self.queen_on_hold:
                    """ If queen was on hold, then release it"""
                    self.queen_on_hold = False
                    self.pocketed_queen = False
                    self.queen.reset()
                    """ Change the turn """
                    self.update_turn(True)
                else:
                    """ if queen was pocketed currently only """
                    self.queen_on_hold = True
                    """ Don;t change turn """
                    self.update_turn(False)

        elif self.current_pocketed:
            """ If any pocket """
            for coin in self.current_pocketed:
                if coin.get_player() == self.player_turn:
                    """ Can keep turn """
                    self.update_turn(False)
                    break
            else:
                """ Change turn """
                self.update_turn(True)

        else:
            """ If nothing was pocketed, then change turn """
            self.update_turn(True)

    def check_moving(self):
        coins = self.player_coins[0] + self.player_coins[1]
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)
        if not coins:
            return False
        if not any(coin.check_moving() for coin in coins):
            return False
        return True

    def __init_pieces__(self, init_rotation=60):
        """ Initializes the carrom coins on the board """
        center = Vector2(self.container.centerx, self.container.centery)
        m = self.board.width / Carrom.TOTAL_LENGTH
        coin_radius = m * Carrom.COIN_RADIUS
        vec = Vector2(0, -1)
        vec.rotate_ip(init_rotation)
        vec.scale_to_length(coin_radius * 2)
        self.queen = Queen(coin_radius, Carrom.COIN_MASS, center, self.container)
        self.coins = []
        for i in range(6):
            self.coins.append(CarromMen(i % 2, coin_radius, Carrom.COIN_MASS, center + vec, self.container))
            vec.rotate_ip(60)

        vec.scale_to_length(coin_radius * 4)
        for i in range(6):
            self.coins.append(CarromMen(0, coin_radius, Carrom.COIN_MASS, center + vec, self.container))
            vec.rotate_ip(60)

        vec.scale_to_length(coin_radius * (2 * sqrt(3)))
        vec.rotate_ip(30)
        for i in range(6):
            self.coins.append(CarromMen(1, coin_radius, Carrom.COIN_MASS, center + vec, self.container))
            vec.rotate_ip(60)
        striker_radius = m * Carrom.STRIKER_RADIUS
        self.striker = Striker(striker_radius, Carrom.STRIKER_MASS, self.container)

    def draw_coins(self, win):
        coins = self.player_coins[0] + self.player_coins[1]
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)
        for coin in coins:
            coin.draw(win)
        """ Also draw pocketed coins """
        m = self.board.width / Carrom.TOTAL_LENGTH
        coin_radius = int(m * Carrom.COIN_RADIUS)
        i = 0
        for i, _ in enumerate(self.pocketed_coins[0]):
            x_offset = int(m * Carrom.FRAME_LENGTH + i * m * Carrom.COIN_RADIUS * 3)
            y_offset = int(self.board.bottom - m * 2 * Carrom.COIN_RADIUS)
            pygame.draw.circle(win, (255, 255, 255), (x_offset, y_offset), coin_radius)
        i += 1
        if self.pocketed_queen and self.has_queen[0]:
            x_offset = int(m * Carrom.FRAME_LENGTH + i * m * Carrom.COIN_RADIUS * 3)
            y_offset = int(self.board.bottom - m * 2 * Carrom.COIN_RADIUS)
            pygame.draw.circle(win, (255, 0, 0), (x_offset, y_offset), coin_radius)

        for i, _ in enumerate(self.pocketed_coins[1]):
            x_offset = int(m * Carrom.FRAME_LENGTH + i * m * Carrom.COIN_RADIUS * 3)
            y_offset = int(self.board.top + m * 2 * Carrom.COIN_RADIUS)
            pygame.draw.circle(win, (0, 0, 0), (x_offset, y_offset), coin_radius)
        i += 1
        if self.pocketed_queen and self.has_queen[1]:
            x_offset = int(m * Carrom.FRAME_LENGTH + i * m * Carrom.COIN_RADIUS * 3)
            y_offset = int(self.board.top + m * 2 * Carrom.COIN_RADIUS)
            pygame.draw.circle(win, (255, 0, 0), (x_offset, y_offset), coin_radius)

    def __init_board_params__(self):
        """ This function initializes board parameters which are necessary for drawing """
        """ pocket centers """
        m = self.board.width / Carrom.TOTAL_LENGTH
        self.pocket_radius = m * Carrom.POCKET_RADIUS
        self.pocket_centers = [
            Vector2(self.container.left + self.pocket_radius, self.container.top + self.pocket_radius),
            Vector2(self.container.right - self.pocket_radius, self.container.top + self.pocket_radius),
            Vector2(self.container.right - self.pocket_radius, self.container.bottom - self.pocket_radius),
            Vector2(self.container.left + self.pocket_radius, self.container.bottom - self.pocket_radius),
        ]

        """ base lines params """
        base_offset = m * Carrom.BASE_OFFSET
        base_distance = m * Carrom.BASE_DISTANCE
        base_height = m * Carrom.BASE_HEIGHT
        base_length = m * Carrom.BASE_LENGTH
        base_radius = m * Carrom.BASE_RADIUS
        self.striker_x_position_limits = (self.container.left + base_offset + base_radius,
                                          self.container.right - base_offset - base_radius)
        self.striker_y_position = [self.container.bottom - base_distance - base_radius,
                                   self.container.top + base_distance + base_radius]
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
        """ Base circle centers """
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
        arrow_start = self.pocket_radius * 2 + m * Carrom.ARROW_OFFSET / sqrt(2)
        arrow_end = arrow_start + m * Carrom.ARROW_LENGTH / sqrt(2)
        self.arrow_lines = [((int(self.container.left + arrow_start), int(self.container.top + arrow_start)),
                             (int(self.container.left + arrow_end), int(self.container.top + arrow_end))),
                            ((int(self.container.left + arrow_start), int(self.container.bottom - arrow_start)),
                             (int(self.container.left + arrow_end), int(self.container.bottom - arrow_end))),
                            ((int(self.container.right - arrow_start), int(self.container.bottom - arrow_start)),
                             (int(self.container.right - arrow_end), int(self.container.bottom - arrow_end))),
                            ((int(self.container.right - arrow_start), int(self.container.top + arrow_start)),
                             (int(self.container.right - arrow_end), int(self.container.top + arrow_end)))]
        arc_offset = int(arrow_end - m * Carrom.ARROW_RADIUS * (1 + 1 / sqrt(2)))
        arc_width = int(m * Carrom.ARROW_DIAMETER)
        """ Arrow Arcs"""
        self.arrow_arcs = [(Rect(self.container.left + arc_offset, self.container.top + arc_offset, arc_width,
                                 arc_width), radians(180), radians(90)),
                           (Rect(self.container.left + arc_offset, self.container.bottom - arc_offset, arc_width,
                                 -arc_width), radians(-90), radians(180)),
                           (Rect(self.container.right - arc_offset, self.container.bottom - arc_offset, -arc_width,
                                 -arc_width), radians(0), radians(-90)),
                           (Rect(self.container.right - arc_offset, self.container.top + arc_offset, -arc_width,
                                 arc_width), radians(90), radians(0))]

    def draw_board(self, win):
        """ This function is called to draw the carrom board and its components """
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
        m = self.board.width / Carrom.TOTAL_LENGTH
        base_radius = m * Carrom.BASE_RADIUS
        base_inner_radius = m * Carrom.BASE_INNER_RADIUS
        for base_circle_center in self.base_circle_centers:
            pygame.draw.circle(win, (100, 50, 50), base_circle_center, int(base_radius), 1)
            pygame.draw.circle(win, (100, 50, 50), base_circle_center, int(base_inner_radius))
        """ Draw the center circles """
        center_outer_radius = m * Carrom.CENTER_OUTER_RADIUS
        center_inner_radius = m * Carrom.CENTER_INNER_RADIUS
        pygame.draw.circle(win, (100, 50, 50), self.container.center, int(center_outer_radius), 2)
        pygame.draw.circle(win, (100, 50, 50), self.container.center, int(center_inner_radius))
        """ Draw the arrow lines """
        for arrow_line in self.arrow_lines:
            pygame.draw.line(win, (100, 50, 50), arrow_line[0], arrow_line[1])

        """ Draw the arrow arcs """
        for arrow_arc in self.arrow_arcs:
            arrow_arc[0].normalize()
            pygame.draw.arc(win, (100, 50, 50), arrow_arc[0], arrow_arc[1], arrow_arc[2], 2)


pygame.init()
width = 800
win = pygame.display.set_mode((width, width))
winRect = win.get_rect()
clock = pygame.time.Clock()
c = Carrom(winRect)
# c.player_turn = 1
c.striker.position.y = c.striker_y_position[c.player_turn]
c.striker.position.x = (c.striker_x_position_limits[0] + c.striker_x_position_limits[1])/2
max_speed = 40
speed = 0
angle = -90 if c.player_turn == 0 else 90
speed_vec = Vector2()
handle_keys = True
run = True

while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        """ If nothing is moving, then space may be pressed """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                print("Moving status:", c.check_moving())
                if not c.check_moving() and not c.game_over:
                    c.striker.velocity.from_polar((speed, angle))
                    print("Not moving")
                    handle_keys = False
    if c.game_over:
        font = pygame.font.Font('freesansbold.ttf', 40)
        winner = 'WHITE' if c.winner == 0 else 'BLACK'
        text = font.render('Game Over!! Winner:' + winner, True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = c.board.center
        win.blit(text, text_rect)
        pygame.display.update()
        continue

    if handle_keys:
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_a]:
            c.striker.position.x -= 4
        if pressed[pygame.K_d]:
            c.striker.position.x += 4
        if pressed[pygame.K_LEFT]:
            c.striker.position.x -= 1
        if pressed[pygame.K_RIGHT]:
            c.striker.position.x += 1
        if pressed[pygame.K_s]:
            speed -= 2
        if pressed[pygame.K_w]:
            speed += 2
        if pressed[pygame.K_DOWN]:
            speed -= 0.5
        if pressed[pygame.K_UP]:
            speed += 0.5
        if pressed[pygame.K_q]:
            if c.player_turn == 0:
                angle -= 2
            else:
                angle += 2
        if pressed[pygame.K_e]:
            if c.player_turn == 0:
                angle += 2
            else:
                angle -= 2
        if pressed[pygame.K_z]:
            if c.player_turn == 0:
                angle -= 0.4
            else:
                angle += 0.4
        if pressed[pygame.K_c]:
            if c.player_turn == 0:
                angle += 0.4
            else:
                angle -= 0.4

        c.striker.position.y = c.striker_y_position[c.player_turn]
        c.striker.position.x = max(c.striker_x_position_limits[0],
                                   min(c.striker.position.x, c.striker_x_position_limits[1]))
        if c.player_turn == 0:
            angle = min(0, max(angle, -180))
        else:
            angle = min(180, max(angle, 0))
        speed = min(max_speed, max(0, speed))

    c.draw_board(win)
    c.draw_coins(win)

    if handle_keys:
        speed_vec.from_polar((speed, angle))
        position_vec = speed_vec * 10 + c.striker.position
        # print(position_vec, 'Striker', striker.position)
        pygame.draw.line(win, (0, 0, 0), (int(c.striker.position.x), int(c.striker.position.y)),
                         (int(position_vec.x), int(position_vec.y)))
    pygame.display.update()
    if not handle_keys:
        for _ in range(10):
            c.update(0.1, 0.3, 0.9)
            if not c.check_moving():
                c.apply_rules()
                handle_keys = True
                if c.pocketed_striker:
                    print("Pocketed striker")
                c.striker.position.y = c.striker_y_position[0]
                c.striker.position.x = (c.striker_x_position_limits[0] + c.striker_x_position_limits[1]) / 2
                speed = 0
                angle = -90 if c.player_turn == 0 else 90
                speed_vec = Vector2()
                break
    if not c.check_moving():
        if c.pocketed_striker:
            c.striker.velocity = Vector2()
            c.pocketed_striker = False



pygame.quit()
