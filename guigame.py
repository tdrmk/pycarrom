from carrom import Carrom
from pygame import Rect
import pygame

""" Width of carrom board to create """
width = 700
""" Collision parameters """
dt = 0.1
decelerate = 0.3
e = 0.9
""" After how many simulations/updates to send the carrom data to clients """
num_updates = 10

""" Limits on user inputs"""
max_angle = 180
max_speed = 100

""" Have a clock to control display updates based on user input """
clock = pygame.time.Clock()


def handle_user_input(win_, carrom_, permit_rotation=False):
    """ Take user input till user presses space """
    get_user_input = True

    """ The initial striker speed, striker angle, assuming striker is placed at center,
     coins orientation is used if permit rotations it set (only for initial player chance) """
    striker_speed = 0
    striker_angle = 90
    coins_orientation = 60  # Conditional (Initial Orientation)
    """ Keep track of the limits of user input """
    x_limits = carrom_.board.get_striker_x_limits()
    """ Angle and speed limits are input parameters """

    while get_user_input:
        clock.tick(60)
        """ Handle user events """
        for event_ in pygame.event.get():
            if event_.type == pygame.QUIT:
                """ If user requested to QUIT, then force quit """
                pygame.quit()
                quit()

        """ Obtain all pressed keys """
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_a] or pressed[pygame.K_LEFT]:
            """ Move the striker to the left """
            carrom_.striker.position.x -= 4 if not pressed[pygame.K_LSHIFT] else 0.5
        if pressed[pygame.K_d] or pressed[pygame.K_RIGHT]:
            """ Move the striker to the right """
            carrom_.striker.position.x += 4 if not pressed[pygame.K_LSHIFT] else 0.5

        if pressed[pygame.K_s] or pressed[pygame.K_DOWN]:
            """ Decrease the striker speed """
            striker_speed -= max_speed * 0.05 if not pressed[pygame.K_LSHIFT] else max_speed * 0.005
        if pressed[pygame.K_w] or pressed[pygame.K_UP]:
            """ Increase the striker speed """
            striker_speed += max_speed * 0.05 if not pressed[pygame.K_LSHIFT] else max_speed * 0.005

        if pressed[pygame.K_q]:
            """ Rotate the striker towards the left """
            striker_angle += max_angle * 0.05 if not pressed[pygame.K_LSHIFT] else max_angle * 0.005
        if pressed[pygame.K_e]:
            """ Rotate the striker towards the rigth """
            striker_angle -= max_angle * 0.05 if not pressed[pygame.K_LSHIFT] else max_angle * 0.005

        if pressed[pygame.K_r] and permit_rotation:
            """ Rotate the coins as per player requirements before starting the game """
            coins_orientation += 1 if not pressed[pygame.K_LSHIFT] else -1
            carrom_.rotate_carrom_men(coins_orientation)

        """ Make user positions, angle and speed are within permissible limits """
        carrom_.striker.position.x = min(x_limits[1], max(x_limits[0], carrom_.striker.position.x))
        striker_speed = min(max_speed, max(striker_speed, 0))
        striker_angle = min(90 + max_angle, max(90 - max_angle, striker_angle))
        """ Setup the striker velocity based on current values set up by the user """
        carrom_.striker.velocity.from_polar(
            (striker_speed, -striker_angle if carrom_.player_turn == 0 else striker_angle))

        if pressed[pygame.K_SPACE]:
            """ Don;t take any more user input, user wants to strike """
            get_user_input = False

        """ Update the striker position on the board """
        carrom_.draw(win_)
        carrom_.board.show_notification(win_, "WHITE'S TURN" if carrom.player_turn == 0 else "BLACK'S TURN")
        carrom_.board.draw_striker_arrow_pointer(win_, carrom_.striker, max_speed)
        pygame.display.flip()


pygame.init()
win = pygame.display.set_mode((width, width))
pygame.display.set_caption("PyCarrom")

carrom = Carrom(Rect(0, 0, width, width))
""" Orientation changes are only allowed for the first turn"""
permit_orientation = True
while not carrom.game_over:
    """ Initialize the striker position """
    carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)
    handle_user_input(win, carrom, permit_rotation=permit_orientation)
    permit_orientation = False
    i = 0
    while carrom.check_moving():
        """ If coins can move, update them and sent the carrom data back to the clients """
        carrom.update(dt, decelerate, e)
        if carrom.check_moving():
            """ Send data if moving """
            i += 1
            if i % num_updates == 0:
                clock.tick(60)
                carrom.draw(win)
                carrom.board.show_notification(win, "SIMULATING..")
                pygame.display.flip()
                """ Handle the events, else screen is not updated """
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        """ If user requested to QUIT, then force quit """
                        pygame.quit()
                        quit()

    carrom.apply_rules()
""" Game Over draw the carrom for the final time, and wait for user inputs """

carrom.draw(win)
carrom.board.show_notification(win, "GAME OVER..")
font = pygame.font.Font('freesansbold.ttf', carrom.board.frame_width)
winner = "WHITE" if carrom.winner == 0 else "BLACK"
text = font.render("WINNER " + winner, True, (0, 0, 255))
text_rect = text.get_rect()
text_rect.center = carrom.board.board.center
win.blit(text, text_rect)
pygame.display.flip()

""" Handle User Events """
while True:
    clock.tick(10)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            """ If user requested to QUIT, then force quit """
            pygame.quit()
            quit()


