import type { NextConfig } from "next";

// Allow next/image to load tour photos served directly from the CRM
// backend (Tour.image), in addition to the production/staging domains.
const backendApiBase = process.env.NEXT_PUBLIC_BACKEND_API_BASE || '';
const backendRemotePattern = (() => {
  try {
    const url = new URL(backendApiBase);
    return {
      protocol: url.protocol.replace(':', '') as 'http' | 'https',
      hostname: url.hostname,
      port: url.port || undefined,
    };
  } catch {
    return null;
  }
})();

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  output: 'standalone',
  compress: true,
  poweredByHeader: false,
  generateEtags: true,
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.kalaisafaris.com' },
      { protocol: 'https', hostname: 'kalaisafaris.com' },
      { protocol: 'http', hostname: 'localhost', port: '8000' },
      { protocol: 'http', hostname: '127.0.0.1', port: '8000' },
      ...(backendRemotePattern ? [backendRemotePattern] : []),
    ],
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
          },
        ],
      },
    ];
  },
};

export default nextConfig;
