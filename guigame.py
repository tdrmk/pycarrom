import pygame
from pygame import Vector2
from carrom import Carrom


class GameWithGUI:
    def __init__(self, width=700, height=700, fps=60, max_speed=40, max_angle=90, dt=0.1, decelerate=0.3, e=0.9,
                 num_updates=10):
        pygame.init()
        """ Initialize the gui """
        self.win = pygame.display.set_mode((width, height))
        pygame.display.set_caption("PyCarrom")
        self.win_rect = self.win.get_rect()
        self.clock = pygame.time.Clock()
        self.fps = fps

        """ Initialize the carrom """
        self.carrom = Carrom(self.win_rect)
        self.dt = dt
        self.max_speed = max_speed
        self.max_angle = max_angle
        self.decelerate = decelerate
        self.e = e
        self.num_updates = num_updates

    def display_game_over(self, player):
        """ Display the game winner message text on the center of the screen """
        font = pygame.font.Font('freesansbold.ttf', self.carrom.board.board.width // 20)
        winner = 'WHITE' if player == 0 else 'BLACK'
        text = font.render('Game Over!! Winner:' + winner, True, (0, 0, 0))
        text_rect = text.get_rect()
        text_rect.center = self.carrom.board.container.center
        self.win.blit(text, text_rect)

    def game_loop(self):
        run = True
        """ Flag to indicate whether game was started or not, this is used to indicate 
        whether player can adjust the orientation of coins or not """
        game_started = False
        coins_orientation = 60
        """ Flag to indicate whether to handle user input (key presses) or not """
        handle_user_input = True
        """ Striker parameters """
        carrom = self.carrom
        striker_speed = 0
        striker_angle = 90
        """ Vector for modelling speed """
        speed_vector = Vector2()
        """ Initialize the striker position """
        carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)

        while run:
            self.clock.tick(self.fps)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if handle_user_input and not carrom.game_over:
                            """ If space bar is pressed, and if nothing is moving, then strike """
                            carrom.striker.velocity.from_polar((striker_speed,
                                -striker_angle if carrom.player_turn == 0 else striker_angle))
                            """ Don't handle user input """
                            game_started = True
                            handle_user_input = False
            if carrom.game_over:
                """ If game is over then don't handle any user inputs """
                self.display_game_over(carrom.winner)
                pygame.display.update()
                continue
            if handle_user_input:
                """ Pressing shift key with control keys causes a fine grainer control """
                pressed = pygame.key.get_pressed()
                if pressed[pygame.K_a] or pressed[pygame.K_LEFT]:
                    """ Move the striker to the left """
                    carrom.striker.position.x -= 4 if not pressed[pygame.K_LSHIFT] else 0.5
                if pressed[pygame.K_d] or pressed[pygame.K_RIGHT]:
                    """ Move the striker to the right """
                    carrom.striker.position.x += 4 if not pressed[pygame.K_LSHIFT] else 0.5

                if pressed[pygame.K_s] or pressed[pygame.K_DOWN]:
                    """ Decrease the striker speed """
                    striker_speed -= 2 if not pressed[pygame.K_LSHIFT] else 0.25
                if pressed[pygame.K_w] or pressed[pygame.K_UP]:
                    """ Increase the striker speed """
                    striker_speed += 2 if not pressed[pygame.K_LSHIFT] else 0.25

                if pressed[pygame.K_q]:
                    """ Rotate the striker towards the left """
                    striker_angle += 2 if not pressed[pygame.K_LSHIFT] else 0.25
                if pressed[pygame.K_e]:
                    """ Rotate the striker towards the rigth """
                    striker_angle -= 2 if not pressed[pygame.K_LSHIFT] else 0.25

                if pressed[pygame.K_r] and not game_started:
                    """ Rotate the coins as per player requirements before starting the game """
                    coins_orientation += 1 if not pressed[pygame.K_LSHIFT] else -1
                    carrom.rotate_carrom_men(coins_orientation)

                """ Now apply the bounds on the position and angle """
                x_limits = carrom.board.get_striker_x_limits()
                carrom.striker.position.x = min(x_limits[1], max(x_limits[0], carrom.striker.position.x))
                striker_speed = min(self.max_speed, max(striker_speed, 0))
                striker_angle = min(90 + self.max_angle, max(90 - self.max_angle, striker_angle))

            if not handle_user_input:
                """ Handle the simulation aspects """
                for _ in range(self.num_updates):
                    carrom.update(self.dt, self.decelerate, self.e)
                    if not carrom.check_moving():
                        """ If coins not moving, the apply the rules and update turn accordingly """
                        carrom.apply_rules()
                        """ Reset the striker parameters for the new turn """
                        striker_speed = 0
                        striker_angle = 90
                        carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)
                        """ Handle user input """
                        handle_user_input = True
                        break
            carrom.draw(self.win)
            if handle_user_input:
                """ Draw the line to help the player indicate the direction in which coin will go on strike """
                speed_vector.from_polar((striker_speed, -striker_angle if carrom.player_turn == 0 else striker_angle))
                position_vector = carrom.striker.position + speed_vector * 5
                pygame.draw.line(self.win, (0, 0, 0), (int(carrom.striker.position.x), int(carrom.striker.position.y)),
                                 (int(position_vector.x), int(position_vector.y)))
            pygame.display.update()
        pygame.quit()


if __name__ == '__main__':
    game = GameWithGUI(max_speed=100, max_angle=120)
    game.game_loop()
