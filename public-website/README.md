# Kalai Safaris Public Website

This is the public-facing website for Kalai Safaris (kalaisafaris.com), built with Next.js 16.

## Overview

This Next.js application serves as the main public website for Kalai Safaris, featuring:
- Safari booking information
- Photo gallery
- About page
- Optimized for production with standalone output

## Production Deployment

The website is deployed using Docker and configured to run behind an Nginx reverse proxy.

### Important Note About Nginx Proxy Manager

This repository includes both:
1. **Nginx Proxy Manager (NPM)** - A UI-based reverse proxy running on port 81
2. **nginx_proxy/** - Static nginx configuration files

If you're using Nginx Proxy Manager (recommended for easier SSL management), configure the proxy rules through the NPM web interface at http://your-server:81 instead of editing nginx.conf files directly.

### SSL Certificate Setup

**Option 1: Using Nginx Proxy Manager (Recommended)**

1. Access NPM UI at http://your-server:81
2. Add a new Proxy Host for kalaisafaris.com
3. Point it to `public-website:3000`
4. Enable SSL with Let's Encrypt through the UI
5. NPM will automatically handle certificate generation and renewal

**Option 2: Using Certbot with Static Nginx**

Before deploying, ensure SSL certificates are obtained for kalaisafaris.com:

```bash
# Using certbot with nginx
certbot certonly --nginx -d kalaisafaris.com -d www.kalaisafaris.com
```

**Option 3: HTTP Only (Development/Testing)**

If SSL certificates are not available, you can temporarily comment out the HTTPS server block in `nginx_proxy/nginx.conf` (lines 130-185) and access the site via HTTP only.

### Docker Deployment

The application uses a multi-stage Docker build for optimal performance:

1. **deps stage**: Installs production dependencies
2. **builder stage**: Builds the Next.js application
3. **runner stage**: Runs the optimized standalone server

Build and run:

```bash
# From the root directory
docker-compose up -d public-website

# Or rebuild after changes
docker-compose up -d --build public-website
```

### Nginx Configuration

The nginx proxy is configured to route traffic from kalaisafaris.com to the Next.js container:

- HTTP (port 80): Redirects to HTTPS
- HTTPS (port 443): Proxies to the Next.js app on port 3000
- Static assets are cached with appropriate headers
- Timeouts are configured for Next.js compatibility

### Health Checks

The container includes a health check that verifies the app is responding on port 3000.

## Local Development

First, install dependencies:

```bash
npm install
```

Then, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

## Build and Test

Build the production version locally:

```bash
npm run build
npm run start
```

## Configuration

The Next.js configuration (`next.config.ts`) includes:

- `output: 'standalone'` - Optimized production build
- `compress: true` - Gzip compression
- Custom security headers
- React compiler enabled

## Troubleshooting

### 504 Gateway Timeout Errors

If you encounter 504 errors:

1. Check if the public-website container is running: `docker ps`
2. Check container logs: `docker logs public_website_app`
3. Verify nginx configuration: `docker exec <nginx-container> nginx -t`
4. Ensure SSL certificates exist at the configured paths
5. Check that the upstream server is defined and reachable

### Static Assets Not Loading

If `_next/static/` assets fail to load:

1. Verify the build completed successfully
2. Check that `.next/static` was copied in the Dockerfile
3. Ensure nginx cache configuration is correct
4. Clear browser cache and try again

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Next.js Deployment](https://nextjs.org/docs/app/building-your-application/deploying) - deployment best practices.

