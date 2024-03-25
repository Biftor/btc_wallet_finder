import json
import platform
import time

import requests

from const import *


def create_hidden_dir(dir_to_create):
    if not os.path.exists(dir_to_create):
        os.makedirs(dir_to_create)
        # Check if the platform is Windows
        if platform.system() == "Windows":
            try:
                os.system(f"attrib +h {dir_to_create}")
            except Exception as e:
                print(f"Failed to create directory '{dir_to_create}' on Windows:", e)


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
    except Exception as e:
        print(f"Failed to send message.", e)


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
