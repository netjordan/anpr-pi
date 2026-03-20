#!/bin/bash -e

install -d "${ROOTFS_DIR}/opt/anpr-pi"
cp -a "${STAGE_DIR}/files/opt/anpr-pi/." "${ROOTFS_DIR}/opt/anpr-pi/"
install -m 0644 "${STAGE_DIR}/files/opt/anpr-pi/config.example.yaml" "${ROOTFS_DIR}/opt/anpr-pi/config.yaml"
install -m 0644 "${STAGE_DIR}/files/opt/anpr-pi/services/anpr-pi.service" "${ROOTFS_DIR}/etc/systemd/system/anpr-pi.service"

on_chroot <<'EOF'
set -e
python3 -m venv --system-site-packages /opt/anpr-pi/.venv
/opt/anpr-pi/.venv/bin/pip install --upgrade pip
/opt/anpr-pi/.venv/bin/pip install --no-deps /opt/anpr-pi
chown -R pi:pi /opt/anpr-pi
systemctl enable anpr-pi.service
EOF
