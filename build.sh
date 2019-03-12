#!/bin/bash

# -e: exit immediately on errors
# -u: treat unset variables as errors
# -o pipefail: exit if any command in pipeline fails
set -euo pipefail

NOW=$(date +%Y%m%d-%H%M%S)
LOGFILE=build/build-$NOW.log

echo "Running build process"
echo "Logfile: $LOGFILE"

mkdir -p build
echo "Build starting at $(date)" > $LOGFILE

echo -e "\nChecking Pipenv environment is installed..." | tee -a $LOGFILE
pipenv sync 2>&1 | tee -a $LOGFILE

echo -e "\nInstalled versions:" | tee -a $LOGFILE
pipenv run pip freeze 2>&1 | tee -a $LOGFILE

echo -e "\nRunning make" | tee -a $LOGFILE
make 2>&1 | tee -a $LOGFILE

echo -e "\nChecking data package" | tee -a $LOGFILE
pipenv run goodtables datapackage.json 2>&1 | tee -a $LOGFILE

echo "Build finished at $(date)" >> $LOGFILE
