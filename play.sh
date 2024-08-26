#!/bin/bash
# Connect to a game control server running on the Raspberry Pi.

export PYTHONPATH=".":$PYTHONPATH
python src/client_connect.py
