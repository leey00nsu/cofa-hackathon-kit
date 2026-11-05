import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  agentRules: false,
  distDir: process.env.NEXT_TEST_DIST_DIR || ".next",
  poweredByHeader: false,
};

export default nextConfig;
