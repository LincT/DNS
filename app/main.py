import socket
import sys


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
    sbe_0_flags = 0x8000  # first bit is response field, sbe 0 for query
    sbe_0_flags |= 0x7800  # opcode_filter = 0x7800 , 0=std query
    sbe_0_flags |= 0x0200  # truncated filter = 0x0200
    sbe_0_flags |= 0x0040  # Z filter 0x0040 = 0?
    
    # check if flags and filters pass validation
    return (get_flags(data) & sbe_0_flags) == 0
    

def get_query_count(data: bytes):
    # Make sure header validation done first.
    return (data[4] << 8) | data[5]


def get_queries(data: bytes):
    queries = []
    count = get_query_count(data)
    offset = 12
    # currently works for 1 query, TODO multiple queries
    if count != 1:
        print("warning, only parsing first query, "
              "multi query not yet implemented")
        count = 1
    while count > 0:
        # also need to parse class and q_type
        name, offset = get_name(data, offset)
        q_type = get_query_ip_type(data, offset)
        queries.append((name, q_type))
        count -= 1
    return {'queries': queries, 'offset': offset + 4}


def get_name(data: bytes, offset: int) -> (str, int):
    name_array = []
    while data[offset] != 0:
        if (offset + data[offset] + 1) >= len(data):
            return ""
        name_array.append(get_name_section(data, offset))
        offset += data[offset] + 1
    return ".".join(name_array), offset + 1
    
    
def get_query_ip_type(data: bytes, offset: int):
    # check both class and type
    types = {0x1: "A", 0x1c: "AAAA"}
    q_type = data[offset] << 8 | data[offset + 1]
    q_class = data[offset + 2] << 8 | data[offset + 3]
    if q_class != 1:  # 1 = IN, we don't care about other types atm
        return None
    return types.get(q_type, None)

    
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
    # ipv4 = ""  # socket.INADDR_ANY  # 0.0.0.0 listen on all interfaces
    # env based config, windows is dev machine, anything else assume stage or prod (both linux systems)
    ipv4 = "" if sys.platform == 'win32' else "159.223.128.28"  # listen on public addr
    port = 53
    # 512 octets or less per rfc1035
    packet_length = 512

    # TODO wire in rdmbs or other config that can be updated without server restarts
    dns_records = {
        'foo.bar.com': '1.2.3.4',
        'a.test.thornmire.com': '1.2.3.4',
        'b.test.thornmire.com': '5.6.7.8',
        'test.thornmire.com': '159.223.128.28'
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
            data, client = sock.recvfrom(packet_length)
            if not validate_header_size(data):
                print("ignoring packet as too small")
                continue
            if not is_query(data):
                print("invalid query, skipping")
                continue
                
            queries = get_queries(data)
            for query in queries.get('queries'):
                
                print(f"client:\t{client}\n"
                      f"transaction id: {get_transaction_id(data)}\n"
                      f"is_query: {is_query(data)}\n"
                      f"query\t{query}")
                
                if query[1] != "A":
                    continue
                    
                dns_lookup = dns_records.get(query[0], None)
                print(f"dns_result: {dns_lookup}")
                if dns_lookup:
                    
                    data = bytearray(data)  # copy into writeable buffer
                    # update original data
                    data[2] |= 0x80  # flip first bit from 0 (q) to 1 (r)
                    
                    data[2] |= 0x04  # authoritative response
                    
                    data[7] = 0x01  # set answer count to 1
                    offset = queries.get('offset') + 1
                    if len(data) > offset:  # handling for additional rr
                        if data[offset] != 0:
                            data[offset] = 0
                            data = data[0:-offset]
                    # append answer
                    data.append(0xc0)    # first bits need to be 1's to indicate ptr
                    data.append(0x0c)    # append pointer to name
                    data.append(0x00)    # padding for type
                    data.append(0x01)    # append type
                    data.append(0x00)    # padding for class
                    data.append(0x01)    # append class
                    data.append(0x00)    # padding for ttl
                    data.append(0x00)    # padding for ttl
                    data.append(0x00)    # padding for ttl
                    data.append(0x0a)    # append ttl as 32 bit int
                    data.append(0x00)    # padding for data length
                    data.append(0x04)    # sbe 4 the size of an ipv4 addr is 4 bytes / 32 bits
                    for each in dns_lookup.split("."):
                        data.append(int(each))
                    
                    # print(data)
                    # send response
                    sock.sendto(data, client)
                else:
                    # send packet back
                    # sock.sendto(b'127.0.0.1', (client, get_transaction_id(data)))
                    data = bytearray(data)  # copy into writeable buffer
                    # update original data
                    data[2] |= 0x80  # flip first bit in flags from 0 (q) to 1 (r)
                    data[3] |= 0x03  # flip last bits in flags to 1 to indicate no answer
                    # send rejection
                    sock.sendto(data, client)


if __name__ == '__main__':
    main()
