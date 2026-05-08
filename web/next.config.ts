import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname, ".."),
  async rewrites() {
    return [
      {
        source: "/api/proxy/:path*",
        destination:
          process.env.NEXT_PUBLIC_BACKEND_URL
            ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/:path*`
            : "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
