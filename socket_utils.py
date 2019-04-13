import socket


def receive(conn: socket.socket, num_bytes):
    """ Receive num_bytes from a connection """
    data = bytes()
    while num_bytes > 0:
        new_data = conn.recv(num_bytes)
        if not new_data:
            raise IOError("Failed to receive data")
        data += new_data
        num_bytes -= len(new_data)
        # print("Got total:", len(data), "current:", len(new_data))
    return data


def read_message(conn: socket.socket):
    """ Receive message from length prefixed channel """
    message_header = receive(conn, 4)

    message_length = int.from_bytes(message_header, byteorder='big', signed=False)
    # print("Message Header:", message_header)
    # print("Message Length:", message_length)
    message = receive(conn, message_length)
    # print("Received:", message)
    return message


def write_message(conn: socket.socket, message: bytes):
    """ Send length prefixed frame """
    message_header = len(message).to_bytes(length=4, byteorder='big', signed=False)
    # print("Write Message Header:", message_header, "Len:", len(message), "headerLen:", len(message_header))
    # print("Expected:", int.from_bytes(message_header, byteorder='big', signed=False))
    conn.sendall(message_header + message)

