import codecs
# todo make this work
byte_str = '000a010000010000000000000178027979037a7a7a0000010001'
plain = codecs.decode(byte_str, 'hex')
print(plain)
