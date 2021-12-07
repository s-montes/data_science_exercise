#!/bin/bash

if [ "$1" == "build_venv" ]
then
    mkdir -p ./.venv
    python3 -m venv ./.venv
    source ./.venv/bin/activate
    python -m pip install -r ./requirements.txt
    pre-commit install
elif [ "$1" == "clean_data" ]
then
    echo "Clean data!"
elif [ "$1" == "experiment_report" ]
then
    echo "Create experiment report!"
elif [ "$1" == "estimate_percentage" ]
then
    echo "Estimate percentage increase!"
else
    echo "Bad option"
fi
