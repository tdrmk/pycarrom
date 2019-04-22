from carrom import Carrom
from pygame import Rect
import pygame
from ai import ai
from random_ai import ai as random_ai
import argparse
from start_menu import start_window

player_choices = ['ai', 'random', 'human']
parser = argparse.ArgumentParser(description="PyCarrom is a two player carrom game played between humans or ai")
parser.add_argument('--player1', '-1', choices=player_choices, default='human', help="specify player type")
parser.add_argument('--player2', '-2', choices=player_choices, default='human', help="specify player type")
parser.add_argument('--width', '-w', type=int, default=700, help="carrom window width")
parser.add_argument("--max_angle", type=float, default=90, help="maximum striker angle")
parser.add_argument("--max_speed", type=float, default=40, help="maximum striker speed")
parser.add_argument("--dt", type=float, default=0.1, help="simulation interval")
parser.add_argument("--decelerate", type=float, default=0.3, help="deceleration due to friction")
parser.add_argument("--e", type=float, default=0.9, help="co-efficient of restitution for collisions")
parser.add_argument("--num_updates", type=int, default=10, help="number of updates before drawing to screen")
parser.add_argument("--num_random_choices", type=int, default=20, help="number of search points for random ai")
parser.add_argument("--no_start_menu", action="store_true", help="disable start menu")
parser.add_argument("--fps", type=int, default=60, help="frames per second")
args = parser.parse_args()

""" Update the internal variables from the parser """
""" Width of carrom board to create """
width = int(args.width)
""" Collision parameters """
dt = float(args.dt)
decelerate = float(args.decelerate)
e = float(args.e)
""" After how many simulations/updates to send the carrom data to clients """
num_updates = int(args.num_updates)

""" Limits on user inputs"""
max_angle = float(args.max_angle)
max_speed = float(args.max_speed)

fps = int(args.fps)

if args.no_start_menu:
    player1, player2 = args.player1, args.player2
else:
    player1, player2 = start_window(width, fps)

""" This is used in case of random ai"""
num_random_choices = int(args.num_random_choices)

print("Parameters are width:", width, "dt:", dt, "decelerate:", decelerate, "e:", e, "max_angle:", max_angle,
      "max_speed:", max_speed, "num_updates:", num_updates, "fps:", fps, "player1:", player1, "player2:", player2)

pygame.init()
win = pygame.display.set_mode((width, width))
pygame.display.set_caption("PyCarrom: WHITE(%s) vs BLACK(%s)" % (player1, player2))

carrom = Carrom(Rect(0, 0, width, width))
""" Orientation changes are only allowed for the first turn"""
permit_orientation = True
players = [player1, player2]

""" Have a clock to control display updates based on user input """
clock = pygame.time.Clock()


def handle_events():
    """ Handle the quit event """
    for event_ in pygame.event.get():
        if event_.type == pygame.QUIT:
            pygame.quit()
            quit()


def handle_user_input(win_, carrom_, permit_rotation=False):
    """ Take user input till user presses space, this function is used to get striker position,
    speed and orientation from the user """
    get_user_input = True

    """ The initial striker speed, striker angle, assuming striker is placed at center,
     coins orientation is used if permit rotations it set (only for initial player chance) """
    striker_speed = 0
    striker_angle = 0
    coins_orientation = 60  # Initial Orientation, used if permit_orientation is set

    """ Keep track of the limits of user input, ie, limit max position, speed, and orientation.
      Angle and speed limits are input parameters """
    x_limits = carrom_.board.get_striker_x_limits()

    while get_user_input:
        clock.tick(fps)
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
        striker_angle = min(max_angle, max(-max_angle, striker_angle))
        """ Setup the striker velocity based on current values set up by the user """
        carrom_.striker.velocity.from_polar(
            (striker_speed, -90-striker_angle if carrom_.player_turn == 0 else 90+striker_angle))

        if pressed[pygame.K_SPACE]:
            """ Don;t take any more user input, user wants to strike """
            get_user_input = False

        """ Update the striker position on the board """
        carrom_.draw(win_)
        carrom_.board.show_notification(win_, "WHITE'S TURN" if carrom.player_turn == 0 else "BLACK'S TURN")
        carrom_.board.draw_striker_arrow_pointer(win_, carrom_.striker, max_speed)
        pygame.display.update()


while not carrom.game_over:
    """ Initialize the striker position """
    carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)
    if players[carrom.player_turn] == "ai":
        """ Just refresh the board """
        carrom.draw(win)
        carrom.board.show_notification(win, "AI thinking")
        pygame.display.flip()
        handle_events()
        """ let the ai make the decision for the striker """
        ai(carrom, max_angle, max_speed, decelerate, e, dt)
        """ just indicate to the user, the ai's decision """
        carrom.draw(win)
        carrom.board.draw_striker_arrow_pointer(win, carrom.striker, max_speed)
        carrom.board.show_notification(win, "AI decided")
        pygame.display.flip()
        handle_events()
        """wait for some time """
        pygame.time.delay(100)
    elif players[carrom.player_turn] == "random":
        """ Just refresh the board """
        carrom.draw(win)
        carrom.board.show_notification(win, "Random AI thinking")
        pygame.display.flip()
        handle_events()
        """ let the random ai make the decision for the striker """
        random_ai(carrom, max_angle, max_speed, decelerate, e, dt, permit_orientation, num_random_choices)
        """ just indicate to the user, the random ai's decision """
        carrom.draw(win)
        carrom.board.draw_striker_arrow_pointer(win, carrom.striker, max_speed)
        carrom.board.show_notification(win, "Random AI decided")
        pygame.display.flip()
        handle_events()
        """wait for some time """
        pygame.time.delay(100)
    else:
        """ Human's turn"""
        handle_user_input(win, carrom, permit_rotation=permit_orientation)
        """ add some delay between human turns """
        pygame.time.delay(100)

    """ Only first time orientation changes are allowed """
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

    """ apply the rules and update fouls and other stuff """
    carrom.apply_rules()

""" Game Over draw the carrom for the final time """
carrom.draw(win)
carrom.board.show_notification(win, "GAME OVER..")
font = pygame.font.Font('freesansbold.ttf', carrom.board.frame_width)
winner = carrom.get_player(carrom.winner)
print("Game Over, won by", winner, players[carrom.winner])
""" Indicate the winner """
text = font.render("WINNER " + winner, True, (0, 0, 255))
text_rect = text.get_rect()
text_rect.center = carrom.board.board.center
win.blit(text, text_rect)
pygame.display.update()
"""Wait for user to quit """
while True:
    clock.tick(10)
    handle_events()


