# mailcow for kalaisafaris.com, served through Nginx Proxy Manager

mailcow hosts the mailboxes (`bookings@`, `reservation@`); Nginx Proxy Manager (NPM,
already in `docker-compose.yml`) serves its web UI and webmail over HTTPS on 443.

**How the pieces fit**

| Traffic | Goes to | Why |
|---|---|---|
| `https://mail.kalaisafaris.com` (admin UI, SOGo webmail, autodiscover) | NPM :443 → `nginx-mailcow:8080` over mailcow's Docker network | NPM already owns 80/443 |
| SMTP 25 / 465 / 587, IMAP 143 / 993, POP3 110 / 995, Sieve 4190 | mailcow directly | NPM only proxies HTTP; mail ports must be published by mailcow |
| TLS certificate | NPM issues it; `sync-npm-certs.sh` copies it into mailcow | one Let's Encrypt cert for web *and* mail; mailcow's own ACME is off (it can't answer challenges behind NPM) |

## 0. Before you start (these decide whether mail gets delivered)

```bash
# Outbound port 25 must be open. Many VPS providers block it until you ask.
nc -vz -w 5 gmail-smtp-in.l.google.com 25      # must say "succeeded"/"open"

free -h                                         # mailcow wants ~6 GB RAM (+ swap); ~4 GB with ClamAV off (step 2)
docker compose version                          # needs Compose v2
```

- **Reverse DNS (PTR).** In your VPS provider's panel (Contabo: *Customer Panel → Reverse DNS Management*), set the server IP's PTR to `mail.kalaisafaris.com` once the `mail` A record exists. Without it, Gmail/Outlook will spam-folder you.
- **Swap.** The app already uses ~4.5 GB of this 8 GB server; add 4 GB swap so mailcow can't trigger the out-of-memory killer:
  ```bash
  sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- **IPv6.** If `ip -6 route show default` prints nothing, the server has no IPv6: set `ENABLE_IPV6=false` in `mailcow.conf` (step 2), or mailcow's network won't come up.
- **Existing mailboxes.** If `@kalaisafaris.com` mail lives somewhere today (e.g. cPanel), don't change MX until you've copied it: mailcow → *Mailboxes → Sync jobs* pulls old mail over IMAP.

## 1. Install mailcow

```bash
cd /opt
sudo git clone https://github.com/mailcow/mailcow-dockerized
cd mailcow-dockerized
sudo ./generate_config.sh        # hostname: mail.kalaisafaris.com, timezone: Africa/Harare
```

## 2. Point mailcow's web server behind NPM

Edit `/opt/mailcow-dockerized/mailcow.conf`:

```ini
MAILCOW_HOSTNAME=mail.kalaisafaris.com
# NPM owns 80/443: keep mailcow's web server off the public interface.
HTTP_PORT=8080
HTTP_BIND=127.0.0.1
HTTPS_PORT=8443
HTTPS_BIND=127.0.0.1
# NPM issues the certificate (synced in step 5); mailcow's ACME can't work behind it.
SKIP_LETS_ENCRYPT=y
ADDITIONAL_SERVER_NAMES=autodiscover.kalaisafaris.com,autoconfig.kalaisafaris.com
TZ=Africa/Harare
# Optional, saves ~1.5 GB RAM (no antivirus scanning of attachments):
SKIP_CLAMD=y
```

```bash
sudo docker compose pull
sudo docker compose up -d
```

## 3. Let NPM reach mailcow

NPM runs in the app's compose project, so attach it to mailcow's network (from the repo root):

```bash
cd /path/to/Kali-Safaris
docker compose -f docker-compose.yml -f docker-compose.mailcow.yml up -d npm
docker exec whatsappcrm_npm getent hosts nginx-mailcow    # must print an IP
```

(Use the same two `-f` files whenever you run `up` for `npm` from now on, or the extra network is dropped.)

## 4. DNS records (at your DNS provider)

| Type | Name | Value |
|---|---|---|
| A | `mail` | your server IP |
| MX | `@` | `mail.kalaisafaris.com` (priority 10) |
| CNAME | `autodiscover` | `mail.kalaisafaris.com` |
| CNAME | `autoconfig` | `mail.kalaisafaris.com` |
| TXT | `@` | `v=spf1 mx a ~all` (switch to `-all` once everything sends through mailcow) |
| TXT | `dkim._domainkey` | copy from mailcow → *Configuration → ARC/DKIM keys* (after step 6) |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:postmaster@kalaisafaris.com` (raise to `p=quarantine` after 2 clean weeks) |
| SRV | `_autodiscover._tcp` | `0 1 443 mail.kalaisafaris.com` |

## 5. NPM proxy host + certificate

NPM admin (`http://SERVER_IP:81`) → **Hosts → Proxy Hosts → Add**:

- **Domain names:** `mail.kalaisafaris.com`, `autodiscover.kalaisafaris.com`, `autoconfig.kalaisafaris.com`
- **Scheme / host / port:** `http` · `nginx-mailcow` · `8080`
- Tick **Block Common Exploits** and **Websockets Support**
- **SSL tab:** *Request a new SSL certificate*, **Force SSL**, **HTTP/2**, agree to the Let's Encrypt terms
- **Advanced tab** (big webmail attachments):
  ```nginx
  client_max_body_size 0;
  proxy_read_timeout 300s;
  ```

Then give mailcow the same certificate for SMTP/IMAP. Find the certificate's id under **SSL Certificates** (hover → `npm-3` means id 3):

```bash
sudo NPM_CERT_ID=3 /path/to/Kali-Safaris/deploy/mailcow/sync-npm-certs.sh

# Keep it in sync after NPM's automatic renewals (daily at 04:23):
( sudo crontab -l 2>/dev/null; echo "23 4 * * * NPM_CERT_ID=3 /path/to/Kali-Safaris/deploy/mailcow/sync-npm-certs.sh >> /var/log/mailcow-cert-sync.log 2>&1" ) | sudo crontab -
```

## 6. Domain and mailboxes

`https://mail.kalaisafaris.com/admin` (default `admin` / `moohoo`: **change it immediately** and turn on 2FA):

1. *Configuration → Mail setup → Domains → Add* `kalaisafaris.com`.
2. *Mailboxes → Add*: `bookings@` (the app sends from it and reads partner documents from it) and `reservation@` (customers reply here).
3. *Configuration → ARC/DKIM keys*: generate for `kalaisafaris.com` (2048-bit), copy the TXT into DNS (step 4).

## 7. Point the app at mailcow

In `whatsappcrm_backend/.env.prod`:

```ini
EMAIL_HOST=mail.kalaisafaris.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=bookings@kalaisafaris.com
EMAIL_HOST_PASSWORD=<bookings mailbox password>
DEFAULT_FROM_EMAIL=Kalai Safaris <bookings@kalaisafaris.com>
PUBLIC_SITE_URL=https://kalaisafaris.com

MAIL_IMAP_HOST=mail.kalaisafaris.com
MAIL_IMAP_USER=bookings@kalaisafaris.com
MAIL_IMAP_PASS=<bookings mailbox password>
```

```bash
docker compose up -d --force-recreate backend celery_default_worker celery_message_worker celery_beat email_idle_fetcher
docker compose exec backend python manage.py sendtestemail you@gmail.com
docker compose exec backend python manage.py preview_emails --out /app/email-previews   # every branded email, as HTML
```

## 8. Check deliverability

```bash
# Ports reachable from outside (run from another machine):
for p in 25 465 587 993; do nc -vz -w 5 mail.kalaisafaris.com $p; done
# Certificate on SMTP is the NPM one, valid for mail.kalaisafaris.com:
openssl s_client -connect mail.kalaisafaris.com:465 -servername mail.kalaisafaris.com </dev/null 2>/dev/null | openssl x509 -noout -subject -enddate
```

Send a test from webmail to the address on https://www.mail-tester.com and aim for 9/10+. Check SPF, DKIM and DMARC all pass, and that the PTR matches.

## Backups and updates

```bash
cd /opt/mailcow-dockerized
sudo MAILCOW_BACKUP_LOCATION=/opt/backups/mailcow ./helper-scripts/backup_and_restore.sh backup all   # cron this nightly, copy off-server
sudo ./update.sh                                                                                       # monthly
```
