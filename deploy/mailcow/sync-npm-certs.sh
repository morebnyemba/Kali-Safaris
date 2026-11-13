#!/usr/bin/env bash
# Copy the Let's Encrypt certificate that Nginx Proxy Manager issued for
# mail.kalaisafaris.com into mailcow, so SMTP/IMAP (which NPM can't proxy)
# present the same valid certificate. Restarts mailcow's TLS services only
# when the certificate actually changed. Safe to run from cron daily.
#
#   ./sync-npm-certs.sh                      # finds NPM's certificate for MAIL_HOSTNAME itself
#   NPM_CERT_ID=3 ./sync-npm-certs.sh        # or name it (3 = npm-3 on NPM's SSL Certificates page)
set -euo pipefail

NPM_CONTAINER="${NPM_CONTAINER:-whatsappcrm_npm}"
MAIL_HOSTNAME="${MAIL_HOSTNAME:-mail.kalaisafaris.com}"
if [ -z "${NPM_CERT_ID:-}" ] || ! [[ "$NPM_CERT_ID" =~ ^[0-9]+$ ]]; then
  # Newest NPM certificate whose names include MAIL_HOSTNAME.
  NPM_CERT_ID=""
  for dir in $(docker exec "$NPM_CONTAINER" ls /etc/letsencrypt/live/ | grep -E '^npm-[0-9]+$' | sort -t- -k2 -n); do
    if docker exec "$NPM_CONTAINER" cat "/etc/letsencrypt/live/$dir/fullchain.pem" \
        | openssl x509 -noout -ext subjectAltName 2>/dev/null | grep -qw "DNS:$MAIL_HOSTNAME"; then
      NPM_CERT_ID="${dir#npm-}"
    fi
  done
  if [ -z "$NPM_CERT_ID" ]; then
    echo "Nginx Proxy Manager has no certificate for $MAIL_HOSTNAME yet." >&2
    echo "Create the proxy host (mail.kalaisafaris.com -> https nginx-mailcow:8443) with 'Request a new SSL Certificate', then run this again." >&2
    exit 1
  fi
  echo "Using NPM certificate npm-$NPM_CERT_ID for $MAIL_HOSTNAME"
fi
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
