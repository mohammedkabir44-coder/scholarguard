#!/usr/bin/env bash
set -o errexit

# Install Python dependencies from backend directory
pip install --upgrade pip
pip install -r backend/requirements.txt