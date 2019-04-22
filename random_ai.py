from carrom import Carrom
from random import uniform
from copy import deepcopy
from pygame import Vector2


def carrom_score(player, carrom: Carrom):
    other_player = (player + 1) % 2
    score = len(carrom.pocketed_coins[player]) - 2 * len(carrom.pocketed_coins[other_player]) - 3 * carrom.foul_count[player]
    if carrom.has_queen[player]:
        score += 15
    elif carrom.queen_on_hold:
        score += 3
    return score


def ai(carrom: Carrom, max_angle, max_speed, decelerate, e, dt, permit_orientation=False, num_choices=10):
    """ Performs a random search """
    player, opponent = carrom.player_turn, (carrom.player_turn + 1) % 2
    y_position = carrom.board.get_striker_y_position(player)
    x_limits = carrom.board.get_striker_x_limits()
    max_score, striker_params = None, None
    # speed = max_speed
    for i in range(num_choices):
        angle_of_attack = uniform(- max_angle, max_angle)
        x_position = uniform(x_limits[0], x_limits[1])
        striker_position = Vector2(x_position, y_position)
        striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
        striker_speed = max_speed
        """ Also if carrom orientation can be changed """
        carrom_orientation = uniform(0, 120)
        copied_carrom = deepcopy(carrom)
        copied_carrom.striker.position = striker_position
        copied_carrom.striker.velocity.from_polar((striker_speed, striker_angle))
        if permit_orientation:
            """ If orientation can be set """
            copied_carrom.rotate_carrom_men(carrom_orientation)
        score = simulate_carrom(copied_carrom, dt, decelerate, e)
        if not max_score or score > max_score:
            max_score = score
            striker_params = (x_position, striker_angle, striker_speed, carrom_orientation)
    """ Local best has been computed.. Now run it with that """
    x_position, striker_angle, striker_speed, carrom_orientation = striker_params
    if permit_orientation:
        carrom.rotate_carrom_men(carrom_orientation)
    carrom.striker.position = Vector2(x_position, y_position)
    carrom.striker.velocity.from_polar((striker_speed, striker_angle))


def simulate_carrom(carrom_: Carrom, dt, decelerate, e):
    """ Simulate the carrom and return the performance score """
    player = carrom_.player_turn
    while carrom_.check_moving():
        carrom_.update(dt, decelerate, e)
    carrom_.apply_rules()
    return carrom_score(player, carrom_)



