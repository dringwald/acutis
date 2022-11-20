#!/bin/bash

cd /home/dringwa/acutis
/home/dringwa/acutis/venv/bin/gunicorn --bind 0.0.0.0:5000 "acutisapi.app:app"

