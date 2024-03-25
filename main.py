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


def method3(params, wallets):
    seed = bip24()
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
        wallet_uncompressed_address = ""
        if method == 1:
            wallet_uncompressed_address = method1(params=params, wallets=wallets)
        elif method == 2:
            wallet_uncompressed_address = method2(params=params, wallets=wallets)
        elif method == 3:
            wallet_uncompressed_address = method3(params=params, wallets=wallets)

        count += 1
        if count < max_generate:
            addresses += wallet_uncompressed_address + "|"
        else:
            addresses += wallet_uncompressed_address

    with open(f'{cache_directory}/{method}_{process_index}wallets.json', 'w') as json_file:
        json.dump(wallets, json_file, indent=4)

    if check:
        checked_wallets = check_btc_balance(addresses=addresses, process_index=process_index, params=params)
        checked_wallets_balance(checked_wallets=checked_wallets, wallets=wallets, process_index=process_index,
                                params=params)


def timer(params):
    start = time.time()
    check_w = params["check_wallets"] == 1
    create_and_check_wallets(params=params, check=check_w, process_index="")
    end = time.time()
    print(str(end - start))
    input()


def asks_for_input(params):
    print("Enter parameters. Press Enter to keep the current value.")

    params['verbose'] = int(
        input("Enter verbose value (0 or 1) [default %d]: " % params.get('verbose', 0)) or params.get('verbose', 0))
    params['max_wallets'] = int(
        input("Enter max_wallets value [default %d]: " % params.get('max_wallets', 400)) or params.get('max_wallets',
                                                                                                       400))
    params['cores'] = int(
        input("Enter number of cores [default %d]: " % params.get('cores', multiprocessing.cpu_count())) or params.get(
            'cores', multiprocessing.cpu_count()))
    params['check_wallets'] = int(
        input("Enter check_wallets value (0 or 1) [default %d]: " % params.get('check_wallets', 1)) or params.get(
            'check_wallets', 1))
    params['method'] = int(
        input("Enter method value (1, 2 or 3) [default %d]: " % params.get('method', 1)) or params.get('method', 1))
    params['tg_bot_token'] = input(
        "Enter Telegram Bot Token [default %s]: " % params.get('tg_bot_token', '') or params.get('tg_bot_token',
                                                                                                 '')) or None
    params['tg_user_id'] = input(
        "Enter Telegram User ID [default %s]: " % params.get('tg_user_id', '') or params.get('tg_user_id', '')) or None
    params['user_wallet_address'] = input(
        "Enter User Wallet Address [default %s]: " % params.get('user_wallet_address', '') or params.get(
            'user_wallet_address', '')) or ""
    check_wallets_string = ""
    if str(params['check_wallets']) == "1":
        check_wallets_string = " and check"
    check_time = input(f"Do you want check process to generate{check_wallets_string} {str(params['max_wallets'])} wallets time? (y/n): ")
    if check_time.lower() == "y":
        timer(params=params)

    print("Press Enter to start...")
    input()
    return params


def parse_and_validate_args():
    _params = defaults_params.copy()  # Initialize _params with default values
    stored_params = None
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            stored_params = json.load(f)
            print("Config file exists with the following settings:")
            print(json.dumps(stored_params, indent=4))

    # Check if config file exists
    if os.path.exists(config_file):
        if len(sys.argv) < 1:
            change_config = input("Do you want to change the settings? (y/n): ")
            if change_config.lower() == "y":
                # Prompt the user for input
                _params.clear()
                _params = asks_for_input(params=stored_params).copy()

                # Write _params to config file
                with open(config_file, 'w') as f:
                    json.dump(_params, f)
                return _params
            else:
                print("Press Enter to start...")
                input()
                return stored_params

    # Check for command-line arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if "=" not in arg:
                return _params
            command, value = arg.split('=')
            if command == 'verbose':
                _params['verbose'] = int(value)
            elif command == 'max_wallets':
                _params['max_wallets'] = int(value)
            elif command == 'cores':
                _params['cores'] = int(value)
            elif command == 'check_wallets':
                _params['check_wallets'] = int(value)
            elif command == 'method':
                _params['method'] = int(value)
            elif command == 'tg_bot_token':
                _params['tg_bot_token'] = str(value)
            elif command == 'tg_user_id':
                _params['tg_user_id'] = str(value)
            elif command == 'user_wallet_address':
                _params['user_wallet_address'] = str(value)

        # Write _params to config file
        with open(config_file, 'w') as f:
            json.dump(_params, f)
    else:
        # Prompt the user for input
        if stored_params:
            _params.clear()
            _params = asks_for_input(params=stored_params).copy()
        else:
            _params = asks_for_input(params=_params).copy()

        # Write _params to config file
        with open(config_file, 'w') as f:
            json.dump(_params, f)

    return _params


def main(params, process_index):
    if params['cores'] > 1:
        try:
            while True:
                create_and_check_wallets(params=params, process_index=process_index)
        except:
            pass
    else:
        while True:
            create_and_check_wallets(params=params, process_index=process_index)


def start_multi_process(cores):
    _processes = []
    for cpu in range(cores):
        index_string = str(cpu + 1) + "_"
        _process = multiprocessing.Process(target=main, args=(args, index_string))
        _process.start()
        _processes.append(_process)

    for p in _processes:
        p.join()
    return _processes


def start_app(params):
    _processes = []
    try:
        if params['cores'] > 1:
            _processes.clear()
            _processes = start_multi_process(params['cores'])
        else:
            main(params=params, process_index="")
    except KeyboardInterrupt:
        print("\nTerminating processes...")
        for process in _processes:
            process.terminate()
        print("\nProgram interrupted. Press Enter to restart or Ctrl+C to exit.")
        try:
            input()
            start_app(params=args)
        except KeyboardInterrupt:
            print("\nExiting program.")
            sys.exit(0)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    create_hidden_dir(cache_directory)
    args = parse_and_validate_args()
    try:
        start_app(params=args)
    except:
        pass
