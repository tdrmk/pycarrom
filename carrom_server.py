import socket
from socket_utils import write_message, read_message
from carrom import Carrom
from pygame import Rect
import pickle

# TODO: Currently client controls the maximum striker speed and angle, the server must limit as well
server_host, server_port = '', 9901
server_address = (server_host, server_port)
encoding = 'utf-8'

""" Width of carrom board to create """
width = 700
""" Collision parameters """
dt = 0.1
decelerate = 0.3
e = 0.9
""" After how many simulations/updates to send the carrom data to clients """
num_updates = 10

""" Create a listening socket which is bound to specified port """
with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as listen_sock:
    listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_sock.bind(server_address)
    listen_sock.listen(5)

    """ Accept client connections """
    while True:
        """ Create a carrom fo specified width """
        carrom = Carrom(Rect(0, 0, width, width))

        print("Waiting for clients to connect...")
        try:
            """ Connect to the clients and sent their player ID """
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
                """ Flag to indicate whether game was started or not, this is used to indicate 
                whether player can adjust the orientation of coins or not """
                """ Flag to allow orientation changes for first shot """
                permit_orientation = True
                coins_orientation = 60

                """ Initialize the striker position """
                carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)

                while not carrom.game_over:
                    print("Game in progress, Current turn:", carrom.player_turn)
                    """ Send the carrom data to both the clients """
                    carrom_data = pickle.dumps(carrom)
                    write_message(client_sock_0, carrom_data)
                    write_message(client_sock_1, carrom_data)
                    print("Sent carrom data to both the clients")
                    if permit_orientation:
                        """ Read the orientation message """
                        orientation_data = read_message(connections[carrom.player_turn])
                        coins_orientation = int(orientation_data.decode(encoding))
                        print("Setting the Carrom Men Orientation to", coins_orientation)
                        """ Rotate the coins by given orientation angle """
                        carrom.rotate_carrom_men(coins_orientation)
                        """ Disable it """
                        permit_orientation = False
                    """ Read the striker data, later check if striker velocity and angle within bounds """
                    striker_data = read_message(connections[carrom.player_turn])
                    carrom.striker = pickle.loads(striker_data)
                    print("Player", carrom.player_turn, "sent striker parameters")
                    i = 0
                    while carrom.check_moving():
                        """ If coins can move, update them and sent the carrom data back to the clients """
                        carrom.update(dt, decelerate, e)
                        carrom_data = pickle.dumps(carrom)
                        if carrom.check_moving():
                            """ Send data if moving """
                            i += 1
                            if i % 10 == 0:
                                write_message(client_sock_0, carrom_data)
                                write_message(client_sock_1, carrom_data)
                                print("Sent carrom data to players after", i, "updates")
                    print("Coins can't move any more and applying rules ...")
                    """ Apply rules """
                    carrom.apply_rules()
                    carrom.striker.position = carrom.board.get_striker_position(carrom.player_turn)

                print("Game Over won by", carrom.winner, "reason:", carrom.reason)
                """ Send the final data """
                carrom_data = pickle.dumps(carrom)
                write_message(client_sock_0, carrom_data)
                write_message(client_sock_1, carrom_data)
                """ Disconnect the clients and wait for next set of clients """
        except socket.error:
            print("Some client closed connection")


