import json

import requests
from dotenv import load_dotenv
from fastecdsa import keys, curve
from ellipticcurve.privateKey import PrivateKey
import platform
import multiprocessing
import hashlib
import binascii
import os
import sys
import time

HELPS = '''
Speed test: 
execute 'python3 main.py time', the output will be the time it takes to bruteforce a single address in seconds
to full check you can pass check_wallets=1 it will check wallets too


Quick start: run command 'python3 main.py'

By default this program runs with parameters:
python3 main.py verbose=0

verbose: must be 0 or 1. If 1, then every bitcoin address that gets bruteforce will be printed to the terminal. This 
has the potential to slow the program down. An input of 0 will not print anything to the terminal and the 
bruteforce will work silently. By default verbose is 0.

max_count: Maximum number of wallet generation and send for test

cores: number of cores to run concurrently. More cores = more resource usage but faster bruteforce. Omit this 
parameter to run with the maximum number of cores'''

directory = os.path.dirname(os.path.abspath(__file__))

ENV_FILE_NAME = "params.env"
env_file_path = os.path.join(directory, ENV_FILE_NAME)

load_dotenv(env_file_path)

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")


def generate_private_key():
    return binascii.hexlify(os.urandom(32)).decode('utf-8').upper()


def private_key_to_public_key(private_key, fastecdsa):
    if fastecdsa:
        key = keys.get_public_key(int('0x' + private_key, 0), curve.secp256k1)
        return '04' + (hex(key.x)[2:] + hex(key.y)[2:]).zfill(128)
    else:
        pk = PrivateKey().fromString(bytes.fromhex(private_key))
        return '04' + pk.publicKey().toString().hex().upper()


def public_key_to_address(public_key):
    output = []
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
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
    alphabet = chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
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


def send_telegram_message(bot_token, chat_id, message):
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    except:
        pass


def parse_addresses_with_btc(json_response):
    addresses_with_balance_gt_zero = []

    with open('btc_wallets.json', 'w') as json_file:
        json.dump(json_response, json_file, indent=4)
    for w_address, data in json_response.items():
        final_balance = data['final_balance'] / 100000000  # Convert satoshi to bitcoin
        if final_balance > 0:
            addresses_with_balance_gt_zero.append({
                w_address: data,
            })
        else:
            return None

    return addresses_with_balance_gt_zero


def check_btc_balance(addresses, retries=3, delay=10):
    # Check the balance of the address
    for attempt in range(retries):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={addresses}")
            json_response = response.json()
            return parse_addresses_with_btc(json_response=json_response)
        except Exception as e:
            if attempt < retries - 1:
                print(
                    f"Error checking balance, retrying in {delay} seconds: {str(e)}"
                )
                time.sleep(delay)
            else:
                print("Error checking balance: %s", str(e))
                return None


def append_json_to_file(json_response, output_json_file):
    # If the output JSON file exists, load its contents
    if os.path.exists(output_json_file):
        with open(output_json_file, 'r') as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = []

    # Parse the JSON response into a dictionary
    new_data = json.loads(json_response)

    # Append the new data to the existing data
    existing_data.append(new_data)

    # Write the updated data back to the output JSON file
    with open(output_json_file, 'w') as json_file:
        json.dump(existing_data, json_file, indent=2)


def create_and_check_wallets(params, check=True):
    wallets = []
    max_generate = params["max_count"]
    count = 0
    addresses = ''
    while count < max_generate:
        wallet_hex_private_key = generate_private_key()
        wallet_public_key = private_key_to_public_key(wallet_hex_private_key, params['fastecdsa'])
        wallet_wif = private_key_to_wif(wallet_hex_private_key)
        wallet_uncompressed_address = public_key_to_address(wallet_public_key)
        if params['verbose']:
            print(wallet_uncompressed_address)
        wallets.append({
            "private_key": wallet_hex_private_key,
            "public_key": wallet_public_key,
            "wif": wallet_wif,
            "address": wallet_uncompressed_address
        })
        count += 1
        if count < max_generate:
            addresses += wallet_uncompressed_address + "|"
        else:
            addresses += wallet_uncompressed_address

    with open('wallets.json', 'w') as json_file:
        json.dump(wallets, json_file, indent=4)

    if check:
        checked_wallets = check_btc_balance(addresses)
        if checked_wallets is not None:
            for w_balance_address in checked_wallets:
                for w_address, data in w_balance_address.items():  # Corrected unpacking
                    for wallet in wallets:
                        if wallet['address'] == w_address:
                            w_private_key = wallet["private_key"]
                            w_public_key = wallet["public_key"]
                            w_wif = wallet["wif"]
                            balance = data["final_balance"]
                            tg_message = str('hex private key: ' + str(w_private_key) + '\n' +
                                             'WIF private key: ' + str(w_wif) + '\n' +
                                             'public key: ' + str(w_public_key) + '\n' +
                                             'uncompressed wallet address: ' + str(w_address) + '\n' +
                                             'balance: ' + str(balance))
                            if TG_BOT_TOKEN and TG_CHAT_ID:
                                send_telegram_message(bot_token=TG_BOT_TOKEN, chat_id=TG_CHAT_ID, message=tg_message)

                            print(f"Found Wallet:{tg_message}\n")
                            wallet["balance"] = balance
                            append_json_to_file(json_response=json.dumps(wallet, indent=4),
                                                output_json_file="found_wallets.json")
                            break


def main(params):
    while True:
        create_and_check_wallets(params)


def print_help():
    print(HELPS)
    sys.exit(0)


def timer(params):
    start = time.time()
    check_w = params["check_wallets"] == "1"
    print(params["check_wallets"])
    create_and_check_wallets(params=params, check=check_w)
    end = time.time()
    print(str(end - start))
    sys.exit(0)


if __name__ == '__main__':
    args = {
        'verbose': 0,
        'max_count': 400,
        'cores': multiprocessing.cpu_count(),
        'check_wallets': 1,
        'fastecdsa': platform.system() in ['Linux', 'Darwin'],
    }

    for arg in sys.argv[1:]:
        command = arg.split('=')[0]
        if command == 'help':
            print_help()
        elif command == 'time':
            timer(args)
        elif command == 'max_count':
            max_count = int(arg.split('=')[1])
            if 0 < max_count:
                args['max_count'] = max_count
            else:
                print('invalid input. max_count must be greater than 0')
                sys.exit(-1)
        elif command == 'cores':
            cpu_count = int(arg.split('=')[1])
            if 0 < cpu_count <= multiprocessing.cpu_count():
                args['cores'] = cpu_count
            else:
                print('invalid input. cores must be greater than 0 and less than or equal to ' + str(
                    multiprocessing.cpu_count()))
                sys.exit(-1)
        elif command == 'verbose':
            verbose = arg.split('=')[1]
            if verbose in ['0', '1']:
                args['verbose'] = verbose
            else:
                print('invalid input. verbose must be 0(false) or 1(true)')
                sys.exit(-1)
        elif command == 'check_wallets':
            check_wallets = arg.split('=')[1]
            if check_wallets in ['0', '1']:
                args['check_wallets'] = check_wallets
            else:
                print('invalid input. check_wallets must be 0(false) or 1(true)')
                sys.exit(-1)
        else:
            print('invalid input: ' + command + '\nrun `python3 main.py help` for help')
            sys.exit(-1)

    print('processes spawned: ' + str(args['cores']))

    for cpu in range(args['cores']):
        multiprocessing.Process(target=main, args=(args,)).start()
