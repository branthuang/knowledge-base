/** @type {import('next').NextConfig} */
const BACKEND_URL = process.env.BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000';

const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
      {
        source: '/docs',
        destination: `${BACKEND_URL}/docs`,
      },
      {
        source: '/openapi.json',
        destination: `${BACKEND_URL}/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;
