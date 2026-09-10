import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: "/kiosk/reports",
        destination: "/kiosk?step=reports",
        permanent: true,
      },
      {
        source: "/kiosk/done",
        destination: "/kiosk?step=done",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
