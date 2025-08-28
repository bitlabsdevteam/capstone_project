import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  // Optimize for Docker networking
  output: 'standalone',
  
  // API rewrites for direct backend communication
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'}/api/:path*`,
      },
    ];
  },
  
  // Headers for better Docker networking
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
