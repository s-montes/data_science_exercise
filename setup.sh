#!/bin/bash

if [ "$1" == "build" ]
then
    mkdir -p ./.venv
    python3 -m venv ./.venv
    source ./.venv/bin/activate
    python -m pip install -r ./requirements.txt
    pre-commit install
fi
