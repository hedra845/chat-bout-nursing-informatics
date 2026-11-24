#!/bin/bash
# Production startup script
# Run with: gunicorn -w 4 -b 0.0.0.0:5000 app:app

gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} app:app