from carrom import Carrom
from copy import deepcopy
from coin import Queen, Coin, CarromMen
from random import uniform
from pygame import Vector2
from math import sin, radians, sqrt, cos, tan
import pygame


def carrom_score(player, carrom: Carrom):
    other_player = (player + 1) % 2
    score = len(carrom.pocketed_coins[player]) - len(carrom.pocketed_coins[other_player]) - carrom.foul_count[player]
    if carrom.has_queen[player]:
        score += 5
    elif carrom.queen_on_hold:
        score += 1
    return score


def carrom_ai(carrom: Carrom, dt, decelerate, e, max_speed, max_angle):
    """ Takes a carrom board, returns a striker position, velocity and orientation """
    x_limits = carrom.board.get_striker_x_limits()
    player = carrom.player_turn
    steps = int((x_limits[1] - x_limits[0]) / 5)
    best_score, best_striker_params = None, None
    speed = max_speed
    for angle in range(90 - max_angle, 90 + max_angle + 1, 25):
        for x_position in range(int(x_limits[0]), int(x_limits[1] + 10), steps):
            copied_carrom = deepcopy(carrom)
            copied_carrom.striker.position.x = x_position
            copied_carrom.striker.velocity.from_polar((speed, -angle if copied_carrom.player_turn == 0 else angle))
            while copied_carrom.check_moving():
                """ Simulate the carrom """
                copied_carrom.update(dt, decelerate, e)
            copied_carrom.apply_rules()
            score = carrom_score(player, copied_carrom)
            if not best_score:
                best_score = score
                best_striker_params = (x_position, speed, angle)
            elif score > best_score:
                best_score = score
                best_striker_params = (x_position, speed, angle)
    x_position, speed, angle = best_striker_params
    carrom.striker.position.x = x_position
    carrom.striker.velocity.from_polar((speed, -angle if carrom.player_turn == 0 else angle))
    return best_striker_params


def random_ai(carrom: Carrom, dt, decelerate, e, max_speed, max_angle, num_choices, permit_orientation=False):
    x_limits = carrom.board.get_striker_x_limits()
    player = carrom.player_turn
    best_score, best_striker_params = None, None
    # speed = max_speed
    for i in range(num_choices):
        angle = uniform(90 - max_angle, 90 + max_angle)
        x_position = uniform(int(x_limits[0]), int(x_limits[1]))
        rotation = uniform(0, 120)
        speed = max_speed  # uniform(max_speed/2, max_speed)
        copied_carrom = deepcopy(carrom)
        copied_carrom.striker.position.x = x_position
        if permit_orientation:
            copied_carrom.rotate_carrom_men(rotation)
        copied_carrom.striker.velocity.from_polar((speed, -angle if copied_carrom.player_turn == 0 else angle))
        while copied_carrom.check_moving():
            """ Simulate the carrom """
            copied_carrom.update(dt, decelerate, e)
        copied_carrom.apply_rules()
        score = carrom_score(player, copied_carrom)
        if not best_score:
            best_score = score
            best_striker_params = (x_position, speed, angle, rotation)
        elif score > best_score:
            best_score = score
            best_striker_params = (x_position, speed, angle, rotation)
    x_position, speed, angle, rotation = best_striker_params

    # something = new_ai(carrom, dt, decelerate, e, max_speed, max_angle)
    # if something:
    #     print("Chosing For AI", something)
    #     speed, x_position, angle = something

    if permit_orientation:
        carrom.rotate_carrom_men(rotation)
    carrom.striker.position.x = x_position
    carrom.striker.velocity.from_polar((speed, -angle if carrom.player_turn == 0 else angle))
    yet_another_ai(carrom, max_angle, decelerate, e, dt)


def check_along_path(start: Vector2, end: Vector2, distance, coins, round_start=False, round_end=False):
    """ This function checks if any of the coins lies within the given distance, of the line joining
    the given two vectors, representing the end points """
    for coin in coins:
        section = (coin.position - start).dot(end - start) / start.distance_squared_to(end)
        """ Whether to round or not """
        section = section if not round_start else max(0, section)
        section = section if not round_end else min(1, section)
        if 0 <= section <= 1:
            projection = start.lerp(end, section)
            if projection.distance_to(coin.position) <= distance:
                """ Coin lies within the distance of the vector """
                return True
    return False


def along_path(vec1: Vector2, vec2, distance_margin, coins):
    for coin in coins:
        """ Project the vector joining coin position and vec1 along vector joining vec2 and vec1 """
        section = (coin.position - vec1).dot(vec2 - vec1) / vec1.distance_squared_to(vec2)
        # section = min(max(section, 0), 1)
        if 0 <= section <= 1:
            """ If coin lies in between the vectors, not check if lies with the margin """
            projection = vec1.lerp(vec2, section)
            if projection.distance_to(coin.position) <= distance_margin:
                """ Coin lies within the margin of the line joining vec1 and vec2 """
                # print("ALONG PATH:", coin.position, projection, distance_margin, projection.distance_to(coin.position))
                return True
    return False


def direct_striker_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2,
                         pocket_center: Vector2, decelerate, e):
    board = carrom.board
    """ These ensure that some additional velocity exists """
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    distance_striker_coin = striker_position.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / ((1 + e) * board.STRIKER_MASS)
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def cut_striker_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, expected_position: Vector2,
                      force_angle, pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    """ Added a little more to be on the safer side """
    distance_striker_coin = striker_position.distance_to(expected_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(force_angle)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed * 1.1


def rebound_striker_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2,
                          expected_position: Vector2, rebound_position: Vector2, force_angle, pocket_center: Vector2,
                          decelerate, e, dt):
    board = carrom.board
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    """ Added a little more to be on the safer side """
    distance_striker_coin = striker_position.distance_to(rebound_position) + \
                            rebound_position.distance_to(expected_position)

    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(force_angle)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    t = (striker_speed - col_striker_speed) / decelerate
    """ Decrease time to the nearest multiple of dt """
    print("t:", t, "dt:", dt, "distance:", distance_striker_coin, " SPEED:", striker_speed, "FIN:", col_striker_speed)
    # t = (t * 0.9) - ((t * 0.9) % dt)
    # striker_speed = (distance_striker_coin + decelerate * t ** 2 / 2) / t
    return striker_speed


def direct_rebound_shot(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, rebound_position: Vector2,
                        angle_of_attack, pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_striker_coin = striker_position.distance_to(coin_position)
    distance_coin_pocket = pocket_center.distance_to(rebound_position) + rebound_position.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(angle_of_attack)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def indirect_rebound_shot(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, rebound_position: Vector2,
                        angle_of_attack, pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_striker_coin = striker_position.distance_to(rebound_position) + rebound_position.distance_to(coin_position)
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(angle_of_attack)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def rebound_possible(carrom: Carrom, prev_rebound: Vector2, striker_direction: Vector2, board_coins):
    """ reflected striker direction """
    player, opponent = carrom.player_turn, (carrom.player_turn + 1) % 2
    container, board = carrom.board.container, carrom.board
    striker_y, x_limits = board.get_striker_x_limits(), board.get_striker_y_position(player)
    if -90 < Vector2(-1, 0).angle_to(striker_direction) < 90:
        rebound_x = container.right - board.striker_radius
        rebound_y = prev_rebound.y + (rebound_x - prev_rebound.x) * tan(radians(Vector2(-1, 0).angle_to(striker_direction)))
        rebound = Vector2(rebound_x, rebound_y)
        striker_direction = -striker_direction.reflect(Vector2(-1, 0))


def direct_strike(carrom: Carrom, board_coins, playable_coins):
    player, opponent = carrom.player_turn, (carrom.player_turn + 1) % 2
    container, board = carrom.board.container, carrom.board
    striker_y, x_limits = board.get_striker_x_limits(), board.get_striker_y_position(player)
    for index, center in enumerate(carrom.board.pocket_centers):
        for coin in playable_coins:
            if not along_path(coin.position, center, 2 * carrom.board.coin_radius,
                              [coin_ for coin_ in board_coins if coin_ != coin]):
                pocket_direction = center - coin.position
                if pocket_direction.x == 0 or pocket_direction.y == 0 or pocket_direction.x == pocket_direction.y:
                    continue
                if -90 < Vector2(-1, 0).angle_to(pocket_direction) < 90:
                    """ Right side of the frame, only rebound can occur """
                    rebound_x = container.right - board.striker_radius
                    scale_factor = (center.x - rebound_x) / (center.x - coin.position.x)
                    rebound = center + (coin.position - center) * scale_factor
                    if container.top <= rebound.y <= container.bottom:
                        """ Possible rebound """
                        striker_direction = -pocket_direction.reflect(Vector2(-1, 0))

                if -90 < Vector2(1, 0).angle_to(pocket_direction) < 90:
                    """ Left side of the frame, only rebound can occur """
                    rebound_x = container.left + board.striker_radius
                    scale_factor = (center.x - rebound_x) / (center.x - coin.position.x)
                    rebound = center + (coin.position - center) * scale_factor
                    if container.top <= rebound.y <= container.bottom:
                        """ Possible rebound """
                        striker_direction = -pocket_direction.reflect(Vector2(1, 0))

                if -90 < Vector2(0, 1).angle_to(pocket_direction) < 90:
                    """ Top Side of the frame """
                    rebound_y = container.top + board.striker_radius
                    scale_factor = (center.y - rebound_y) / (center.y - coin.position.y)
                    rebound = center + (coin.position - center) * scale_factor
                    if container.left <= rebound.x <= container.right:
                        """ Possible rebound """
                        striker_direction = -pocket_direction.reflect(Vector2(0, 1))

                if -90 < Vector2(0, -1).angle_to(pocket_direction) < 90:
                    """ Bottom Side of the frame """
                    rebound_y = container.bottom - board.striker_radius
                    scale_factor = (center.y - rebound_y) / (center.y - coin.position.y)
                    rebound = center + (coin.position - center) * scale_factor
                    if container.left <= rebound.x <= container.right:
                        """ Possible rebound """
                        striker_direction = -pocket_direction.reflect(Vector2(0, -1))


def yet_another_ai(carrom: Carrom, max_angle, decelerate, e, dt):
    player, opponent = carrom.player_turn, (carrom.player_turn + 1) % 2
    """ Now find some strike-able coin """
    direction_vec = Vector2(0, -1) if player == 0 else Vector2(0, 1)
    board_coins = carrom.player_coins[0] + carrom.player_coins[1]
    if not carrom.pocketed_queen: board_coins.append(carrom.queen)
    # striker positions
    x_limits = carrom.board.get_striker_x_limits()
    y_position = carrom.board.get_striker_y_position(player)
    coin_radius, striker_radius = carrom.board.coin_radius, carrom.board.striker_radius
    if not carrom.pocketed_queen and len(carrom.player_coins[player]) == 1:
        """ Modify playable coins if only queen and some other coin remains,
         then don't try pocketing the coin """
        playable_coins = [carrom.queen]
    else:
        playable_coins = carrom.player_coins[player].copy()
        if not carrom.pocketed_queen: playable_coins.insert(0, carrom.queen)
    for index, center in enumerate(carrom.board.pocket_centers):
        """ Later Update playable coins, to those that have no coin coin between it and pocket """
        for coin in playable_coins:
            if not along_path(coin.position, center, 2 * carrom.board.coin_radius,
                              [coin_ for coin_ in board_coins if coin_ != coin]):
                """ Potentially strike-able coin, as nothing along the path to the destination """
                """ Now consider, direct strike """
                rel_vec = coin.position - center
                if center.y == coin.position.y:
                    """ Coin in line along y-axis then not hittable directly"""
                    continue
                """ Find the factor by which striker is away from the coin in comparison to the center """
                scale_factor = (center.y - y_position) / (center.y - coin.position.y)
                striker_position = center + (coin.position - center) * scale_factor
                # striker_position = Vector2((y_position - center.y) * rel_vec.x / rel_vec.y + center.x, y_position)
                """ Find the angle at which the striker must strike """
                angle_of_attack = (center - striker_position).angle_to(direction_vec)
                """ x position must be within limits, angle of attack within limits and
                striker must not be between coin and pocket """
                if (x_limits[0] <= striker_position.x <= x_limits[1]) and abs(angle_of_attack) <= max_angle \
                        and scale_factor > 1:
                    """ Striker can directly hit the coin, now check if any thing in-between them """
                    if not along_path(striker_position, coin.position,
                                      carrom.board.coin_radius + carrom.board.striker_radius,
                                      [coin_ for coin_ in board_coins if coin_ != coin]):
                        """ Direct strike possible, """
                        print(carrom.current_player(), "Angle of attack",
                              angle_of_attack, "Striker Position:", striker_position, "Coin:", coin.position,
                              "Pocket:", center, "Rel Vec:", rel_vec, "Scale factor:", scale_factor)
                        # coin.color = (0, 255, 0)
                        carrom.striker.position = striker_position
                        striker_speed = direct_striker_speed(carrom, striker_position, coin.position, center,
                                                             decelerate, e)
                        striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                        carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                        return

    """ Rebounds """
    board, container = carrom.board, carrom.board.container
    for index, center in enumerate(carrom.board.pocket_centers):
        """ Later Update playable coins, to those that have no coin coin between it and pocket """
        for coin in playable_coins:
            if not along_path(coin.position, center, 2 * carrom.board.coin_radius,
                              [coin_ for coin_ in board_coins if coin_ != coin]):
                """ Potentially strike-able coin, as nothing along the path to the destination """
                rel_vec = coin.position - center
                if rel_vec.x == 0 or rel_vec.y == 0 or rel_vec.x == rel_vec.y:
                    """ No direct rebound shot possible """
                    continue
                rebound_y = board.diagonal_pocket_opposite[index][1]
                normal_vec = board.normal_vectors[index][1]
                # rebound_y = container.top + striker_radius if player == 0 else container.bottom - striker_radius
                # normal_vec = Vector2(0, 1) if player == 0 else Vector2(0, -1)
                scale_factor = (center.y - rebound_y) / (center.y - coin.position.y)
                rebound_position = center + (coin.position - center) * scale_factor
                angle_of_attack = (center - rebound_position).angle_to(normal_vec)
                if container.left <= rebound_position.x <= container.right\
                        and abs(angle_of_attack) <= max_angle and scale_factor > 1:
                    print("Trying to hit rebound...")
                    if not along_path(rebound_position, coin.position,
                                      carrom.board.coin_radius + carrom.board.striker_radius,
                                      [coin_ for coin_ in board_coins if coin_ != coin]):
                        """ Nothing blocking it """
                        scale_factor = (rebound_position.y - y_position)/(rebound_position.y - center.y)
                        striker_position = rebound_position - (center - rebound_position).reflect(normal_vec) *scale_factor
                        print("Center:", center, "Rebound Position:", rebound_position, "Dif:",(center - rebound_position),
                              "Rotation:",  (center - rebound_position).reflect(normal_vec), "Scale:", scale_factor)
                        print("Striker Positions:", striker_position, "Limits:", x_limits, y_position)
                        if x_limits[0] <= striker_position.x <= x_limits[1]:
                            angle_of_attack = (rebound_position - striker_position).angle_to(direction_vec)
                            if  not along_path(rebound_position, striker_position,
                                      carrom.board.coin_radius + carrom.board.striker_radius, board_coins) and \
                                    abs(angle_of_attack) <= max_angle:
                                print("REBOUND INDIRECT")
                                carrom.striker.position = striker_position
                                striker_speed = indirect_rebound_shot(carrom, striker_position, coin.position, rebound_position,
                                            angle_of_attack, center, decelerate, e)
                                # coin.color = (0, 0, 255)
                                striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                                carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                                return
                rebound_x = board.diagonal_pocket_opposite[index][0]
                normal_vec = board.normal_vectors[index][0]
                scale_factor = (center.x - rebound_x) / (center.x - coin.position.x)
                rebound_position = center + (coin.position - center) * scale_factor
                angle_of_attack = (center - rebound_position).angle_to(normal_vec)
                if container.top <= rebound_position.y <= container.bottom \
                        and abs(angle_of_attack) <= max_angle and scale_factor > 1:
                    print("Trying to hit rebound...")
                    if not along_path(rebound_position, coin.position,
                                      carrom.board.coin_radius + carrom.board.striker_radius,
                                      [coin_ for coin_ in board_coins if coin_ != coin]):
                        """ Nothing blocking it """
                        scale_factor = (rebound_position.y - y_position) / (rebound_position.y - center.y)
                        striker_position = rebound_position + (center - rebound_position).reflect(
                            normal_vec) * scale_factor
                        print("Center:", center, "Rebound Position:", rebound_position, "Dif:",
                              (center - rebound_position),
                              "Rotation:", (center - rebound_position).reflect(normal_vec), "Scale:", scale_factor)
                        print("Striker Positions:", striker_position, "Limits:", x_limits, y_position)
                        if x_limits[0] <= striker_position.x <= x_limits[1]:
                            angle_of_attack = (rebound_position - striker_position).angle_to(direction_vec)
                            if not along_path(rebound_position, striker_position,
                                              carrom.board.coin_radius + carrom.board.striker_radius, board_coins)\
                                    and  abs(angle_of_attack) <= max_angle:
                                print("REBOUND INDIRECT")
                                carrom.striker.position = striker_position
                                striker_speed = indirect_rebound_shot(carrom, striker_position, coin.position,
                                                                      rebound_position,
                                                                      angle_of_attack, center, decelerate, e)
                                # coin.color = (255, 255, 0)
                                striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                                carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                                return
    for index, center in enumerate(carrom.board.pocket_centers):
        """ If nothing works out, try hitting it from the side """
        for coin in playable_coins:
            # if (center.y <= coin.position.y <= y_position) or (center.y >= coin.position.y >= y_position):
            #     """ If coin is in-between """
            expected_position = center + (coin.position - center).normalize() * \
                                (center.distance_to(coin.position) + striker_radius + coin_radius)
            if not along_path(coin.position, center, 2 * carrom.board.coin_radius,
                              [coin_ for coin_ in board_coins if coin_ != coin]):
                # print(carrom.current_player(), "Nothing between coin and center")
                """ Potentially strike-able coin, as nothing along the path to the destination """
                for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
                    striker_position = Vector2(striker_x, y_position)
                    force_angle = (center - coin.position).angle_to(expected_position - striker_position) % 360
                    force_angle = force_angle if force_angle <= 180 else force_angle - 360
                    angle_of_attack = (expected_position - striker_position).angle_to(direction_vec)
                    if abs(force_angle) <= 60 and abs(angle_of_attack) <= max_angle:
                        # print("FORCE ANGLE:", striker_x, force_angle, "POCKET:", center, "COIN:", coin.position,
                        #       "EXPECTED:", expected_position, "STRIKER:", striker_position)
                        """ Hittable if nothing in-between """
                        if not along_path(striker_position, expected_position, striker_radius + coin_radius,
                                          [coin_ for coin_ in board_coins if coin_ != coin]) and \
                                not along_path(expected_position, coin.position, striker_radius + coin_radius,
                                          [coin_ for coin_ in board_coins if coin_ != coin]):
                            striker_speed = cut_striker_speed(carrom, striker_position, coin.position,
                                                              expected_position, force_angle,
                                                              center, decelerate, e)
                            # coin.color = (0, 255, 0)
                            carrom.striker.position = striker_position
                            striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                            carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                            print("CUT SHOT:", "FORCE ANGLE:", striker_x, force_angle, "POCKET:", center, "COIN:",
                                  coin.position,
                                  "EXPECTED:", expected_position, "STRIKER:", striker_position)
                            return
    for center in carrom.board.pocket_centers:
        for coin in playable_coins:
            rebounds = []
            rebound_y = carrom.board.container.top + carrom.board.coin_radius
            rebound_x = center.x + (coin.position.x - center.x) * (center.y - rebound_y) / \
                        (center.y + coin.position.y - 2 * rebound_y)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_y = carrom.board.container.bottom - carrom.board.coin_radius
            rebound_x = center.x + (coin.position.x - center.x) * (center.y - rebound_y) / \
                        (center.y + coin.position.y - 2 * rebound_y)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_x = carrom.board.container.left + carrom.board.coin_radius
            rebound_y = center.y + (coin.position.y - center.y) * (center.x - rebound_x) / \
                        (center.x + coin.position.x - 2 * rebound_x)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_x = carrom.board.container.right - carrom.board.coin_radius
            rebound_y = center.y + (coin.position.y - center.y) * (center.x - rebound_x) / \
                        (center.x + coin.position.x - 2 * rebound_x)
            rebounds.append(Vector2(rebound_x, rebound_y))
            for rebound in rebounds:
                angle_of_attack = (rebound - coin.position).angle_to(direction_vec)
                scale_factor = (rebound.y - y_position) / (rebound.y - coin.position.y)
                striker_position = rebound + (coin.position - rebound) * scale_factor
                if (x_limits[0] <= striker_position.x <= x_limits[1]) and abs(angle_of_attack) <= max_angle \
                        and scale_factor > 1:
                    """ Striker can directly hit the coin, now check if any thing in-between them """
                    if not along_path(striker_position, coin.position, striker_radius + coin_radius,
                                      [coin_ for coin_ in board_coins if coin_ != coin]) and \
                            not along_path(coin.position, rebound, coin_radius + coin_radius,
                                           [coin_ for coin_ in board_coins if coin_ != coin]) and \
                            not along_path(rebound, center, coin_radius + coin_radius, board_coins):
                        # coin.color = (0, 255, 0)
                        striker_speed = direct_rebound_shot(carrom, striker_position, coin.position, rebound,
                                                            angle_of_attack, center, decelerate, e)
                        carrom.striker.position = striker_position
                        striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                        carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                        print("DIRECT REBOUND SHOT!!")
                        return

    # for index, center in enumerate(carrom.board.pocket_centers):
    #     """ If nothing works out, try hitting it from the side """
    #     for coin in playable_coins:
    #         """ Try rebounding type 1, striker hits the board and re-bounds to hit the coin """
    #         expected_position = center + (coin.position - center).normalize() * \
    #                             (center.distance_to(coin.position) + striker_radius + coin_radius)
    #         rebound_y = carrom.board.container.top + striker_radius if player == 0 \
    #             else carrom.board.container.bottom - striker_radius
    #         # rebound_y = carrom.board.board.top if player == 0 else carrom.board.board.bottom
    #         if not along_path(coin.position, center, 2 * carrom.board.coin_radius,
    #                           [coin_ for coin_ in board_coins if coin_ != coin]):
    #             """ Try a rebound cut shot """
    #             for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
    #                 striker_position = Vector2(striker_x, y_position)
    #                 y1, y2 = expected_position.y - rebound_y, y_position - rebound_y
    #                 rebound_x = expected_position.x + (striker_x - coin.position.x) * y1 / (y1 + y2)
    #                 rebound_position = Vector2(rebound_x, rebound_y)
    #                 angle_of_attack = (rebound_position - striker_position).angle_to(direction_vec)
    #                 force_angle = (center - coin.position).angle_to(expected_position - rebound_position) % 360
    #                 force_angle = force_angle if force_angle <= 180 else force_angle - 360
    #                 if abs(force_angle) <= 80 and abs(angle_of_attack) <= max_angle:
    #                     if not along_path(striker_position, rebound_position, striker_radius + coin_radius,
    #                                       board_coins) and \
    #                             not along_path(rebound_position, expected_position, striker_radius + coin_radius,
    #                                            [coin_ for coin_ in board_coins if coin_ != coin]):
    #                         """ If no collision both ways """
    #                         striker_speed = rebound_striker_speed(carrom, striker_position, coin.position,
    #                                                               expected_position, rebound_position, force_angle,
    #                                                               center, decelerate, e, dt)
    #                         carrom.striker.position = striker_position
    #                         striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
    #                         carrom.striker.velocity.from_polar((striker_speed, striker_angle))
    #                         coin.color = (0, 255, 255)
    #                         print("REBOUND SHOT", "STRIKER:", striker_position, 40, "COIN:",
    #                               coin.position, "ANGLE OF ATTACK:", angle_of_attack, "FORCE:", force_angle,
    #                               "REBOUND:", rebound_position)
    #                         return

    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position = Vector2(striker_x, y_position)
            if not along_path(coin.position, striker_position, carrom.board.striker_radius + carrom.board.coin_radius,
                              [coin_ for coin_ in board_coins if coin_ != coin]):
                """ Potentially strike-able coin, as nothing along the path to the destination """
                angle_of_attack = (coin.position - striker_position).angle_to(direction_vec)
                if abs(angle_of_attack) <= max_angle:
                    """ Hittable if nothing in-between """
                    carrom.striker.position = striker_position
                    striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                    carrom.striker.velocity.from_polar((40, striker_angle))
                    print("Simply hitting inline coin")
                    return

    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position = Vector2(striker_x, y_position)
            rebounds = []
            rebound_y = carrom.board.container.top + carrom.board.coin_radius
            rebound_x = coin.position.x + (striker_position.x - coin.position.x) * (coin.position.y - rebound_y) / \
                        (coin.position.y + striker_position.y - 2 * rebound_y)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_y = carrom.board.container.bottom - carrom.board.coin_radius
            rebound_x = coin.position.x + (striker_position.x - coin.position.x) * (coin.position.y - rebound_y) / \
                        (coin.position.y + striker_position.y - 2 * rebound_y)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_x = carrom.board.container.left + carrom.board.coin_radius
            rebound_y = coin.position.y + (striker_position.y - coin.position.y) * (coin.position.x - rebound_x) / \
                        (coin.position.x + striker_position.x - 2 * rebound_x)
            rebounds.append(Vector2(rebound_x, rebound_y))
            rebound_x = carrom.board.container.right - carrom.board.coin_radius
            rebound_y = coin.position.y + (striker_position.y - coin.position.y) * (coin.position.x - rebound_x) / \
                        (coin.position.x + striker_position.x - 2 * rebound_x)
            rebounds.append(Vector2(rebound_x, rebound_y))
            for rebound in rebounds:
                angle_of_attack = (rebound - striker_position).angle_to(direction_vec)
                if abs(angle_of_attack) <= max_angle:
                    if not along_path(striker_position, rebound, striker_radius + coin_radius,
                                      board_coins) and \
                            not along_path(coin.position, rebound, striker_radius + coin_radius,
                                           [coin_ for coin_ in board_coins if coin_ != coin]):
                        carrom.striker.position = striker_position
                        striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                        carrom.striker.velocity.from_polar((40, striker_angle))
                        print("Simply hitting rebound coin")
                        return




def new_ai(carrom: Carrom, dt, decelerate, e, max_speed, max_angle):
    player = carrom.player_turn
    other_player = (player + 1) % 2
    x_limits = carrom.board.get_striker_x_limits()
    y_position = carrom.board.get_striker_y_position(player)
    pocket_centers = carrom.board.pocket_centers
    if player == 0:
        centers = pocket_centers[0:2]
    else:
        centers = pocket_centers[2:]
    for center in centers:
        for coin in carrom.player_coins[player]:
            if (coin.position.y < y_position and player == 0) or (coin.position.y > y_position and player == 1):
                dif = coin.position - center
                x = (y_position - center.y) * dif.x / dif.y + center.x
                if x_limits[0] <= x <= x_limits[1]:
                    other_coins = carrom.player_coins[other_player] + carrom.player_coins[player]
                    other_coins.remove(coin)
                    striker_position = Vector2(x, y_position)
                    for coin1 in other_coins:
                        """ This checks for between the striker and the coin """
                        angle_deg = (center - striker_position).angle_to(coin1.position - striker_position)
                        distance = striker_position.distance_to(coin1.position) * abs(sin(radians(angle_deg)))
                        if distance <= carrom.striker.radius + coin1.radius:
                            break
                    else:
                        coin.color = (255, 0, 255)
                        print(carrom.current_player(), "Striking Coin Found", x,
                              abs((striker_position - center).angle_to(Vector2(1, 0))))
                        if player == 0:
                            return 20, x, (striker_position - center).angle_to(Vector2(-1, 0))
                        else:
                            return 20, x, -(striker_position - center).angle_to(Vector2(-1, 0))
                striker_pos = coin.position - center
                striker_pos.scale_to_length(striker_pos.length() + coin.radius + carrom.striker.radius)
                striker_pos += center

                if x_limits[0] <= striker_pos.x <= x_limits[1]:
                    """ In-line """
                    other_coins = carrom.player_coins[other_player] + carrom.player_coins[player]
                    other_coins.remove(coin)
                    for coin1 in other_coins:
                        if abs(coin1.position.x - striker_pos.x) <= coin1.radius + carrom.striker.radius:
                            break
                        angle_deg = (center - coin.position).angle_to(coin1.position - coin.position)
                        distance = coin.position.distance_to(coin1.position) * abs(sin(radians(angle_deg)))
                        if distance <= carrom.striker.radius + coin1.radius:
                            break

                    else:
                        coin.color = (0, 255, 0)
                        print("Possible direct striker")
                        return 50, striker_pos.x, 90
    return None


def depth_ai(carrom: Carrom, max_angle):
    """ Construct a list of on board coins """
    on_board_coins = carrom.player_coins[0] + carrom.player_coins[1]
    if not carrom.pocketed_queen:
        on_board_coins.append(carrom.queen)
    player = carrom.player_turn
    x_limits = carrom.board.get_striker_x_limits()
    y_position = carrom.board.get_striker_y_position(player)
    """ Construct a 3 x 3 carrom image replicas """
    w, h = carrom.board.container.size
    positions = lambda x, y: [(w - x, h - y), (w + x, h - y), (3 * w - x, h - y),
                              (w - x, h + y), (w + x, h + y), (3 * w - x, h + y),
                              (w - x, 3 * h - y), (w + x, 3 * h - y), (3 * w - x, 3 * h - y)]
    reflected_coins = []
    pocket_centers = []
    """ Center carrom is where striker is """
    y_position = h + y_position
    x_limits = [w + x_limit for x_limit in x_limits]
    coin_radius, striker_radius = carrom.board.coin_radius, carrom.board.striker_radius
    for coin in on_board_coins:
        x_b, y_b = coin.position.x - carrom.board.board.left, coin.position.y - carrom.board.board.top
        for x, y in positions(x_b, y_b):
            coin1 = deepcopy(coin)
            coin1.position = Vector2(x, y)
            reflected_coins.append(coin1)
    for center in carrom.board.pocket_centers:
        x_b, y_b = center.x - carrom.board.board.left, center.y - carrom.board.board.top
        for x, y in positions(x_b, y_b):
            pocket_centers.append(Vector2(x, y))
    """ Now find some strike-able coin """
    direction_vec = Vector2(0, -1) if player == 0 else Vector2(0, 1)
    print("REF COINS:", len(reflected_coins), reflected_coins)
    print("CENTERS:", len(pocket_centers), pocket_centers)
    for center in pocket_centers:
        for coin in reflected_coins:
            if isinstance(coin, Queen) or coin.get_player() == player:
                print("Coin Position:", coin.position, "QUEEN" if isinstance(coin, Queen) else coin.get_player())
                angle = (center - coin.position).angle_to(direction_vec)
                print("Pocket Center:", center, "Angle:", angle)
                if abs(angle) <= max_angle:
                    """ Find corresponding striker position"""
                    striker_x = center.x + (y_position - center.y) * \
                                (coin.position.x - center.x) / (coin.position.y - center.y)
                    if x_limits[0] <= striker_x <= x_limits[1]:
                        print("Striker X:", striker_x, y_position, "LIMITS:", x_limits)
                        """ Strike-able if no obstacle """
                        striker_position = Vector2(striker_x, y_position)
                        print("_--------------------------")
                        to_check_coins = reflected_coins.copy()
                        to_check_coins.remove(coin)
                        for coin1 in to_check_coins:
                            # if coin1 != coin:
                            """ If not same coin, check if it will come in-between """
                            section = (coin1.position - striker_position).dot(center - striker_position) / \
                                      center.distance_squared_to(striker_position)
                            print("Section:", section)
                            if 0 <= section <= 1:
                                """ Potentially in-between, find distance to determine the same """
                                normal_point = striker_position.lerp(center, section)
                                print("normal point:", normal_point, "CENTER:", center, "COIN:", coin1.position,
                                      "STRIKER:", striker_position, normal_point.distance_to(coin1.position),
                                      "LIMIT:", striker_radius + coin_radius)
                                if normal_point.distance_to(coin1.position) <= striker_radius + coin_radius:
                                    """ Some coin inbetween """
                                    break
                        else:
                            """ If nothing in-between, done strike-able """
                            x = striker_x - w
                            print("Hittable:", x, angle, coin.position)
                            position = Vector2()
                            if 0 <= coin.position.x <= w:
                                position.x = w - coin.position.x
                            elif w <= coin.position.x <= 2 * w:
                                position.x = coin.position.x - w
                            else:
                                position.x = 3 * w - coin.position.x
                            if 0 <= coin.position.y <= h:
                                position.y = h - coin.position.y
                            elif h <= coin.position.y <= 2 * h:
                                position.y = coin.position.y - w
                            else:
                                position.y = 3 * h - coin.position.y
                            for coin in carrom.player_coins[0] + carrom.player_coins[1]:
                                if coin.position == position:
                                    coin.color = (0, 255, 0)
                                    print("FOUND")
                            print(position)
                            return x, angle
