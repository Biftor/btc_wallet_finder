import multiprocessing

from bip_wallet_generator import *
from fastecdsa_wallet_generator import *
from utils import *


def method1(params, wallets):
    wallet_hex_private_key = generate_private_key()
    wallet_public_key = private_key_to_public_key(wallet_hex_private_key)
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


def parse_and_validate_args():
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


if __name__ == '__main__':
    multiprocessing.freeze_support()
    create_hidden_dir(cache_directory)

    args = {
        'verbose': 0,
        'max_wallets': 400,
        'cores': multiprocessing.cpu_count(),
        'check_wallets': 1,
        'method': 1,
    }
    parse_and_validate_args()

    if args['cores'] > 1:
        index = 0
        print('processes spawned: ' + str(args['cores']))
        for cpu in range(args['cores']):
            index += 1
            index_string = str(index) + "_"
            multiprocessing.Process(target=main, args=(args, index_string)).start()
    else:
        main(params=args, process_index="")
