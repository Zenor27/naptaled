import asyncio
from argparse import ArgumentParser

from src.helpers.control import connect_to_server

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--host", default="192.168.128.175")
    args = parser.parse_args()

    asyncio.run(connect_to_server(args.host))
