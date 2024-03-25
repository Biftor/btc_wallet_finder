import os
import sys

from dotenv import load_dotenv

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

ENV_FILE_NAME = "params.env"
env_file_path = os.path.join(directory, ENV_FILE_NAME)

load_dotenv(env_file_path)

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
# CHARS = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# Base58 CHARS
CHARS = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
