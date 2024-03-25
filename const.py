import multiprocessing
import os
import sys

def get_app_directory():
    if getattr(sys, 'frozen', False):
        # If the application is frozen (i.e., compiled into an executable),
        # return the directory containing the executable.
        return os.path.dirname(sys.executable)
    else:
        # If the application is not frozen, return the current working directory.
        return os.path.dirname(os.path.abspath(__file__))


directory = get_app_directory()
cache_directory = os.path.join(directory, ".wallet_finder_caches")
config_file = f'{cache_directory}/config.json'
defaults_params = {
    'verbose': 0,
    'max_wallets': 400,
    'cores': multiprocessing.cpu_count(),
    'check_wallets': 1,
    'method': 1,
    'tg_bot_token': None,
    'tg_user_id': None,
    'user_wallet_address': None
}

# CHARS = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# Base58 CHARS
CHARS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
