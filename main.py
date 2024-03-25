import json
import platform

import requests
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum, Bip39SeedGenerator, Bip44Coins, Bip44, Bip44Changes
from dotenv import load_dotenv
from fastecdsa import keys, curve
from ellipticcurve.privateKey import PrivateKey
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


Quick start: run command 'python main.py'

By default this program runs with parameters:
python main.py verbose=0

verbose: must be 0 or 1. If 1, then every bitcoin address that gets bruteforce will be printed to the terminal. This 
has the potential to slow the program down. An input of 0 will not print anything to the terminal and the 
bruteforce will work silently. By default verbose is 0.

max_wallets: Maximum number of wallet generation and send for test

method: There are 2 methods 1 is using private key and 2 is using seed phrases

cores: number of cores to run concurrently. More cores = more resource usage but faster bruteforce. Omit this 
parameter to run with the maximum number of cores'''

directory = os.path.dirname(os.path.abspath(__file__))
cache_directory = str(directory) + '/.wallet_finder_caches'

ENV_FILE_NAME = "params.env"
env_file_path = os.path.join(directory, ENV_FILE_NAME)

load_dotenv(env_file_path)

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# CHARS = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# Base58 CHARS
CHARS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


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


def bip():
    # Generate a 12-word BIP39 mnemonic
    return Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)


def bip44_btc_seed_to_address(seed):
    # Generate the seed from the mnemonic
    seed_bytes = Bip39SeedGenerator(seed).Generate()

    # Generate the Bip44 object
    bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)

    # Generate the Bip44 address (account 0, change 0, address 0)
    bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
    bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
    bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)

    # Print the address
    return bip44_addr_ctx.PublicKey().ToAddress()


def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        params = {
            "chat_id": TG_CHAT_ID,
            "text": message
        }
        response = requests.post(url, params=params)
        if response.status_code == 200:
            print("Message sent successfully.")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    except:
        pass


def parse_addresses_with_btc(json_response, process_index, method):
    addresses_with_balance_gt_zero = []

    with open(f'{cache_directory}/{method}_{process_index}btc_wallets.json', 'w') as json_file:
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


def check_btc_balance(addresses, process_index, method, retries=10, delay=10):
    # Check the balance of the address
    for attempt in range(retries):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={addresses}")
            json_response = response.json()
            return parse_addresses_with_btc(process_index=process_index, json_response=json_response, method=method)
        except Exception as e:
            if attempt < retries - 1:
                error = f"Error checking balance, retrying in {delay} seconds: {str(e)}"
                print(
                    error
                )
                if TG_BOT_TOKEN and TG_CHAT_ID:
                    send_telegram_message(message=error)
                time.sleep(delay * attempt)
            else:
                error = f"Error checking balance: {str(e)}"
                print(
                    error
                )
                if TG_BOT_TOKEN and TG_CHAT_ID:
                    send_telegram_message(message=error)
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


def method1(params, wallets):
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
    return wallet_uncompressed_address


def method2(params, wallets):
    seed = bip()
    wallet_uncompressed_address = bip44_btc_seed_to_address(seed)
    if params['verbose']:
        print(seed)
    wallets.append({
        "seed": str(seed),
        "address": wallet_uncompressed_address
    })
    return wallet_uncompressed_address


def checked_wallets_balance(checked_wallets, wallets, method, process_index):
    if checked_wallets is not None:
        for w_balance_address in checked_wallets:
            for w_address, data in w_balance_address.items():
                for wallet in wallets:
                    if wallet['address'] == w_address:
                        if method == 1:
                            w_private_key = wallet["private_key"]
                            w_public_key = wallet["public_key"]
                            w_wif = wallet["wif"]
                            balance = data["final_balance"]
                            tg_message = str('hex private key: ' + str(w_private_key) + '\n' +
                                             'WIF private key: ' + str(w_wif) + '\n' +
                                             'public key: ' + str(w_public_key) + '\n' +
                                             'uncompressed wallet address: ' + str(w_address) + '\n' +
                                             'balance: ' + str(balance))
                        else:
                            seed = data["seed"]
                            balance = data["final_balance"]
                            tg_message = str('seed: ' + str(seed) + '\n' +
                                             'uncompressed wallet address: ' + str(w_address) + '\n' +
                                             'balance: ' + str(balance))
                        if TG_BOT_TOKEN and TG_CHAT_ID:
                            send_telegram_message(message=tg_message)

                        print(f"Found Wallet:{tg_message}\n")
                        wallet["balance"] = balance
                        append_json_to_file(json_response=json.dumps(wallet, indent=4),
                                            output_json_file=f'{cache_directory}/{method}_{process_index}found_wallets.json')
                        break


def create_and_check_wallets(params, process_index, check=True):
    wallets = []
    max_generate = params["max_wallets"]
    method = params['method']
    count = 0
    addresses = ''
    while count < max_generate:
        if method == 1:
            wallet_uncompressed_address = method1(params=params, wallets=wallets)
        else:
            wallet_uncompressed_address = method2(params=params, wallets=wallets)

        count += 1
        if count < max_generate:
            addresses += wallet_uncompressed_address + "|"
        else:
            addresses += wallet_uncompressed_address

    with open(f'{cache_directory}/{method}_{process_index}wallets.json', 'w') as json_file:
        json.dump(wallets, json_file, indent=4)

    if check:
        checked_wallets = check_btc_balance(addresses=addresses, process_index=process_index, method=method)
        checked_wallets_balance(checked_wallets=checked_wallets, wallets=wallets, method=method,
                                process_index=process_index)


def main(params, process_index):
    while True:
        create_and_check_wallets(params=params, process_index=process_index)


def print_help():
    print(HELPS)
    sys.exit(0)


def timer(params):
    start = time.time()
    check_w = params["check_wallets"] == "1"
    print(params["check_wallets"])
    create_and_check_wallets(params=params, check=check_w, process_index="")
    end = time.time()
    print(str(end - start))
    sys.exit(0)


def create_cache_dir():
    if not os.path.exists(cache_directory):
        os.makedirs(cache_directory)
        # Check if the platform is Windows
        if platform.system() == "Windows":
            try:
                os.system(f"attrib +h {cache_directory}")
            except Exception as e:
                print(f"Failed to create directory '{cache_directory}' on Windows:", e)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    create_cache_dir()

    args = {
        'verbose': 0,
        'max_wallets': 400,
        'cores': multiprocessing.cpu_count(),
        'check_wallets': 1,
        'fastecdsa': True,
        'method': 1,
    }

    for arg in sys.argv[1:]:
        command = arg.split('=')[0]
        if command == 'help':
            print_help()
        elif command == 'time':
            timer(args)
        elif command == 'max_wallets':
            max_wallets = int(arg.split('=')[1])
            if 0 < max_wallets:
                args['max_wallets'] = max_wallets
            else:
                print('invalid input. max_wallets must be greater than 0')
                sys.exit(-1)
        elif command == 'cores':
            cpu_count = int(arg.split('=')[1])
            if 0 < cpu_count <= multiprocessing.cpu_count():
                args['cores'] = cpu_count
            elif 0 < cpu_count > multiprocessing.cpu_count():
                print('Warning you have selected more that actual number of cores which is ' + str(
                    multiprocessing.cpu_count()) + ' this may freeze slowdown your computer')
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
        elif command == 'method':
            selected_method = int(arg.split('=')[1])
            if selected_method in [1, 2]:
                args['method'] = selected_method
            else:
                print('invalid input. method must be 1(false) or 2(true)')
                sys.exit(-1)
        else:
            print('invalid input: ' + command + '\nrun `python3 main.py help` for help')
            sys.exit(-1)

    if args['cores'] > 1:
        index = 0
        print('processes spawned: ' + str(args['cores']))
        for cpu in range(args['cores']):
            index += 1
            index_string = str(index) + "_"
            multiprocessing.Process(target=main, args=(args, index_string)).start()
    else:
        main(params=args, process_index="")
