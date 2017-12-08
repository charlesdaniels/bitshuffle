#!/usr/bin/python3

import argparse
import requests

VERSION = 1.0

parser = argparse.ArgumentParser(description='all-in-one tool for downloading and checking internet files')

parser.add_argument("--username", "-u")
parser.add_argument("--password", "-p")
parser.add_argument("--port", "-P", action="store_const", const=443))
parser.add_argument("url")


