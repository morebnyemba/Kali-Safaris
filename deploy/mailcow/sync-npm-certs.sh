#!/usr/bin/env bash
# Copy the Let's Encrypt certificate that Nginx Proxy Manager issued for
# mail.kalaisafaris.com into mailcow, so SMTP/IMAP (which NPM can't proxy)
# present the same valid certificate. Restarts mailcow's TLS services only
# when the certificate actually changed. Safe to run from cron daily.
#
#   NPM_CERT_ID=3 ./sync-npm-certs.sh        # 3 = the NPM certificate id (SSL Certificates page)
set -euo pipefail

NPM_CONTAINER="${NPM_CONTAINER:-whatsappcrm_npm}"
NPM_CERT_ID="${NPM_CERT_ID:?Set NPM_CERT_ID to the NPM certificate id (e.g. 3 for npm-3)}"
MAILCOW_DIR="${MAILCOW_DIR:-/opt/mailcow-dockerized}"
SSL_DIR="$MAILCOW_DIR/data/assets/ssl"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# -L follows the live/ -> archive/ symlinks inside the NPM container.
docker cp -L "$NPM_CONTAINER:/etc/letsencrypt/live/npm-$NPM_CERT_ID/fullchain.pem" "$TMP/cert.pem"
docker cp -L "$NPM_CONTAINER:/etc/letsencrypt/live/npm-$NPM_CERT_ID/privkey.pem" "$TMP/key.pem"

# Refuse to install something that isn't a matching cert/key pair.
openssl x509 -in "$TMP/cert.pem" -noout -subject >/dev/null
if [ "$(openssl x509 -in "$TMP/cert.pem" -noout -pubkey | sha256sum)" != "$(openssl pkey -in "$TMP/key.pem" -pubout | sha256sum)" ]; then
  echo "Certificate and key don't match; not installing." >&2
  exit 1
fi

if cmp -s "$TMP/cert.pem" "$SSL_DIR/cert.pem" && cmp -s "$TMP/key.pem" "$SSL_DIR/key.pem"; then
  echo "mailcow certificate already up to date."
  exit 0
fi

install -m 0644 "$TMP/cert.pem" "$SSL_DIR/cert.pem"
install -m 0600 "$TMP/key.pem" "$SSL_DIR/key.pem"
cd "$MAILCOW_DIR"
docker compose restart postfix-mailcow dovecot-mailcow nginx-mailcow
echo "mailcow certificate updated: $(openssl x509 -in "$SSL_DIR/cert.pem" -noout -enddate)"
