import socket
from socket_utils import read_message, write_message
import pygame
from carrom import Carrom
import pickle
from pygame import Vector2
server_host, server_port = '', 9901
server_address = (server_host, server_port)
encoding = 'utf-8'

pygame.init()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as sock:
    sock.connect(server_address)
    player_id = read_message(sock)
    print("Received Player ID info")
    if player_id == b'0':
        player = 0
        permit_rotation = True
    else:
        player = 1
        permit_rotation = False

    print("Current player is ", player)
    setup_gui = True
    striker_speed = 0
    striker_angle = 90
    max_angle = 90
    max_speed = 100
    """ Used to provide initial rotation """
    coins_orientation = 60

    """ Vector for modelling speed """
    speed_vector = Vector2()
    run = True
    message = read_message(sock)
    carrom = pickle.loads(message)
    print("Got carrom info")
    assert isinstance(carrom, Carrom)

    print("Setting up GUI")
    width, height = carrom.board.board.size
    win = pygame.display.set_mode((width, height))
    player_color = "WHITE" if player == 0 else "BLACK"
    pygame.display.set_caption("PyCarrom " + player_color)
    carrom.draw(win)
    pygame.display.update()
    clock = pygame.time.Clock()

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        if carrom.game_over:
            print("Game Over")
            """ If game is over then don't handle any user inputs """
            font = pygame.font.Font('freesansbold.ttf', carrom.board.board.width // 20)
            winner = 'WHITE' if carrom.winner == 0 else 'BLACK'
            text = font.render('Game Over!! Winner:' + winner, True, (0, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = carrom.board.container.center
            win.blit(text, text_rect)
            pygame.display.update()
            continue

        if carrom.check_moving():
            print("Carrom is moving")
            """ If carrom is moving """
            message = read_message(sock)
            carrom = pickle.loads(message)
            carrom.draw(win)
            carrom.board.show_notification(win, "Coins Moving")
            pygame.display.update()

        else:
            # print("Carrom is not moving")
            """ If not moving, check player chance """
            if carrom.player_turn == player:
                clock.tick(60)
                # print("Current player turn")
                """ Current player turn """
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

                if pressed[pygame.K_r] and permit_rotation:
                    """ Rotate the coins as per player requirements before starting the game """
                    coins_orientation += 1 if not pressed[pygame.K_LSHIFT] else -1
                    carrom.rotate_carrom_men(coins_orientation)

                carrom.draw(win)
                carrom.board.show_notification(win, "Your Turn! Setup Striker!")
                x_limits = carrom.board.get_striker_x_limits()
                carrom.striker.position.x = min(x_limits[1], max(x_limits[0], carrom.striker.position.x))
                striker_speed = min(max_speed, max(striker_speed, 0))
                striker_angle = min(90 + max_angle, max(90 - max_angle, striker_angle))

                speed_vector.from_polar((striker_speed, -striker_angle if carrom.player_turn == 0 else striker_angle))
                position_vector = carrom.striker.position + speed_vector * 5
                pygame.draw.line(win, (0, 0, 0), (int(carrom.striker.position.x), int(carrom.striker.position.y)),
                                 (int(position_vector.x), int(position_vector.y)))
                pygame.display.update()

                if pressed[pygame.K_SPACE]:
                    carrom.striker.velocity.from_polar((striker_speed,
                        -striker_angle if carrom.player_turn == 0 else striker_angle))
                    if permit_rotation:
                        """ Initially allow rotation """
                        """ Send orientation to the server """
                        print("Coin Orientation:", coins_orientation)
                        write_message(sock, str(coins_orientation).encode(encoding))
                        permit_rotation = False

                    striker_data = pickle.dumps(carrom.striker)
                    striker_speed = 0
                    striker_angle = 90
                    """ Vector for modelling speed """
                    speed_vector = Vector2()
                    write_message(sock, striker_data)
            else:
                print("Waiting....")
                carrom.draw(win)
                carrom.board.show_notification(win, "Waiting. Opponents Turn")
                pygame.display.update()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        run = False
                message = read_message(sock)
                carrom = pickle.loads(message)
                print("Got carrom")
    pygame.quit()








