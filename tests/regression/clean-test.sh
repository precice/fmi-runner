#!/bin/sh
set -e -u

rm -rfv ./output/test-result-fmi.csv
rm -rfv ./output/test-result-python.csv
rm -rfv ./precice-run/
rm -rfv *events.json
rm -rfv *.log
