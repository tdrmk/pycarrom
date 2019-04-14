# PyCarrom
Python based 2 player carrom game application which can be player across network or on the same machine.
For detailed documentation refer the code.

To play locally run the guigame.py. 

To play remotely run the carrom_server.py to launch the server. 
Run the carrom_client.py to create the clients which will launch the GUI and accept user input.

### Design 
#### coin.py
Defines the carrom men, the queen and the striker and handles the simulation physics.
#### board.py
Defines the carrom board, the layout.
#### carrom.py
Uses the functionality from _coin.py_ and _board.py_ to create a 
functional carrom game with its set of defined rules.

#### guigame.py
Creates a GUI wrapper around carrom.py to play locally.

#### carrom_server.py
Launches a carrom game server, to which clients connects, and handles simulations.

#### carrom_client.py 
Connects to the carrom game server, creates GUI and accepts user input.