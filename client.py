import socket
import threading

control_socket = None
data_socket = None

def read_response(sock):
    data = sock.recv(1024).decode()

    if "\n\n" in data:
        code, body = data.split("\n\n", 1)
        return code.strip(), body.strip()

    return data.strip(), ""

def receive_messages():
    while True:
        code, body = read_response(data_socket)
        if not code:
            break

        if code == "200":
            if body.startswith("Broadcast\n"):
                _, sender, message = body.split("\n", 2)
                print("\r200 status code received.")
                print(f"Broadcast from {sender}: {message}")
                print("> ", end="", flush=True)
            elif body.startswith("Private\n"):
                _, sender, message = body.split("\n", 2)
                print("\r200 status code received.")
                print(f"Private from {sender}: {message}")
                print("> ", end="", flush=True)
            elif body == "Message Sent.":
                print(f"\r200 status code received. {body}")
                print("> ", end="", flush=True)
        else:
            print("500 status code received.")
            if body:
                print(body)
                print("> ", end="", flush=True)

def main():
    global control_socket
    global data_socket

    print("Starting client…")

    while True:
        user_input = input("> ").strip()

        if user_input == "":
            continue

        parts = user_input.split(" ", 2)
        command = parts[0]

        if command == "connect":
            if len(parts) < 3:
                print("Usage: connect <ip> <port>")
                continue

            server_ip = parts[1]
            control_port = int(parts[2])

            control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            control_socket.connect((server_ip, control_port))

            control_socket.sendall(b"connect\n")

            code, body = read_response(control_socket)

            if code == "200":
                data_port = int(body)
                print(f"200 status code received. Starting data connection on port {data_port}")

                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.connect((server_ip, data_port))
            else:
                print("500 status code received. Connection failed")

        elif command == "login":
            if control_socket is None or data_socket is None:
                print("Connect to a server first")
                continue

            control_socket.sendall((user_input + "\n").encode())

            code, body = read_response(data_socket)

            if code == "200":
                print("200 status code received. Login successful")
                threading.Thread(target=receive_messages, daemon=True).start()
            else:
                print("500 status code received.")
                if body:
                    print(body)

        elif command == "who":
            if control_socket is None or data_socket is None:
                print("Connect to a server first")
                continue

            control_socket.sendall((user_input + "\n").encode())

            code, body = read_response(control_socket)

            if code == "200":
                print(f"200 status code received. Users currently connected: {body}")
            else:
                print("500 status code received.")
                if body:
                    print(body)
        
        elif command == "broadcast":
            if control_socket is None or data_socket is None:
                print("Connect to a server first")
                continue

            control_socket.sendall((user_input + "\n").encode())
            
        elif command == "private":
            if control_socket is None or data_socket is None:
                print("Connect to a server first")
                continue

            if len(parts) < 3:
                print("Usage: private <username> <message>")
                continue

            control_socket.sendall((user_input + "\n").encode())

        elif command == "quit":
            if control_socket is None or data_socket is None:
                print("Connect to a server.")
                continue
            control_socket.sendall((user_input + "\n").encode())
            code, body = read_response(control_socket)
            if code == "200":
                print("200 status code received.")
            break

        else:
            print("Invalid command")

    if control_socket:
        control_socket.close()

    if data_socket:
        data_socket.close()

if __name__ == "__main__":
    main()
