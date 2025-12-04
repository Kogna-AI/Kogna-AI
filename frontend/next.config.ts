import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone", // Required for Docker production builds
};

export default nextConfig;
