/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,

  async rewrites() {
    return {
      fallback: [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*", // Proxy to Backend
        },
      ],
    };
  },
};

module.exports = nextConfig;
