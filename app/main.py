import socket
import os
import threading


def receive():
    pass


def send():
    pass


def main():
    ipv4 = '127.0.0.1'
    port = 53
    dns_records = {
        b'foo.bar.com': b'1.2.3.4'
    }
    
    # we need a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        print(f"socket created")
        # port bindings
        server_socket.bind((ipv4, port))
        print(f"socket binding:\n\t{server_socket}\n")
        print(f"starting listen on:\n\t{socket.gethostname()}:{port}")
        server_socket.listen()
        client_socket, client_ipv4 = server_socket.accept()
        with client_socket:
            print(f"connection from \n\t{client_ipv4}")
            while True:
                data = client_socket.recv(1024)
                print(data)
                if not data:
                    break
                client_socket.sendall(dns_records[data])


if __name__ == '__main__':
    main()
