/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Disabled due to Leaflet map initialization conflicts
  // swcMinify is now default in Next.js 15+ and deprecated

  output: 'standalone', // Required for Docker standalone build

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/api', // Use relative path for Traefik
    NEXT_PUBLIC_APP_NAME: 'Smart Shamba',
  },

  // Image optimization (updated for Next.js 15)
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
      },
      {
        protocol: 'https',
        hostname: 'www.greenlife.co.ke',
      },
      {
        protocol: 'https',
        hostname: 'res.cloudinary.com',
      },
      {
        protocol: 'https',
        hostname: 'www.nasa.gov',
      },
      {
        protocol: 'https',
        hostname: 'learn.digitalearthafrica.org',
      },
      {
        protocol: 'https',
        hostname: 'earthengine.google.com',
      },
      {
        protocol: 'https',
        hostname: 'www.esri.com',
      },
      {
        protocol: 'https',
        hostname: 'www.star-idaz.net',
      },
      {
        protocol: 'https',
        hostname: 'ksa.go.ke',
      },
      {
        protocol: 'https',
        hostname: 'mespt.org',
      },
      {
        protocol: 'https',
        hostname: 'enablinginnovation.africa',
      },
      {
        protocol: 'https',
        hostname: 'uonbi.ac.ke',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // Security headers
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
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(self)',
          },
        ],
      },
    ]
  },

  // Redirects (commented out as /admin is now the main dashboard)
  // async redirects() {
  //   return []
  // },
}

export default nextConfig

