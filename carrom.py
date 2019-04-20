from coin import CarromMen, Queen, Striker
from pygame import Rect
from pygame import Vector2
import logging
import sys
from math import sqrt
from itertools import combinations
from board import Board

logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class Carrom:
    def __init__(self, board_rect: Rect):
        """ Must be a squared """
        board = Board(board_rect)
        self.board = board
        self.center = Vector2(board.container.center)
        self.queen = Queen(board.coin_radius, Board.COIN_MASS, self.center, board.container)
        self.striker = Striker(board.striker_radius, Board.STRIKER_MASS, board.container)
        """ Coins player order defined in a way suitable for rotate method """
        self.coins = [CarromMen(i % 2, board.coin_radius, Board.COIN_MASS, self.center, board.container) for i in range(6)] \
            + [CarromMen(0, board.coin_radius, Board.COIN_MASS, self.center, board.container) for _ in range(6)]\
            + [CarromMen(1, board.coin_radius, Board.COIN_MASS, self.center, board.container) for _ in range(6)]
        self.rotate_carrom_men(60)

        """ All the states of the carrom board """
        """ Player coins will contain the list of player coins on the board """
        self.player_coins = ([], [])
        for coin in self.coins:
            """ Initially add all the coins to the board """
            self.player_coins[coin.get_player()].append(coin)
        """ Player coins that were pocketed """
        self.pocketed_coins = ([], [])
        """ Number of fouls a given player committed """
        self.foul_count = [0, 0]
        """ Whether the player captured the queen or not """
        self.has_queen = [False, False]
        """ Whether queen was pocketed or not """
        self.pocketed_queen = False
        """ Whether queen was captured on previous turn and needs a follow on """
        self.queen_on_hold = False
        """ Whether striker was pocketed or not in the current shot """
        self.pocketed_striker = False
        """ List of all carrom coins (carrom men), that were pocketed in current shot """
        self.current_pocketed = []
        """ The current player turn, there are two players """
        self.player_turn = 0
        """ Whether game is over or not and if yes who is the winner and why """
        self.game_over = False
        self.winner = None
        self.reason = None
        self.first_collision = None

    def rotate_carrom_men(self, init_rotation=60):
        """ if player wants to rotate the carrom men at the start call this function """
        vec = Vector2(0, -1)
        vec.rotate_ip(init_rotation)
        vec.scale_to_length(self.board.coin_radius * 2)
        for index, coin in enumerate(self.coins):
            if index == 6:
                vec.scale_to_length(self.board.coin_radius * 4)
            elif index == 12:
                vec.scale_to_length(self.board.coin_radius * (2 * sqrt(3)))
                vec.rotate_ip(30)
            coin.position = self.center + vec
            vec.rotate_ip(60)

    def check_moving(self):
        """ This function is used to check if some coin is moving on the board """
        coins = self.player_coins[0] + self.player_coins[1]
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)
        """ Return true there exist some coin which is moving"""
        return any(coin.check_moving() for coin in coins)

    def update(self, dt, decelerate, e):
        """ After striking, this function is used to update the positions of the coins on the board,
         call this function to proceed the simulation by given delta time. decelerate is used to model friction
         e is the coefficient of restitution for collision between coins. """
        """ coins will contain the list of coins to consider for simulation """
        """ Sort it so that first check collisions with the player coins and the striker and then with others """
        coins = sorted(self.player_coins[0] + self.player_coins[1],
                       key=lambda coin_: coin_.get_player() == self.player_turn, reverse=True)
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)

        """ Check for collisions and change velocities on collision """
        for coin1, coin2 in combinations(coins, 2):
            if coin1.check_collision(coin2):
                if not self.first_collision and (coin1.check_moving() or coin2.check_moving()):
                    """ Detect the first collision between coins """
                    self.first_collision = [coin1, coin2]
                coin1.collide(coin2, e)

        for coin in coins:
            """ Update the position of each of the coins """
            coin.update(dt, decelerate)
            """ Now check if pocketed """
            if self.board.pocketed(coin):
                if coin == self.striker:
                    self.pocketed_striker = True
                elif coin == self.queen:
                    self.pocketed_queen = True
                else:
                    assert isinstance(coin, CarromMen)
                    """ Move coins to pocketed coins for that player """
                    self.player_coins[coin.get_player()].remove(coin)
                    self.pocketed_coins[coin.get_player()].append(coin)
                    """ Also add to the current pocketed, this is kept to return them back to board in case of foul"""
                    self.current_pocketed.append(coin)

    def __handle_fouls__(self, player):
        """ This function is used to handle player fouls of the given player, if any foul for the given player,
        and any pocketed coin, then place it back to the board. If no player coin and conquered the queen,
        then place back the queen itself """
        for _ in range(self.foul_count[player]):
            """ If current player has any foul """
            if self.pocketed_coins[player]:
                """ If any coin was pocketed by the player, place it back and reduce the foul count """
                """ Get some pocketed player coin and place it back """
                coin = self.pocketed_coins[player].pop()
                self.player_coins[player].append(coin)
                coin.reset()
                """ Reduce the foul count """
                self.foul_count[player] -= 1
                logging.info(self.get_player(player) + " Coin Reset, Foul Reduced")
            else:
                """ If no more pocketed coins to pay for fouls, then place the queen if acquired by the place """
                """ Both players can't have the queen simultaneously """
                assert not (self.has_queen[0] and self.has_queen[1])
                if self.pocketed_queen and self.has_queen[player]:
                    """ If player has the queen, the reset it """
                    self.has_queen[player] = False
                    self.queen_on_hold = False
                    self.pocketed_queen = False
                    self.queen.reset()
                    self.foul_count[player] -= 1
                    logging.info(self.get_player(player) + " Queen Reset, Foul Reduced")
                break

    def __update_turn__(self, change: bool):
        """ This function is used to update the player turn, it changes if the player turn if specified.
         This function also handles the fouls, if any foul and some pocketed coins of the any player,
         then place it back to the center.
         """
        """ Handle fouls of both the players """
        self.__handle_fouls__(0)
        self.__handle_fouls__(1)

        if not self.player_coins[self.player_turn]:
            """ If all the player coins of the current player are pocketed """
            if not self.pocketed_queen:
                """ However if queen was not pocketed, current player incurs a penalty of 2 player coins  """
                logging.warning(self.current_player() + " Pocketed All Coins without Capturing Queen,"
                                                        " Incurs Heavy Penalty")
                self.foul_count[self.player_turn] += 2
                """ Call update turn function again with updated penalty. 
                Note that player turn changes irrespective of whether turn was to change or not."""
                self.__update_turn__(change=True)
                return
            else:
                """ if queen was acquired, as no need to check which player has acquired the queen. 
                 winner is the one whose coins where pocketed. """
                """ Note: if the current player pocketed all coins including the opponent coins,
                 the current player is declared the winner not the opponent """
                self.winner = self.player_turn
                self.reason = "Player pocketed all coins"
                self.game_over = True
                logging.debug(self.current_player() + " Pocketed All Coins, Declared Winner!!")
                """ Don't proceed """
                return
        other_player = (self.player_turn + 1) % 2
        if not self.player_coins[other_player]:
            """ If all coins of other player were pocket """
            if not self.pocketed_queen or not (self.has_queen[0] or self.has_queen[1]):
                """ If queen was not pocketed or was on hold, then restore the opponents coin """
                coin = self.pocketed_coins[other_player].pop()
                self.player_coins[other_player].append(coin)
                coin.reset()
                """ Add penalty for hitting other's coin """
                self.foul_count[self.player_turn] += 2
                logging.warning(self.current_player() + " Pocketed All Enemy Coins without Capturing Queen,"
                                                        " Incurs Heavy Penalty")
                if self.pocketed_queen:
                    """ If queen was pocketed in the current and on hold, place it back """
                    self.queen_on_hold = False
                    self.pocketed_queen = False
                    logging.debug(self.current_player() + " Pocketed All Enemy Coins When Queen On Hold, Queen Reset")
                    self.queen.reset()

                """ Change the turn of the player """
                self.__update_turn__(change=True)
                return
            else:
                """ If queen was already conquered, then other player is the winner """
                self.winner = other_player
                self.reason = "Player pocketed all of other players coins"
                self.game_over = True
                logging.debug(self.current_player() + " Pocketed All Enemy Coins, " +
                              self.get_player(other_player) + " Declared Winner!!")
                """ Don;t proceed """
                return

        """ Reset the currently pocketed coins and ensure striker back on board """
        self.current_pocketed = []
        self.pocketed_striker = False
        self.striker.velocity = Vector2()
        if change:
            logging.debug(self.current_player() + " Lost Turn.")
            """ Change turn if specified """
            self.player_turn = (self.player_turn + 1) % 2
            logging.debug(self.current_player() + " Turn Begins")

    def current_player(self):
        return "WHITE" if self.player_turn == 0 else "BLACK"

    @staticmethod
    def get_player(player):
        return "WHITE" if player == 0 else "BLACK"

    def apply_rules(self):
        """ Once all coins on the board stopped moving after strike, call this function to decide what to do next
         whether to maintain the turn and allow the player to striker again or to change the turn.
         This essentially applies the rules of the carrom and updates the overall state of the carrom """
        """ Check for the first collision """
        if self.first_collision:
            coin1, coin2 = self.first_collision
            assert isinstance(coin1, Striker) or isinstance(coin2, Striker)
            coin = coin2 if isinstance(coin1, Striker) else coin1
            if not isinstance(coin, Queen):
                if self.player_turn != coin.get_player():
                    """ If striking other players coin, then incur foul """
                    self.foul_count[self.player_turn] += 1
                    logging.warning(self.current_player() + " Incurred Foul Hitting Other Players Coin")
            self.first_collision = None
        if self.pocketed_striker:
            """ Rule: If striker is pocketed, then whatever was pocketed this turn (current player coins plus queen) 
            goes back along a foul. Note this does not affect coins of the opponent, 
            however if it was the final coin a opponent coin may be place back with addition fouls being added """
            if self.pocketed_queen and not self.has_queen[0] and not self.has_queen[1]:
                """ If queen was pocketed in the current turn or previous, then place it back """
                """ Queen not on hold nor pocketed, and place it back to the center """
                self.queen_on_hold = False
                self.pocketed_queen = False
                logging.debug(self.current_player() + " Pocketed Striker, Queen Reset")
                self.queen.reset()
            for coin in self.current_pocketed:
                """ For all the player coins pocketed in this turn, place it back to the center """
                if coin.get_player() == self.player_turn:
                    """ If pocketed coin belongs to player, then place it back """
                    self.player_coins[coin.get_player()].append(coin)
                    self.pocketed_coins[coin.get_player()].remove(coin)
                    logging.debug(self.current_player() + " Pocketed Striker, Coin Reset")
                    coin.reset()
            """ Add a foul to the current player """
            self.foul_count[self.player_turn] += 1
            """ Update the turn to the next player, 
            also handle cases if all other coins were pocketed or place coins back to center to handle fouls """
            logging.warning(self.current_player() + " Pocketed Striker, Incurred Foul")
            self.__update_turn__(change=True)

        elif self.pocketed_queen and not self.has_queen[0] and not self.has_queen[1]:
            """ If queen was pocketed, then check if it was pocketed in the current turn or previous turn """
            for coin in self.current_pocketed:
                """ Irrespective of whether queen was pocket in current turn or previous, 
                if any player coin was pocketed then queen belongs to the current player """
                if coin.get_player() == self.player_turn:
                    """ If also player coin was pocketed, then player acquires the queen """
                    self.has_queen[self.player_turn] = True
                    self.queen_on_hold = False
                    """ Don't change the turn, however handle penalties if any from previous turn """
                    logging.debug(self.current_player() + " Pocketed Queen, With Follow")
                    self.__update_turn__(change=False)
                    break
            else:
                """ If no player coin was pocketed, and queen was pocketed in previous turn (on hold), 
                then place it back to the board  """
                if self.queen_on_hold:
                    """ If queen was on hold, then release it  """
                    self.queen_on_hold = False
                    self.pocketed_queen = False
                    self.queen.reset()
                    """ Change the turn """
                    logging.debug(self.current_player() + " Lost Queen From Hold, No Follow")
                    self.__update_turn__(change=True)
                else:
                    """ if queen was pocketed in the current turn without pocketing 
                    any current player coin in the turn, then place the queen on hold and player can acquire it
                    if it follows with a player coin """
                    self.queen_on_hold = True
                    """ Don;t change turn """
                    logging.debug(self.current_player() + " Pocketed Queen, On Hold")
                    self.__update_turn__(change=False)

        else:
            """ If any coin was pocket, check if it belongs to the player, if yes keep turn """
            for coin in self.current_pocketed:
                if coin.get_player() == self.player_turn:
                    """ Can keep turn """
                    logging.debug(self.current_player() + " Pocketed Coin(s)")
                    self.__update_turn__(change=False)
                    break
            else:
                """ If no player coin was pocketed or no coin was pocketed, the change the turn """
                logging.debug(self.current_player() + " Pocketed Nothing")
                self.__update_turn__(change=True)

    def draw(self, win):
        """ Draws all board with all the coins on the board and those that were captured """
        self.board.draw(win)
        """ Draw the coins (including striker and queen) on the board """
        coins = self.player_coins[0] + self.player_coins[1]
        if not self.pocketed_striker:
            coins.append(self.striker)
        if not self.pocketed_queen:
            coins.append(self.queen)
        for coin in coins:
            coin.draw(win)
        """ Draw the captured coins """
        captured_coins_0 = self.pocketed_coins[0].copy()
        if self.has_queen[0]:
            captured_coins_0.append(self.queen)
        captured_coins_1 = self.pocketed_coins[1].copy()
        if self.has_queen[1]:
            captured_coins_1.append(self.queen)
        self.board.draw_captured_coins(win, 0, captured_coins_0)
        self.board.draw_captured_coins(win, 1, captured_coins_1)
