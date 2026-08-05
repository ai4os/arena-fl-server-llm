#!/usr/bin/env bash
# Install this project's Flower Configuration file (SuperLink connections)
# to the location Flower's CLI reads it from ($FLWR_HOME/config.toml,
# defaulting to root/.flwr/config.toml).
#
# Run this once after a new session start, before `flwr run`.
#
# Usage:
#   ./install_flwr_config.sh
set -euo pipefail

FLWR_CONFIG_DIR="${FLWR_HOME:-$HOME/.flwr}"
SOURCE="$(cd "$(dirname "$0")/.." && pwd)/arena-fl-server-llm/deploy/config.toml"

mkdir -p "$FLWR_CONFIG_DIR"
cp "$SOURCE" "$FLWR_CONFIG_DIR/config.toml"

echo "Installed Flower Configuration file to $FLWR_CONFIG_DIR/config.toml"
flwr config list