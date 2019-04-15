import socket
from socket_utils import read_message, write_message
import pygame
from carrom import Carrom
import pickle
import tkinter

# server_host, server_port = '', 9901
# server_address = (server_host, server_port)
encoding = 'utf-8'


def connect_to_server():
    """ Create a tkinter window to request server address and tries connecting to it. """
    root = tkinter.Tk()
    root.title("Enter Server Details")
    address = tkinter.StringVar(value="localhost")
    port = tkinter.StringVar(value="9901")
    status = tkinter.StringVar()
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    def connect():
        if not port.get().isdigit():
            status.set("Invalid port.")
            return
        try:
            """ Try connecting to specified server address """
            nonlocal client_socket
            server_host, server_port = address.get(), int(port.get())
            client_socket.connect((server_host, server_port))
            """ If connected, then close the tkinter window """
            root.destroy()
        except socket.error:
            client_socket.close()
            """ Create a new socket """
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            status.set("Connection Failed..")

    tkinter.Label(root, text="Server IP").grid(row=0, column=0)
    tkinter.Entry(root, textvariable=address).grid(row=0, column=1)
    tkinter.Label(root, text="Server Port").grid(row=1, column=0)
    tkinter.Entry(root, textvariable=port).grid(row=1, column=1)
    tkinter.Button(root, text="Connect", command=connect).grid(row=2, column=1)
    tkinter.Label(root, textvariable=status, bd=1, relief=tkinter.SUNKEN, anchor=tkinter.SW)\
        .grid(row=3, sticky=tkinter.EW, columnspan=2)
    """ Exit the program is window is closed """
    root.protocol("WM_DELETE_WINDOW", quit)
    root.mainloop()
    """ Return the socket """
    return client_socket


def handle_user_input(win_, carrom_, max_angle=90, max_speed=40, permit_rotation=False):
    """ Have a clock to control display updates based on user input """
    clock = pygame.time.Clock()

    """ Take user input till user presses space """
    get_user_input = True

    """ The initial striker speed, striker angle, assuming striker is placed at center,
     coins orientation is used if permit rotations it set (only for initial player chance) """
    striker_speed = 0
    striker_angle = 90
    coins_orientation = 60      # Conditional (Initial Orientation)
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
        carrom_.board.show_notification(win_, "Your Turn To Strike")
        carrom_.board.draw_striker_arrow_pointer(win_, carrom_.striker, max_speed)
        pygame.display.flip()

    if permit_rotation:
        """ If rotation was allowed, then return the rotation set by the player"""
        return coins_orientation
    """ Striker position is updated within the carrom object itself"""


# with socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP) as sock:
#     """ Connect to server """
#     # sock.connect(server_address)
with connect_to_server() as sock:
    print("Connected to server")

    """ Obtain the player ID """
    player_data = read_message(sock)
    player_id = int(player_data.decode(encoding))
    player_color = "WHITE" if player_id == 0 else "BLACK"
    print("Obtained player ID:", player_id, "Color:", player_color)
    print("Waiting for opponent to connect..")

    """ Obtain the initial carrom """
    carrom_data = read_message(sock)
    carrom = pickle.loads(carrom_data)
    assert isinstance(carrom, Carrom)
    print("Obtained the initial carrom data, setting up the GUI")

    """ Set up the GUI """
    pygame.init()
    win = pygame.display.set_mode(carrom.board.board.size)
    pygame.display.set_caption("PyCarrom Client: Player " + player_color)

    """ Draw the carrom board, first time """
    carrom.draw(win)
    carrom.board.show_notification(win, "Wait for your turn!")
    pygame.display.update()
    """ Handle the events, else screen is not updated """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            """ If user requested to QUIT, then force quit """
            pygame.quit()
            quit()
    print("Initial GUI is drawn")
    try:
        """ Try catch block to handle graceful shutdown after GUI is up and running """
        """ If it was the first player, then allow rotation of coins from user end """
        if player_id == 0:
            print("Player 0 playing first turn, may setup coin orientation")
            coin_orientation = handle_user_input(win, carrom, permit_rotation=True)
            """ Send the initial coin orientation """
            write_message(sock, str(coin_orientation).encode(encoding))
            """ Send the striker data for updating the simulation """
            striker_data = pickle.dumps(carrom.striker)
            write_message(sock, striker_data)

        """ While game in progress """
        while True:
            """ Read the carrom data """
            carrom_data = read_message(sock)
            carrom = pickle.loads(carrom_data)
            assert isinstance(carrom, Carrom)
            if carrom.game_over:
                print("Game Over....")
                message = "Victory!" if carrom.winner == player_id else "You Lost!"
                break
            if carrom.check_moving() or carrom.player_turn != player_id:
                print("Waiting for opponents turn or for simulation to complete ...")
                """ if it is not current turn to strike, just draw the carrom """
                carrom.draw(win)
                carrom.board.show_notification(win, "Simulating.." if carrom.check_moving() else "Opponent's Move!")
                pygame.display.flip()
                """ Handle the events, else screen is not updated """
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        """ If user requested to QUIT, then force quit """
                        pygame.quit()
                        quit()
            else:
                print("Waiting for user input...")
                """ Current player needs to strike """
                handle_user_input(win, carrom)
                """ Once user set the striker position, then send the striker data to the server """
                striker_data = pickle.dumps(carrom.striker)
                write_message(sock, striker_data)
    except socket.error:
        """ Set the message to indicate connection failure """
        message = "Connection Failed !!"

    """ Display End Game Message or Connection Failed message """
    carrom.draw(win)
    carrom.board.show_notification(win, "Game Over..")
    font = pygame.font.Font('freesansbold.ttf', carrom.board.frame_width)
    text = font.render(message, True, (0, 0, 255))
    text_rect = text.get_rect()
    text_rect.center = carrom.board.board.center
    win.blit(text, text_rect)
    pygame.display.flip()

    """ Handle User Events """
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                """ If user requested to QUIT, then force quit """
                pygame.quit()
                quit()
        pygame.time.delay(100)








