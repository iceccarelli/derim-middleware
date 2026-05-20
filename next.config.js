/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  
  // Recommended for Vercel + monorepo setups
  output: 'standalone',
  
  // Image optimization (uncomment when you add images later)
  // images: {
  //   remotePatterns: [
  //     {
  //       protocol: 'https',
  //       hostname: 'derim.vercel.app',
  //     },
  //   ],
  // },
};

module.exports = nextConfig;
