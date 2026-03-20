# Raspberry Pi ANPR Recorder

This project runs a local ANPR pipeline on a Raspberry Pi with a USB webcam. It:

- captures frames from the camera
- calls a local ANPR engine through the `alpr` CLI
- records plate sightings in SQLite
- plays a sound when a plate has been seen before
- infers the most likely country for UK and EU plates from engine hints plus plate-format heuristics
- can be baked into a Raspberry Pi OS image artifact through GitHub Actions for direct flashing to an SD card

## What This Uses

The code is designed around the OpenALPR CLI being installed on the Raspberry Pi.

Why:

- it is practical on a Pi
- it works fully offline
- it already handles plate localization and OCR
- it is a better fit than trying to ship a full detector and OCR stack in this empty workspace without model files

## Limits

No offline OCR stack will perfectly identify every plate format in every EU country from format rules alone. This code combines:

- the ANPR engine result
- country and region hints from the engine
- heuristics for UK and EU formats

That gets you a usable system, but some countries have overlapping formats, so ambiguous cases are marked with lower confidence or `unknown`.

## Raspberry Pi Setup

These commands are intended to run on the Pi, not on this Mac workspace.

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-opencv python3-yaml sqlite3 sox libsox-fmt-all alsa-utils
sudo apt install -y openalpr openalpr-daemon openalpr-utils
```

If your distro packages for OpenALPR are poor or missing EU runtime data, install/build OpenALPR separately and confirm this works:

```bash
alpr -h
```

### 2. Python environment

```bash
cd /opt/anpr-pi
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

If you want to stay fully on distro packages for OpenCV and YAML on Raspberry Pi OS, install into a virtual environment with access to system packages:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install --upgrade pip
pip install . --no-deps
```

### 3. Config

Copy the sample config:

```bash
cp config.example.yaml config.yaml
```

Edit it for your camera, storage path, and preferred sound behavior.

### 4. Run

```bash
source .venv/bin/activate
anpr-pi --config config.yaml
```

## Files Produced

- SQLite database: configurable, default `./data/anpr.db`
- snapshots: configurable, default `./data/snapshots/`
- repeat alert tone: generated automatically if missing

## systemd

Example service file:

[`services/anpr-pi.service`](./services/anpr-pi.service)

Adjust paths before installing:

```bash
sudo cp services/anpr-pi.service /etc/systemd/system/anpr-pi.service
sudo systemctl daemon-reload
sudo systemctl enable --now anpr-pi.service
```

## Prebuilt SD Card Image

The repository includes a GitHub Actions workflow that downloads an official Raspberry Pi OS Lite image, injects this project into it, and prepares a first-boot bootstrap service.

What the image does:

- starts from Raspberry Pi OS Lite
- copies this project into `/opt/anpr-pi`
- enables SSH and writes the default `pi` user password hash into the boot partition
- installs a first-boot bootstrap service
- on first boot, installs OpenALPR and runtime dependencies
- creates `/opt/anpr-pi/config.yaml` from the sample config
- installs and enables `anpr-pi.service`
- boots directly into the ANPR service on first startup

Build output:

- compressed image artifact: `anpr-pi-image-*.img.xz`
- SHA256 checksum file

Workflow:

[`/.github/workflows/build-raspi-image.yml`](./.github/workflows/build-raspi-image.yml)

## Important Assumptions For The Image

- target OS base: Raspberry Pi OS Lite
- default webcam device: `/dev/video0`
- service user: `pi`
- no desktop UI is installed
- SSH is enabled in the baked image
- the default local password in the baked image is `raspberry`; change it immediately on first login if you keep using the image

One constraint matters here: OpenALPR is not built into Raspberry Pi OS. The baked image installs it on first boot. If the upstream package disappears or changes in a later Raspberry Pi OS release, the bootstrap script will need a small adjustment.

## Querying Seen Plates

```sql
SELECT plate_text, country_code, sightings_count, first_seen_at, last_seen_at
FROM vehicles
ORDER BY last_seen_at DESC;
```
