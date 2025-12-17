# Deployment Guide for kalaisafaris.com

This guide provides step-by-step instructions for deploying the kalaisafaris.com public website.

## Overview

The kalaisafaris.com website is a Next.js application that runs in a Docker container and is served through either Nginx Proxy Manager or a static nginx reverse proxy.

## Prerequisites

- Docker and Docker Compose installed
- Domain name (kalaisafaris.com) pointing to your server's IP address
- Port 80 and 443 open on your firewall

## Deployment Options

### Option 1: Using Nginx Proxy Manager (Recommended)

This is the easiest option as it provides a web UI for managing SSL certificates and proxy configurations.

#### Step 1: Start the Services

```bash
cd /path/to/Kali-Safaris
docker-compose up -d public-website npm
```

#### Step 2: Access Nginx Proxy Manager

1. Open your browser and navigate to `http://your-server-ip:81`
2. Default login credentials:
   - Email: `admin@example.com`
   - Password: `changeme`
3. Change the default password immediately

#### Step 3: Configure the Proxy

1. In NPM, go to "Proxy Hosts" and click "Add Proxy Host"
2. Fill in the details:
   - **Domain Names**: `kalaisafaris.com`, `www.kalaisafaris.com`
   - **Scheme**: `http`
   - **Forward Hostname / IP**: `public-website`
   - **Forward Port**: `3000`
   - Enable "Cache Assets" and "Websockets Support"
3. Go to the "SSL" tab:
   - Select "Request a new SSL Certificate with Let's Encrypt"
   - Enable "Force SSL"
   - Agree to Let's Encrypt Terms
   - Enter your email address
4. Click "Save"

NPM will automatically obtain and configure SSL certificates from Let's Encrypt.

### Option 2: Using Static Nginx Configuration

If you prefer to use a static nginx configuration instead of NPM:

#### Step 1: Obtain SSL Certificates

```bash
# Install certbot if not already installed
apt-get update
apt-get install certbot python3-certbot-nginx

# Stop NPM if it's running (to free up port 80)
docker-compose stop npm

# Obtain certificates
certbot certonly --standalone -d kalaisafaris.com -d www.kalaisafaris.com
```

#### Step 2: Configure Nginx

The nginx configuration in `nginx_proxy/nginx.conf` is already set up. You just need to:

1. Ensure the SSL certificate paths are correct
2. Mount the letsencrypt directory in your nginx container
3. Start nginx with the configuration

#### Step 3: Deploy

```bash
# Build and start the public-website
docker-compose up -d --build public-website

# If using a separate nginx container, start it
docker-compose up -d nginx
```

## Troubleshooting

### Issue: 504 Gateway Timeout

**Symptoms**: The website loads slowly or returns 504 errors.

**Solutions**:
1. Check if the public-website container is running:
   ```bash
   docker ps | grep public-website
   ```

2. Check the container logs:
   ```bash
   docker logs public_website_app
   ```

3. Verify the container is healthy:
   ```bash
   docker inspect public_website_app | grep -A 10 Health
   ```

4. Restart the container:
   ```bash
   docker-compose restart public-website
   ```

### Issue: SSL Certificate Errors

**Symptoms**: Browser shows "Your connection is not private" or certificate errors.

**Solutions**:
1. Verify certificates exist:
   ```bash
   ls -la /etc/letsencrypt/live/kalaisafaris.com/
   ```

2. Check certificate expiration:
   ```bash
   certbot certificates
   ```

3. Renew certificates if expired:
   ```bash
   certbot renew
   ```

4. If using NPM, check the SSL configuration in the NPM UI

### Issue: Static Assets Not Loading

**Symptoms**: The page loads but images/styles are missing, console shows 404 errors for `_next/static/*` files.

**Solutions**:
1. Verify the build completed successfully:
   ```bash
   docker exec public_website_app ls -la .next/static
   ```

2. Check nginx cache configuration

3. Clear browser cache and hard refresh (Ctrl+F5)

4. Rebuild the container:
   ```bash
   docker-compose up -d --build public-website
   ```

### Issue: Container Fails to Start

**Symptoms**: Container exits immediately after starting.

**Solutions**:
1. Check logs for errors:
   ```bash
   docker logs public_website_app
   ```

2. Verify the build succeeded:
   ```bash
   docker-compose build public-website
   ```

3. Check if port 3000 is already in use:
   ```bash
   lsof -i :3000
   ```

## Health Checks

The public-website container includes a health check that verifies the application is responding. You can check the health status:

```bash
docker inspect public_website_app --format='{{.State.Health.Status}}'
```

Expected output: `healthy`

## Monitoring

### Check Container Status

```bash
docker-compose ps
```

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f public-website

# View last 100 lines
docker-compose logs --tail=100 public-website
```

### Test the Endpoint

```bash
# Test from the host machine
curl -I http://localhost:3000

# Test from inside the container
docker exec public_website_app node -e "require('http').get('http://localhost:3000', (r) => console.log(r.statusCode))"
```

## Updating the Website

When you need to update the website code:

1. Pull the latest changes:
   ```bash
   cd /path/to/Kali-Safaris
   git pull
   ```

2. Rebuild and restart the container:
   ```bash
   docker-compose up -d --build public-website
   ```

3. Verify the update:
   ```bash
   docker logs public_website_app
   ```

## Performance Optimization

### Enable Caching

The nginx configuration already includes caching for static assets. Ensure your proxy (NPM or nginx) has caching enabled.

### Monitor Resource Usage

```bash
# Check CPU and memory usage
docker stats public_website_app
```

### Scale if Needed

If the single container can't handle the load, you can scale horizontally:

```bash
docker-compose up -d --scale public-website=3
```

Then configure your load balancer (NPM or nginx) to distribute traffic across the instances.

## Security Considerations

1. **Keep Next.js Updated**: Regularly update Next.js to the latest version to patch security vulnerabilities
   ```bash
   cd public-website
   npm update next
   ```

2. **Use HTTPS Only**: Always force HTTPS in production

3. **Configure Firewall**: Only allow necessary ports (80, 443, 81 for NPM admin)

4. **Secure NPM Admin Panel**: Change default credentials and restrict access to port 81

5. **Regular Backups**: Backup your docker volumes and configuration

## Support

For issues specific to:
- **Next.js**: Check [Next.js documentation](https://nextjs.org/docs)
- **Docker**: Check [Docker documentation](https://docs.docker.com/)
- **Nginx Proxy Manager**: Check [NPM documentation](https://nginxproxymanager.com/guide/)
- **Let's Encrypt**: Check [Certbot documentation](https://certbot.eff.org/)
