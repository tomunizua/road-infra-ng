#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status.
set -o errexit

# Run Gunicorn. The module is 'api.integrated_backend' 
# and the Flask application object is named 'app'.
gunicorn integrated_backend:app --workers 1