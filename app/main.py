import socket
import os
import threading


def receive():
    pass


def send():
    pass


def main():
    # listen port and ipv4
    # ipv4 = '127.0.0.1'
    ipv4 = ""  # socket.INADDR_ANY  # 0.0.0.0 listen on all interfaces
    port = 53
    dns_records = {
        b'foo.bar.com': b'1.2.3.4'
    }
    
    # we need a socket object, using a context manager
    # AF_INET = ipv4 ONLY!!!
    # AF_INET6 = ipv6, dual stack, not necessarily ipv6 only
    # SOCK_STREAM means that it is a TCP socket.
    # SOCK_DGRAM means that it is a UDP socket.
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        print(f"attempting to bind socket to local udp port {port}")
        # port bindings,
        # bind relates to the ip and port we want set locally, forms composit address.
        sock.bind((ipv4, port))
        print(f"socket bound:\n\t{sock}\n")
        while True:
            data, client = sock.recvfrom(10240)
            addr = [each for each in data.split(b'\x00') if (each != b'')]
            print(f"{client}\nbytes: {data}\n"
                  f"hex:{data.hex()}\n"
                  # f"{addr!r}\n"
                  # f"{addr}"
                  )
            
            print(f"query: {str(addr[2], 'UTF-8')}")
            if not data:
                break
            # sock.sendall(dns_records[data])


if __name__ == '__main__':
    main()
