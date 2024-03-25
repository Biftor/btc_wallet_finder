import sys
from cx_Freeze import setup, Executable

base = None

setup(
    name="BTC Finder",
    version="1.0",
    description="Nothing Fancy",
    executables=[Executable("main.py", base=base)]
)