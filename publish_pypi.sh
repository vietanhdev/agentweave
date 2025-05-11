#!/bin/bash

# Remove existing builds
rm -rf dist/
rm -rf build/
rm -rf *.egg-info

# Build the package
python -m build

# Upload to PyPI
python -m twine upload dist/*
