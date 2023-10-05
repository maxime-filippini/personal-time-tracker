import argparse
from unittest import defaultTestLoader
from timetracker.server import run

parser = argparse.ArgumentParser()
parser.add_argument("--port", action="store", default="8000")
args = parser.parse_args()

run(port=int(args.port))
