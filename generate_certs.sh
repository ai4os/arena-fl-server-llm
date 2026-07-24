#!/usr/bin/env bash
# Generate a self-signed CA and a server certificate for TLS.
# Run this ONCE, on the server machine.
#
# Usage example:
#   ./generate_certs.sh localhost
#
# After running it:
#   - deploy/certificates/ca.crt      -> copy this to EVERY client machine
#   - deploy/certificates/server.pem  -> stays on the server
#   - deploy/certificates/server.key  -> stays on the server (secret, do not share)
set -euo pipefail

SERVER_NAME="${1:?Usage: ./generate_certs.sh <server-hostname-or-IP>}"
CERT_DIR="./deploy/certificates"
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# 1. Own certificate authority (CA)
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -sha256 -days 3650 -out ca.crt \
  -subj "/CN=arena-fl-server-ca"

# 2. Server certificate, signed by the CA above
openssl genrsa -out server.key 4096
openssl req -new -key server.key -out server.csr \
  -subj "/CN=$SERVER_NAME"

# Use the correct subjectAltName type depending on whether SERVER_NAME is
# an IP address or a hostname
if [[ "$SERVER_NAME" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  SAN_ENTRY="IP:$SERVER_NAME"
else
  SAN_ENTRY="DNS:$SERVER_NAME"
fi

cat > server.ext <<EXT
subjectAltName = $SAN_ENTRY
EXT

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.pem -days 825 -sha256 \
  -extfile server.ext

rm -f server.csr server.ext ca.srl

echo ""
echo "Certificates generated in $CERT_DIR:"
echo "  ca.crt      -> copy this file to EVERY client machine"
echo "  server.pem  -> stays on the server"
echo "  server.key  -> stays on the server (do NOT share this)"
