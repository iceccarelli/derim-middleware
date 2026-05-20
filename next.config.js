/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  // Vercel-optimized standalone output (recommended for monorepos)
  output: 'standalone',

  // Image optimization - ready for future assets
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'derim.vercel.app',
      },
      {
        protocol: 'https',
        hostname: '**.vercel.app',
      },
      // Add more domains here when you use external images (e.g. Unsplash, GitHub avatars, etc.)
      // {
      //   protocol: 'https',
      //   hostname: 'images.unsplash.com',
      // },
    ],
    formats: ['image/avif', 'image/webp'],
    minimumCacheTTL: 60,
  },

  // Security headers (recommended for production)
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Production compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
};

module.exports = nextConfig;
