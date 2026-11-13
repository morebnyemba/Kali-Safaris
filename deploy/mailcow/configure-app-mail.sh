#!/usr/bin/env bash
# Point the Kalai Safaris app at the mailcow mailbox:
#   - asks for the bookings@ mailbox password (hidden; never in shell history or command lines);
#   - checks it really logs in to SMTP (587) and IMAP (993) before changing anything;
#   - writes EMAIL_* / MAIL_IMAP_* / DEFAULT_FROM_EMAIL into whatsappcrm_backend/.env.prod
#     (backup kept, file made root-only), single-quoted so Docker Compose never mangles
#     special characters like $ , & =;
#   - recreates the app containers that read it and sends a test email.
#
#   cd ~/Kali-Safaris && ./deploy/mailcow/configure-app-mail.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="$REPO_DIR/whatsappcrm_backend/.env.prod"
MAIL_HOST="${MAIL_HOST:-mail.kalaisafaris.com}"
MAILBOX="${MAILBOX:-bookings@kalaisafaris.com}"

[ -f "$ENV_FILE" ] || { echo "Missing $ENV_FILE" >&2; exit 1; }
read -rsp "Password for $MAILBOX: " MAIL_PASS; echo
[ -n "$MAIL_PASS" ] || { echo "Empty password." >&2; exit 1; }
case "$MAIL_PASS" in *"'"*) echo "Please choose a password without a single quote (')." >&2; exit 1;; esac
read -rp "Send the test email to: " TEST_TO

echo "== Checking the mailbox logs in (SMTP 587 + IMAP 993)…"
MAIL_HOST="$MAIL_HOST" MAILBOX="$MAILBOX" MAIL_PASS="$MAIL_PASS" python3 - <<'PY'
import imaplib, os, smtplib, ssl, sys
host, user, password = os.environ['MAIL_HOST'], os.environ['MAILBOX'], os.environ['MAIL_PASS']
def ctx():
    try:
        c = ssl.create_default_context()
        with smtplib.SMTP(host, 587, timeout=20) as s:
            s.starttls(context=c)
        return c, True
    except ssl.SSLError:
        return ssl._create_unverified_context(), False
c, trusted = ctx()
if not trusted:
    print("  ! Certificate on mail ports isn't trusted yet: run sync-npm-certs.sh (Step 5). Checking login anyway.")
try:
    with smtplib.SMTP(host, 587, timeout=20) as s:
        s.starttls(context=c); s.login(user, password)
    print("  SMTP login OK")
    with imaplib.IMAP4_SSL(host, 993, ssl_context=c, timeout=20) as m:
        m.login(user, password)
    print("  IMAP login OK")
except Exception as exc:
    sys.exit(f"  Login failed: {exc}\n  Nothing was changed. Check the mailbox exists in mailcow and the password.")
PY

echo "== Updating $ENV_FILE"
cp -p "$ENV_FILE" "$ENV_FILE.bak.$(date +%Y%m%d-%H%M%S)"
ENV_FILE="$ENV_FILE" MAIL_HOST="$MAIL_HOST" MAILBOX="$MAILBOX" MAIL_PASS="$MAIL_PASS" python3 - <<'PY'
import os, re, sys
path, host, user = os.environ['ENV_FILE'], os.environ['MAIL_HOST'], os.environ['MAILBOX']
password = os.environ['MAIL_PASS']
values = {
    'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    'EMAIL_HOST': host, 'EMAIL_PORT': '587', 'EMAIL_USE_TLS': 'True',
    'EMAIL_HOST_USER': user, 'EMAIL_HOST_PASSWORD': password,
    'DEFAULT_FROM_EMAIL': f'Kalai Safaris <{user}>',
    'PUBLIC_SITE_URL': 'https://kalaisafaris.com',
    'MAIL_IMAP_HOST': host, 'MAIL_IMAP_USER': user, 'MAIL_IMAP_PASS': password,
}
lines = open(path).read().splitlines()
seen = set()
for i, line in enumerate(lines):
    m = re.match(r'\s*(?:export\s+)?([A-Z_][A-Z0-9_]*)\s*=', line)
    if m and m.group(1) in values:
        key = m.group(1)
        lines[i] = f"{key}='{values[key]}'"
        seen.add(key)
missing = [k for k in values if k not in seen]
if missing:
    lines += ['', '# Mail (mailcow), set by deploy/mailcow/configure-app-mail.sh']
    lines += [f"{k}='{values[k]}'" for k in missing]
open(path, 'w').write('\n'.join(lines) + '\n')
print(f"  {len(seen)} updated, {len(missing)} added")
PY
chmod 600 "$ENV_FILE"
unset MAIL_PASS

echo "== Recreating app containers that read .env.prod"
cd "$REPO_DIR"
SERVICES=$(docker compose config --services | grep -E '^(backend|celery|email_idle_fetcher)' | tr '\n' ' ')
docker compose up -d --force-recreate $SERVICES

echo "== Sending a test email to $TEST_TO"
sleep 10
docker compose exec -T backend python manage.py sendtestemail "$TEST_TO" && echo "  Sent. Check the inbox (and spam folder)."
docker compose logs --tail 5 email_idle_fetcher 2>/dev/null | sed 's/^/  idle fetcher: /' || true
