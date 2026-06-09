import socket
import sys
import threading

clients = {}


def make_response(code, data=""):
    if data:
        return f"{code}\n\n{data}\n"
    return f"{code}\n\n"


def send_response(sock, code, data=""):
    sock.sendall(make_response(code, data).encode())


def handle_client(control_socket):
    data_socket = None
    username = None
    data_listener = None

    try:
        while True:
            command = control_socket.recv(1024).decode().strip()

            if not command:
                break

            parts = command.split(" ", 1)
            cmd = parts[0]
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "connect":
                print("Connection requested. Creating data socket")

                data_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_listener.bind(("", 0))
                data_listener.listen(1)

                data_port = data_listener.getsockname()[1]
                send_response(control_socket, 200, str(data_port))

                data_socket, _ = data_listener.accept()
                data_listener.close()
                data_listener = None

            elif cmd == "login":
                username = arg.strip()
                print(f"Login requested by: {username}")

                if data_socket is None:
                    send_response(control_socket, 500, "Connect first")

                elif username == "":
                    send_response(data_socket, 500, "Missing username")

                elif username in clients:
                    send_response(data_socket, 500, "Username already taken")

                else:
                    clients[username] = data_socket
                    send_response(data_socket, 200)

            else:
                response_socket = data_socket or control_socket
                send_response(response_socket, 500, "Invalid command")

    except OSError:
        return

    finally:
        if username in clients:
            del clients[username]

        control_socket.close()

        if data_listener:
            data_listener.close()

        if data_socket:
            data_socket.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        return

    port = int(sys.argv[1])

    print("Starting server…")
    print("Creating server socket")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", port))
    server_socket.listen(5)

    print("Awaiting connections…")

    while True:
        control_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(control_socket,)).start()


if __name__ == "__main__":
    main()
