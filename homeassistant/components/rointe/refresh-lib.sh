#!/bin/sh

# Refreshes the python lib

pip uninstall --no-input -y  rointe-sdk
pip install  --no-cache-dir ~/projects/homeassistant/rointe-sdk
