import socket
import os
import threading
import struct


# NOPE, We're doing this ourselves
# from dnsparser import DNSMessage


def validate_header_size(data: bytes) -> bool:
    # per rfc1035 4.1.1, header will be 12 bytes
    return len(data) >= 12


def get_transaction_id(data: bytes) -> int:
    # Make sure header validation done first.
    return (data[0] << 8) | data[1]


def get_flags(data: bytes) -> int:
    # Make sure header validation done first.
    return (data[2] << 8) | data[3]


def is_query(data: bytes):
    flags = get_flags(data)
    # response_filter = 0x8000
    
    # first bit is response field, 0x8000 must be 0 for query
    if (0x8000 & flags) != 0:
        return False
    # opcode_filter = 0x7800, ensure opcode is 0; a standard query
    if (0x7800 & flags) != 0:
        return False
    # truncated filter = 0x0200
    if (0x0200 & flags) != 0:
        return False
    # Z filter 0x0040 = 0?
    if (0x0040 & flags) != 0:
        return False
    return True
    

def get_query_count(data: bytes):
    # Make sure header validation done first.
    return (data[4] << 8) | data[5]


def get_queries(data: bytes):
    queries = []
    count = get_query_count(data)
    offset = 12
    # currently works for 1 query, TODO multiple queries
    if count > 1:
        print("warning, only parsing first query, "
              "multi query not yet implemented")
        count = 1
    while count > 0:
        # also need to parse class and type
        queries.append(get_name(data, offset))
        count -= 1
    return queries


def get_name(data: bytes, offset: int):
    name_array = []
    while data[offset] != 0:
        if (offset + data[offset] + 1) >= len(data):
            return ""
        name_array.append(get_name_section(data, offset))
        offset += data[offset] + 1
    return ".".join(name_array)
    
    
def get_name_section(data: bytes, offset: int) -> str:
    name_length = data[offset]
    return_string = ""
    i = 0
    while i < name_length:
        i += 1
        return_string += chr(data[offset + i])
    return return_string
    
    
# def get_z(data: bytes) -> int(16):
#     # per rfc 1035:4.1.1
#     # Reserved for future use.
#     # Must be zero in all queries and responses.
#     # still accept data arg to keep in standard with other methods and for future maintainability
#     return 0


def main():
    # listen port and ipv4
    # ipv4 = '127.0.0.1'
    ipv4 = ""  # socket.INADDR_ANY  # 0.0.0.0 listen on all interfaces
    port = 53
    # 512 octets or less per rfc1035
    packet_length = 512
    
    dns_records = {
        b'foo.bar.com': b'1.2.3.4'
    }
    
    # we need a socket object, using a context manager
    # AF_INET = ipv4 ONLY!!!
    # AF_INET6 = ipv6, dual stack, not necessarily ipv6 only
    # SOCK_STREAM means that it is a TCP socket.
    # SOCK_DGRAM means that it is a UDP socket. 512 octets or less per rfc1035
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        print(f"attempting to bind socket to local udp port {port}")
        # port bindings,
        # bind relates to the ip and port we want set locally, forms composite address.
        sock.bind((ipv4, port))
        print(f"socket bound:\n\t{sock}\n")
        while True:
            # "https://stackoverflow.com/a/16981944/15528476" \
            # "using struct
            # https://linuxtut.com/en/d0026bc47559320039f2/"
            data, client = sock.recvfrom(packet_length)
            if not validate_header_size(data):
                print("ignoring packet as too small")
                continue
            if not is_query(data):
                print("invalid query, skipping")
                continue
            for query in get_queries(data):
                print(f"client:\t{client}\nquery\t{query}")
            
            sock.sendto(b'127.0.0.1', (client, get_transaction_id(data)))


if __name__ == '__main__':
    main()
