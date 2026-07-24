#!/usr/bin/env bash
# Start the SERVER (SuperLink) on this machine, with TLS enabled.
#
# Requires that generate_certs.sh has already been run once on
# this machine.
#
# Usage:
#   ./start_superlink.sh
set -euo pipefail

CERT_DIR="./deploy/certificates"

# Default ports:
#   9092 -> Fleet API   (SuperNodes connect here)
#   9093 -> Exec API    (`flwr run` connects here)
FLEET_ADDRESS="${FLEET_ADDRESS:-0.0.0.0:9092}"
EXEC_ADDRESS="${EXEC_ADDRESS:-0.0.0.0:9093}"

if [[ ! -f "$CERT_DIR/ca.crt" || ! -f "$CERT_DIR/server.pem" || ! -f "$CERT_DIR/server.key" ]]; then
  echo "Missing certificates in $CERT_DIR."
  echo "Generate the certificates first with: ./scripts/generate_certs.sh <hostname-or-IP>"
  exit 1
fi

echo "Starting SuperLink with TLS enabled."
echo "Fleet API (clients):  $FLEET_ADDRESS"
echo "Exec API  (flwr run): $EXEC_ADDRESS"

exec flower-superlink \
  --fleet-api-address "$FLEET_ADDRESS" \
  --exec-api-address "$EXEC_ADDRESS" \
  --ssl-ca-certfile "$CERT_DIR/ca.crt" \
  --ssl-certfile "$CERT_DIR/server.pem" \
  --ssl-keyfile "$CERT_DIR/server.key"
