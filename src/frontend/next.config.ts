import type { NextConfig } from 'next';
const path = require('path');

const isDev = process.env.NODE_ENV !== 'production';
const enableStaticExport = !isDev && (process.env.NEXT_EXPORT === '1' || process.env.NEXT_EXPORT === 'true');

const nextConfig: NextConfig = {
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  reactStrictMode: false,
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    unoptimized: true,
  },
  trailingSlash: false,
  ...(enableStaticExport ? { output: 'export' } : {}),
};

export default nextConfig;
