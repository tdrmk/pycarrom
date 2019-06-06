from pygame import Vector2
from carrom import Carrom
from math import sqrt, cos, radians


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


def check_inside_container(position, radius, container):
    """ This function checks if the given coin (given by position and radius)
    lies entirely within the container of not """
    boundary_points = [
        Vector2(position.x + radius, position.y), Vector2(position.x, position.y + radius),
        Vector2(position.x - radius, position.y), Vector2(position.x, position.y - radius),
    ]
    """ returns true if all the boundary points lies within the container. """
    return all(container.collidepoint(point) for point in boundary_points)


def ___(angle_):
    """ This function is used to normalize angles """
    angle_ = angle_ % 360
    return angle_ if angle_ <= 180 else angle_ - 360


def ai(carrom: Carrom, max_angle, max_speed, decelerate, e, dt, max_cut_shot_angle=70, max_rebound_cut_shot_angle=70):
    """ Carrom Ai which knows to play direct shots, rebound shots and cuts """
    player, opponent = carrom.player_turn, (carrom.player_turn + 1) % 2
    """ Coins on the board and the coins which player can hit """
    board_coins = carrom.player_coins[0] + carrom.player_coins[1]
    if not carrom.pocketed_queen:
        board_coins.append(carrom.queen)

    if not carrom.pocketed_queen and len(carrom.player_coins[player]) == 1:
        """ If only one coin and queen, then hit only queen """
        playable_coins = [carrom.queen]
    else:
        playable_coins = carrom.player_coins[player].copy()
        if not carrom.pocketed_queen:
            playable_coins.insert(0, carrom.queen)

    """ Forward direction  of the player """
    direction_vec = Vector2(0, -1) if player == 0 else Vector2(0, 1)
    x_limits = carrom.board.get_striker_x_limits()
    y_position = carrom.board.get_striker_y_position(player)
    coin_radius, striker_radius = carrom.board.coin_radius, carrom.board.striker_radius
    board, container = carrom.board, carrom.board.container
    pocket_radius = board.pocket_radius
    pocket_centers = board.pocket_centers.copy()
    """ Added more positions to pocket center apart from just the centers, 
    add more positions to given more chances to pocket """
    for pocket_center in board.pocket_centers:
        pocket_centers.append(Vector2(pocket_center.x + pocket_radius - coin_radius, pocket_center.y))
        pocket_centers.append(Vector2(pocket_center.x - pocket_radius + coin_radius, pocket_center.y))
        pocket_centers.append(Vector2(pocket_center.x, pocket_center.y + pocket_radius - coin_radius))
        pocket_centers.append(Vector2(pocket_center.x, pocket_center.y - pocket_radius + coin_radius))
    """ Try hitting direct shots if any """
    for center in pocket_centers:
        for coin in playable_coins:
            if not check_along_path(coin.position, center, 2 * coin_radius,
                                    [coin_ for coin_ in board_coins if coin_ != coin]) and center.y != coin.position.y:
                scale_factor = (center.y - y_position) / (center.y - coin.position.y)
                striker_position = center + (coin.position - center) * scale_factor
                angle_of_attack = ___((center - striker_position).angle_to(direction_vec))
                attack_vector = coin.position - striker_position
                collision_position = striker_position + attack_vector.normalize() * \
                                     (attack_vector.length() - coin_radius - striker_radius)
                if (x_limits[0] <= striker_position.x <= x_limits[1]) and abs(angle_of_attack) <= max_angle \
                        and scale_factor > 1 and \
                        not check_along_path(striker_position, collision_position, coin_radius + striker_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin], round_end=True):
                    carrom.striker.position = striker_position
                    striker_speed = straight_shot_speed(carrom, striker_position, coin.position, center,
                                                        decelerate, e)
                    striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                    carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                    print("AI", carrom.current_player(), "Hits Direct Strike")
                    return
    """ Try hitting rebound shots, striker hits the board frame and then hits the inline coin """
    for index, center in enumerate(board.pocket_centers):
        for coin in playable_coins:
            if not check_along_path(coin.position, center, 2 * carrom.board.coin_radius,
                                    [coin_ for coin_ in board_coins if coin_ != coin]) and \
                    center.y != coin.position.y and center.x != coin.position.x:
                """ Rebound with top or bottom """
                rebound_y = board.diagonal_pocket_opposite[index][1]
                normal_vec = board.normal_vectors[index][1]
                scale_factor = (center.y - rebound_y) / (center.y - coin.position.y)
                rebound_position = center + (coin.position - center) * scale_factor
                attack_vector = coin.position - rebound_position
                collision_position = rebound_position + attack_vector.normalize() * \
                                     (attack_vector.length() - coin_radius - striker_radius)
                if container.left <= rebound_position.x <= container.right and scale_factor > 1 and \
                        not check_along_path(rebound_position, collision_position, coin_radius + striker_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin], round_end=True):
                    scale_factor = (rebound_position.y - y_position) / (rebound_position.y - center.y)
                    striker_position = rebound_position - (center - rebound_position).reflect(
                        normal_vec) * scale_factor
                    if x_limits[0] <= striker_position.x <= x_limits[1]:
                        angle_of_attack = ___((rebound_position - striker_position).angle_to(direction_vec))
                        if not check_along_path(rebound_position, striker_position, coin_radius + striker_radius,
                                                board_coins) and abs(angle_of_attack) <= max_angle:
                            carrom.striker.position = striker_position
                            striker_speed = rebound_shot_speed(carrom, striker_position, coin.position,
                                                               rebound_position, center, decelerate, e)
                            striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                            carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                            print("AI", carrom.current_player(), "Tries Rebound Shot (top/bottom)")
                            return
                """ Rebound with left or right """
                rebound_x = board.diagonal_pocket_opposite[index][0]
                normal_vec = board.normal_vectors[index][0]
                scale_factor = (center.x - rebound_x) / (center.x - coin.position.x)
                rebound_position = center + (coin.position - center) * scale_factor
                attack_vector = coin.position - rebound_position
                collision_position = rebound_position + attack_vector.normalize() * \
                                     (attack_vector.length() - coin_radius - striker_radius)
                if container.top <= rebound_position.y <= container.bottom and scale_factor > 1 and \
                        not check_along_path(rebound_position, collision_position, coin_radius + striker_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin], round_end=True):
                    scale_factor = (rebound_position.y - y_position) / (rebound_position.y - center.y)
                    striker_position = rebound_position + (center - rebound_position).reflect(
                        normal_vec) * scale_factor
                    if x_limits[0] <= striker_position.x <= x_limits[1]:
                        angle_of_attack = ___((rebound_position - striker_position).angle_to(direction_vec))
                        if not check_along_path(rebound_position, striker_position, coin_radius + striker_radius,
                                                board_coins) and abs(angle_of_attack) <= max_angle:
                            carrom.striker.position = striker_position
                            striker_speed = rebound_shot_speed(carrom, striker_position, coin.position,
                                                               rebound_position, center, decelerate, e)
                            striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                            carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                            print("AI", carrom.current_player(), "Tries Rebound Shot (left/right)")
                            return

    """ Try doubling, hit the coin onto the frame, then goes to the pocket,
    NOTE:this may not always work, if coin is close to the frame, chances are that it will hit the striker again """

    for center in pocket_centers:
        for coin in playable_coins:
            rebound_x__ = lambda rebound_y_: center.x + (coin.position.x - center.x) * \
                                             (center.y - rebound_y_) / (center.y + coin.position.y - 2 * rebound_y_)
            rebound_y__ = lambda rebound_x_: center.y + (coin.position.y - center.y) * \
                                             (center.x - rebound_x_) / (center.x + coin.position.x - 2 * rebound_x_)
            rebounds = [
                Vector2(container.left + coin_radius, rebound_y__(container.left + coin_radius)),
                Vector2(container.right - coin_radius, rebound_y__(container.right - coin_radius)),
                Vector2(rebound_x__(container.top + coin_radius), container.top + coin_radius),
                Vector2(rebound_x__(container.bottom - coin_radius), container.bottom - coin_radius),
            ]
            for rebound_position in rebounds:
                angle_of_attack = ___((rebound_position - coin.position).angle_to(direction_vec))
                scale_factor = (rebound_position.y - y_position) / (rebound_position.y - coin.position.y)
                striker_position = rebound_position + (coin.position - rebound_position) * scale_factor
                attack_vector = coin.position - striker_position
                collision_position = striker_position + attack_vector.normalize() * \
                                     (attack_vector.length() - coin_radius - striker_radius)

                if (x_limits[0] <= striker_position.x <= x_limits[1]) and abs(angle_of_attack) <= max_angle \
                        and scale_factor > 1 and \
                        not check_along_path(striker_position, collision_position, striker_radius + coin_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin], round_end=True) and \
                        not check_along_path(coin.position, rebound_position, 2 * coin_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin]) and \
                        not check_along_path(rebound_position, center, 2 * coin_radius, board_coins):
                    striker_speed = doubling_shot_speed(carrom, striker_position, coin.position, rebound_position,
                                                        center, decelerate, e)
                    carrom.striker.position = striker_position
                    striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                    carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                    print("AI", carrom.current_player(), "Hits Doubling shot")
                    return
    """ Try cut shots, within the given angle, may not always work, due to in-accuracies in simulation 
    due to discretization of simulations """
    for center in pocket_centers:
        for coin in playable_coins:
            expected_position = center + (coin.position - center).normalize() * \
                                (center.distance_to(coin.position) + striker_radius + coin_radius)
            """ Also check if expected position is with board.. """
            if not check_along_path(coin.position, center, 2 * coin_radius,
                                    [coin_ for coin_ in board_coins if coin_ != coin])\
                    and check_inside_container(expected_position, striker_radius, container):
                for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
                    striker_position = Vector2(striker_x, y_position)
                    force_angle = ___((center - coin.position).angle_to(expected_position - striker_position))
                    angle_of_attack = ___((expected_position - striker_position).angle_to(direction_vec))
                    if abs(force_angle) <= max_cut_shot_angle and abs(angle_of_attack) <= max_angle and \
                            not check_along_path(striker_position, expected_position, striker_radius + coin_radius,
                                                 [coin_ for coin_ in board_coins if coin_ != coin], round_end=True):
                        striker_speed = cut_shot_speed(carrom, striker_position, coin.position,
                                                       expected_position, force_angle,
                                                       center, decelerate, e, dt)
                        carrom.striker.position = striker_position
                        striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                        carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                        print("AI", carrom.current_player(), "Cut Shot with angle:", "%0.2f" % force_angle, "degrees",
                              "Speed:", striker_speed)
                        return
    """ Also try out rebound cut shots, if possible, not accurate though """
    for center in pocket_centers:
        for coin in playable_coins:
            expected_position = center + (coin.position - center).normalize() * \
                                (center.distance_to(coin.position) + striker_radius + coin_radius)
            """ Also check if expected position is with board.. """
            if not check_along_path(coin.position, center, 2 * coin_radius,
                                    [coin_ for coin_ in board_coins if coin_ != coin])\
                    and check_inside_container(expected_position, striker_radius, container):
                for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
                    striker_position = Vector2(striker_x, y_position)
                    rebound_x__ = lambda rebound_y_: \
                        expected_position.x + (striker_position.x - expected_position.x) * \
                        (expected_position.y - rebound_y_) / (expected_position.y + striker_position.y - 2 * rebound_y_)
                    rebound_y__ = lambda rebound_x_: \
                        expected_position.y + (striker_position.y - expected_position.y) * \
                        (expected_position.x - rebound_x_) / (expected_position.x + striker_position.x - 2 * rebound_x_)
                    rebounds = [
                        Vector2(container.left + striker_radius, rebound_y__(container.left + striker_radius)),
                        Vector2(container.right - striker_radius, rebound_y__(container.right - striker_radius)),
                        Vector2(rebound_x__(container.top + striker_radius), container.top + striker_radius),
                        Vector2(rebound_x__(container.bottom - striker_radius), container.bottom - striker_radius),
                    ]
                    for rebound_position in rebounds:
                        angle_of_attack = ___((rebound_position - striker_position).angle_to(direction_vec))
                        force_angle = ___((center - coin.position).angle_to(expected_position - rebound_position))
                        if abs(force_angle) <= max_rebound_cut_shot_angle and abs(angle_of_attack) <= max_angle and \
                                not check_along_path(rebound_position, expected_position, striker_radius + coin_radius,
                                                     [coin_ for coin_ in board_coins if coin_ != coin],
                                                     round_end=True) and \
                                not check_along_path(rebound_position, striker_position, coin_radius + striker_radius,
                                                     board_coins):
                            carrom.striker.position = striker_position
                            striker_speed = rebound_cut_shot_speed(
                                carrom, striker_position, coin.position, rebound_position, expected_position,
                                force_angle, center, decelerate, e, dt)
                            striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                            carrom.striker.velocity.from_polar((striker_speed, striker_angle))
                            print("AI", carrom.current_player(), "Tries Rebound Cut Shot with angle:",
                                  "%0.2f" % force_angle, "degrees", "Speed:", striker_speed)
                            return

    """ Simply hit straight at some coin """
    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position = Vector2(striker_x, y_position)
            angle_of_attack = ___((coin.position - striker_position).angle_to(direction_vec))
            attack_vector = coin.position - striker_position
            collision_position = striker_position + attack_vector.normalize() * \
                                 (attack_vector.length() - coin_radius - striker_radius)
            if not check_along_path(striker_position, collision_position, striker_radius + coin_radius,
                                    [coin_ for coin_ in board_coins if coin_ != coin], round_end=True) and \
                    abs(angle_of_attack) <= max_angle:
                """ Simply hit the coins with max speed """
                carrom.striker.position = striker_position
                striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                carrom.striker.velocity.from_polar((max_speed, striker_angle))
                print("AI", carrom.current_player(), "does a simply direct hit with angle:",
                      "%0.2f" % angle_of_attack, "degrees")
                return

    """ Simply hit rebound shot at some coin """
    rebound_x__ = lambda striker_pos_, coin_pos_, rebound_y_: coin_pos_.x + (striker_pos_.x - coin_pos_.x) * \
                                                              (coin_pos_.y - rebound_y_) / (
                                                                      coin_pos_.y + striker_pos_.y - 2 * rebound_y_)
    rebound_y__ = lambda striker_pos_, coin_pos_, rebound_x_: coin_pos_.y + (striker_pos_.y - coin_pos_.y) * \
                                                              (coin_pos_.x - rebound_x_) / (
                                                                      coin_pos_.x + striker_pos_.x - 2 * rebound_x_)

    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position, c_pos, s_radius = Vector2(striker_x, y_position), coin.position, striker_radius
            c_left, c_right, c_top, c_bottom = container.left, container.right, container.top, container.bottom
            rebounds = [
                Vector2(c_left + s_radius, rebound_y__(striker_position, c_pos, c_left + s_radius)),
                Vector2(c_right - s_radius, rebound_y__(striker_position, c_pos, c_right - s_radius)),
                Vector2(rebound_x__(striker_position, c_pos, c_top + s_radius), c_top + s_radius),
                Vector2(rebound_x__(striker_position, c_pos, c_bottom - s_radius), c_bottom - s_radius),
            ]
            for rebound_position in rebounds:
                angle_of_attack = ___((rebound_position - striker_position).angle_to(direction_vec))
                attack_vector = coin.position - rebound_position
                collision_position = rebound_position + attack_vector.normalize() * \
                                     (attack_vector.length() - coin_radius - striker_radius)
                if abs(angle_of_attack) <= max_angle and \
                        not check_along_path(rebound_position, collision_position, striker_radius + coin_radius,
                                             [coin_ for coin_ in board_coins if coin_ != coin], round_end=True) and \
                        not check_along_path(rebound_position, striker_position, coin_radius + striker_radius,
                                             board_coins):
                    """ Simply hit the coins with max speed """
                    carrom.striker.position = striker_position
                    striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                    carrom.striker.velocity.from_polar((max_speed, striker_angle))
                    print("AI", carrom.current_player(), "does a simply rebound hit with angle:",
                          "%0.2f" % angle_of_attack, "degrees")
                    return
    """ If nothing can be hit either way don't worry about the fouls try hitting the coin """
    """ Simply hit straight at some coin """
    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position = Vector2(striker_x, y_position)
            angle_of_attack = ___((coin.position - striker_position).angle_to(direction_vec))
            attack_vector = coin.position - striker_position
            if abs(angle_of_attack) <= max_angle:
                """ Simply hit the coins with max speed """
                carrom.striker.position = striker_position
                striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                carrom.striker.velocity.from_polar((max_speed, striker_angle))
                print("AI", carrom.current_player(), "does a simply direct hit with angle:",
                      "%0.2f" % angle_of_attack, "degrees", "may face penalty")
                return
    for coin in playable_coins:
        for striker_x in range(int(x_limits[0]), int(x_limits[1] + 1), 1):
            striker_position, c_pos, s_radius = Vector2(striker_x, y_position), coin.position, striker_radius
            c_left, c_right, c_top, c_bottom = container.left, container.right, container.top, container.bottom
            rebounds = [
                Vector2(c_left + s_radius, rebound_y__(striker_position, c_pos, c_left + s_radius)),
                Vector2(c_right - s_radius, rebound_y__(striker_position, c_pos, c_right - s_radius)),
                Vector2(rebound_x__(striker_position, c_pos, c_top + s_radius), c_top + s_radius),
                Vector2(rebound_x__(striker_position, c_pos, c_bottom - s_radius), c_bottom - s_radius),
            ]
            for rebound_position in rebounds:
                angle_of_attack = ___((rebound_position - striker_position).angle_to(direction_vec))
                attack_vector = coin.position - rebound_position
                if abs(angle_of_attack) <= max_angle:
                    """ Simply hit the coins with max speed """
                    carrom.striker.position = striker_position
                    striker_angle = -90 - angle_of_attack if player == 0 else 90 - angle_of_attack
                    carrom.striker.velocity.from_polar((max_speed, striker_angle))
                    print("AI", carrom.current_player(), "does a simply rebound hit with angle:",
                          "%0.2f" % angle_of_attack, "degrees", "may face penalty")
                    return
    print("Nothing done..")


def straight_shot_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2,
                        pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    distance_striker_coin = striker_position.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / ((1 + e) * board.STRIKER_MASS)
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def rebound_shot_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, rebound_position: Vector2,
                       pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_striker_coin = striker_position.distance_to(rebound_position) + rebound_position.distance_to(coin_position)
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / ((1 + e) * board.STRIKER_MASS)
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def doubling_shot_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, rebound_position: Vector2,
                        pocket_center: Vector2, decelerate, e):
    board = carrom.board
    distance_striker_coin = striker_position.distance_to(coin_position)
    distance_coin_pocket = pocket_center.distance_to(rebound_position) + rebound_position.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / ((1 + e) * board.STRIKER_MASS)
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    return striker_speed


def cut_shot_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, expected_position: Vector2,
                   force_angle, pocket_center: Vector2, decelerate, e, dt):
    board = carrom.board
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    """ Added a little more to be on the safer side """
    distance_striker_coin = striker_position.distance_to(expected_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(force_angle)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    """ Sometimes speed is not just sufficient add some more, also for better shots, time of hit in terms of dt"""
    time = (striker_speed - col_striker_speed) / decelerate
    time = 0.95 * time
    time = time - (time % dt)
    striker_speed = (distance_striker_coin + decelerate * time ** 2 / 2) / time
    return striker_speed


def rebound_cut_shot_speed(carrom: Carrom, striker_position: Vector2, coin_position: Vector2, rebound_position: Vector2,
                           expected_position: Vector2, force_angle, pocket_center: Vector2, decelerate, e, dt):
    board = carrom.board
    distance_striker_coin = striker_position.distance_to(rebound_position) + \
        rebound_position.distance_to(expected_position)
    distance_coin_pocket = pocket_center.distance_to(coin_position)
    col_coin_speed = sqrt(2 * distance_coin_pocket * decelerate)
    col_striker_speed = col_coin_speed * (board.COIN_MASS + board.STRIKER_MASS) / \
                        ((1 + e) * board.STRIKER_MASS * cos(radians(force_angle)))
    striker_speed = sqrt(col_striker_speed ** 2 + 2 * decelerate * distance_striker_coin)
    """ Sometimes speed is not just sufficient add some more, also for better shots, time of hit in terms of dt"""
    time = (striker_speed - col_striker_speed) / decelerate
    time = 0.95 * time
    time = time - (time % dt)
    striker_speed = (distance_striker_coin + decelerate * time ** 2 / 2) / time
    return striker_speed
