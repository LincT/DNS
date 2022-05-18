from app import main

my_bytes = bytes([0x1a, 0xb9])

assert main.get_transaction_id(my_bytes) == 6841
my_bytes = bytes([0xff, 0xff])
assert main.get_transaction_id(my_bytes) == 65535
