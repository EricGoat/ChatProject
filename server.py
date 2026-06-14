import socket
import sys
import threading

clients = {}
clients_lock = threading.Lock()

def broadcast_message(sender, message):
    with clients_lock:
        for username, sock in clients.items():
            send_response(sock, 200, f"Broadcast\n{sender}\n{message}")

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
                    with clients_lock:
                        clients[username] = data_socket
                    send_response(data_socket, 200)

            elif cmd == "who":
                print("Who requested. Sending users.")

                if username is None:
                    send_response(data_socket or control_socket, 500, "Login first")
                else:
                    with clients_lock:
                        user_list = ", ".join(clients.keys())

                    send_response(control_socket, 200, user_list)

            elif cmd == "broadcast":
                message = arg.strip()
                if username is None:
                    send_response(control_socket, 500, "Login first")
                elif data_socket is None:
                    send_response(control_socket, 500, "Connect first")
                elif message == "":
                    send_response(data_socket, 500, "Missing message")
                else:
                    print(f"Broadcast requested by {username}")
                    print(f"Message: {message}")
                    broadcast_message(username, message)

            elif cmd == "private":
                if username is None:
                    send_response(control_socket, 500, "Login first")
                elif data_socket is None:
                    send_response(control_socket, 500, "Connect first")
                else:
                    try:
                        target_user, message = arg.split(" ", 1)
                        target_user = target_user.strip()
                        message = message.strip()
                    except ValueError:
                        send_response(data_socket, 500, "Usage: private <username> <message>")
                        continue

                    if not target_user or not message:
                        send_response(data_socket, 500, "Missing username or message")
                    else:
                        with clients_lock:
                            target_sock = clients.get(target_user)

                        if not target_sock:
                            send_response(data_socket, 500, "User not found")
                        else:
                            print(f"Private message requested by {username} to {target_user}")
                            print(f"Message: {message}")
                            # Acknowledge the sender
                            send_response(data_socket, 200, "Message Sent.")
                            # Route message to the specific recipient's socket
                            send_response(target_sock, 200, f"Private\n{username}\n{message}")

            elif cmd == "quit":
                print(f"Quit requested by {username}")
                send_response(control_socket, 200)
                break

            else:
                response_socket = data_socket or control_socket
                send_response(response_socket, 500, "Invalid command")

    except OSError:
        return

    finally:
        if username in clients:
            with clients_lock:
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
