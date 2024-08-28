#!/bin/bash
# Connect to a game control server running locally.

export PYTHONPATH=".":$PYTHONPATH
python src/client_connect.py --host=127.0.0.1
