import json
import logging
import os
import time

import requests


def append_json_to_file(json_response, output_json_file):
    # If the output JSON file exists, load its contents
    if os.path.exists(output_json_file):
        with open(output_json_file, 'r') as json_file:
            existing_data = json.load(json_file)
    else:
        existing_data = {}

    # Update existing_data with the new json_response
    existing_data.update(json_response)

    # Write the updated data back to the output JSON file
    with open(output_json_file, 'w') as json_file:
        json.dump(existing_data, json_file)


def parse_addresses(json_response):
    addresses_with_balance_gt_zero = []
    addresses_with_balance_eq_zero = []

    append_json_to_file(json_response, "json_response.json")
    for address, data in json_response.items():
        final_balance = data['final_balance'] / 100000000  # Convert satoshi to bitcoin
        if final_balance > 0:
            addresses_with_balance_gt_zero.append((address, final_balance))
        elif final_balance == 0:
            addresses_with_balance_eq_zero.append((address, final_balance))

    return addresses_with_balance_gt_zero, addresses_with_balance_eq_zero


def check_btc_balance(addresses, retries=3, delay=5):
    # Check the balance of the address
    for attempt in range(retries):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={addresses}")
            json_response = response.json()
            return parse_addresses(json_response=json_response)  # Corrected line
        except Exception as e:
            if attempt < retries - 1:
                logging.error(
                    f"Error checking balance, retrying in {delay} seconds: {str(e)}"
                )
                time.sleep(delay)
            else:
                logging.error("Error checking balance: %s", str(e))
                return None


def check_single_btc_balance(address, retries=3, delay=5):
    # Check the balance of the address
    for attempt in range(retries):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={address}")
            data = response.json()

            balance = data[address]["final_balance"]
            return balance / 100000000  # Convert satoshi to bitcoin
        except Exception as e:
            if attempt < retries - 1:
                logging.error(
                    f"Error checking balance, retrying in {delay} seconds: {str(e)}"
                )
                time.sleep(delay)
            else:
                logging.error("Error checking balance: %s", str(e))
                return -1


def append_line(file_path, line_to_append):
    with open(file_path, 'a') as file:
        file.write(line_to_append + '\n')


def batch_addresses(address_list, batch_size=100):
    batched_addresses = []
    for i in range(0, len(address_list), batch_size):
        batched_addresses.append('|'.join(address_list[i:i + batch_size]))
    return batched_addresses


def split_addresses():
    # Read addresses from the file
    with open("BtcAdress.txt", 'r') as file:
        addresses = [line.strip() for line in file]

    # Batch addresses into groups of 100 and concatenate them with '|'
    batched_addresses = batch_addresses(addresses)

    # Write the batched addresses into a new file
    with open("database/Batched_BtcAddresses.txt", 'w') as batch_file:
        for batch in batched_addresses:
            batch_file.write(batch + '\n')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # split_addresses()
    with open("database/Batched_BtcAddresses.txt", 'r') as file:
        for line in file:
            address = line.strip()
            BTC_balance = check_btc_balance(addresses=address)
            if BTC_balance is None:
                append_line(file_path="error_addresses.txt", line_to_append=address)
            else:
                for address, _ in BTC_balance[0]:
                    append_line(file_path="database/have_btc.txt", line_to_append=address)
                for address, _ in BTC_balance[1]:
                    append_line(file_path="no_btc.txt", line_to_append=address)
