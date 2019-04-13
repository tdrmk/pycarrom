import socket
from socket_utils import write_message, read_message
from carrom import Carrom
from pygame import Rect, Vector2
import pickle
server_host, server_port = '', 9901
server_address = (server_host, server_port)


""" Create a listening socket which is bound to specified port """
with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as listen_sock:
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(server_address)
    listen_sock.listen(5)

    """ Accept client connections """
    while True:
        width = 800
        encoding = 'utf-8'
        max_speed = 40
        max_angle = 90
        dt = 0.1
        decelerate = 0.3
        e = 0.9
        num_updates = 10
        carrom = Carrom(Rect(0, 0, width, width))

        client_sock_0, client_addr_0 = listen_sock.accept()
        print("Accepted client connection 0", client_addr_0)
        write_message(client_sock_0, '0'.encode(encoding))
        print("Sent player info to connection 0")

        client_sock_1, client_addr_1 = listen_sock.accept()
        print("Accepted client connection 1", client_addr_1)
        write_message(client_sock_1, '1'.encode(encoding))

        print("Sent player info to connection 1")
        with client_sock_0, client_sock_1:
            connections = [client_sock_0, client_sock_1]
            run = True
            """ Flag to indicate whether game was started or not, this is used to indicate 
            whether player can adjust the orientation of coins or not """
            game_started = False
            coins_orientation = 60

            """ Vector for modelling speed """
            speed_vector = Vector2()
            """ Initialize the striker position """
            carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)

            while not carrom.game_over:
                print("Game in progress")
                carrom_data = pickle.dumps(carrom)
                write_message(client_sock_0, carrom_data)
                write_message(client_sock_1, carrom_data)
                print("Sent carrom data")
                striker_data = read_message(connections[carrom.player_turn])
                print("Expecting striker data")
                carrom.striker = pickle.loads(striker_data)
                print("Sending data with striker")
                i = 0
                while carrom.check_moving():
                    print("While coin can move")
                    carrom.update(dt, decelerate, e)
                    carrom_data = pickle.dumps(carrom)
                    if carrom.check_moving():
                        print("Can still move")
                        """ Send data if moving """
                        i += 1
                        if i % 10 == 0:
                            write_message(client_sock_0, carrom_data)
                            write_message(client_sock_1, carrom_data)
                print("Coins can't move any more and applying rules ")
                """ Apply rules """
                carrom.apply_rules()
                print("Reset the striker position")
                carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)
            """ Send the final data """
            print("Game Over")
            carrom_data = pickle.dumps(carrom)
            write_message(client_sock_0, carrom_data)
            write_message(client_sock_1, carrom_data)


