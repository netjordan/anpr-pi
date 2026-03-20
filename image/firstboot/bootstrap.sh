#!/bin/bash
set -euo pipefail

MARKER_FILE="/opt/anpr-pi/.bootstrapped"

if [ -f "${MARKER_FILE}" ]; then
  exit 0
fi

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-opencv \
  python3-yaml \
  sqlite3 \
  sox \
  libsox-fmt-all \
  alsa-utils \
  openalpr \
  openalpr-daemon \
  openalpr-utils

python3 -m venv --system-site-packages /opt/anpr-pi/.venv
/opt/anpr-pi/.venv/bin/python -m pip install --no-deps /opt/anpr-pi

if [ ! -f /opt/anpr-pi/config.yaml ]; then
  cp /opt/anpr-pi/config.example.yaml /opt/anpr-pi/config.yaml
fi

touch "${MARKER_FILE}"
chown -R pi:pi /opt/anpr-pi

systemctl daemon-reload
systemctl enable anpr-pi.service
systemctl start anpr-pi.service
