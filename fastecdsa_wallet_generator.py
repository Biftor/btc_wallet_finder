import binascii
import hashlib
from fastecdsa import keys, curve

from const import *


def generate_private_key():
    return binascii.hexlify(os.urandom(32)).decode('utf-8').upper()


def private_key_to_public_key(private_key):
    key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
    return '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)


def public_key_to_address(public_key):
    output = []
    alphabet = CHARS
    var = hashlib.new('ripemd160')
    encoding = binascii.unhexlify(public_key.encode())
    var.update(hashlib.sha256(encoding).digest())
    var_encoded = ('00' + var.hexdigest()).encode()
    digest = hashlib.sha256(binascii.unhexlify(var_encoded)).digest()
    var_hex = '00' + var.hexdigest() + hashlib.sha256(digest).hexdigest()[0:8]
    count = [char != '0' for char in var_hex].index(True) // 2
    n = int(var_hex, 16)
    while n > 0:
        n, remainder = divmod(n, 58)
        output.append(alphabet[remainder])
    for i in range(count):
        output.append(alphabet[0])
    return ''.join(output[::-1])


def private_key_to_wif(private_key):
    digest = hashlib.sha256(binascii.unhexlify('80' + private_key)).hexdigest()
    var = hashlib.sha256(binascii.unhexlify(digest)).hexdigest()
    var = binascii.unhexlify('80' + private_key + var[0:8])
    alphabet = chars = CHARS
    value = pad = 0
    result = ''
    for i, c in enumerate(var[::-1]):
        value += 256 ** i * c
    while value >= len(alphabet):
        div, mod = divmod(value, len(alphabet))
        result, value = chars[mod] + result, div
    result = chars[value] + result
    for c in var:
        if c == 0:
            pad += 1
        else:
            break
    return chars[0] * pad + result