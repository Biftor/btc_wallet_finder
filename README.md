
## First time you have to install its dependencies
`pip install -r requirements.txt`

## on macOS:

## First install 

`brew install gmp `

## To find path of gmp.h

`find / -name "gmp.h" -print 2>/dev/null `

## Then install dependencies

`CFLAGS="-I/usr/local/include/ -I/usr/local/Cellar/gmp/6.3.0/include/" LDFLAGS="-L/usr/local/lib/ -L/usr/local/Cellar/gmp/6.3.0/lib/" pip install -r requirements.txt
`
# Just run it now
`python main.py`

# Prams:

`cores` number of cpu cores
`max_wallets` number wallet generation each time (default is 100)
`verbose` print the addresses
`time` time of process(create, check wallets)
if you want to omit checking wallets in time process you can pass `check_wallets=0` to combine with time

`python main.py check_wallets=0 time`

# Env Prams:
Additionally, you can add your own telegram bot in case if any wallet found send a message to you,
create an env file named `prams.env`
with these values `TG_BOT_TOKEN` and `TG_CHAT_ID`

# To make package
`pyinstaller --add-data "includes/wordlist/*.txt:bip_utils/bip/bip39/wordlist" --onefile  main.py`

Windows:
`pyinstaller --add-data "includes/wordlist/*.txt:bip_utils/bip/bip39/wordlist" --add-data "includes/libsecp256k1.dll:coincurve" --onefile  main.py`

# Enjoy!