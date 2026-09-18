import type { NextConfig } from "next";
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  output: "standalone", //standalone output prodduces a smaller production image intened for conatiners
  reactCompiler: true,
  turbopack: {
    root: frontendRoot,
  },
};

export default nextConfig;
