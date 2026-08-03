#!/usr/bin/env bash
# Start the SERVER (SuperLink) on this machine, for deployments where
# Traefik terminates TLS at the edge with a public certificate (the
# "Federated LLM Server" template on this platform routes fedserver-<uuid>:443
# to this container's port 5000.
#
# No certificates are generated or managed here -- Traefik already
# presents a publicly-trusted certificate to clients. The SuperLink itself
# runs without TLS, since traffic between Traefik and this container stays
# inside the platform's internal network.
#
# Usage:
#   ./start_superlink_traefik.sh
set -euo pipefail

# Fleet API: SuperNodes connect here (via Traefik, on :443 externally).
# This MUST be port 5000 to match this deployment's
# fedserver-<uuid>:443 -> :5000 route.
FLEET_ADDRESS="${FLEET_ADDRESS:-0.0.0.0:5000}"

# Exec/Control API: only `flwr run` running inside this same container
# needs to reach this. Loopback only, never exposed externally.
EXEC_ADDRESS="${EXEC_ADDRESS:-127.0.0.1:9093}"

echo "Starting SuperLink WITHOUT TLS (Traefik terminates TLS at the edge)."
echo "Fleet API (behind Traefik, reachable via fedserver-<uuid>:443): $FLEET_ADDRESS"
echo "Exec API  (local only, for flwr run):                           $EXEC_ADDRESS"

exec flower-superlink \
  --insecure \
  --fleet-api-address "$FLEET_ADDRESS" \
  --exec-api-address "$EXEC_ADDRESS"