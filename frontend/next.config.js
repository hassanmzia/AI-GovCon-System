/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://django-api:8001/api/:path*",
      },
      {
        source: "/ws/:path*",
        destination: "http://node-realtime:8002/ws/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
