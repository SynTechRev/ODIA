import type { NextConfig } from "next";

// When ELECTRON_BUILD=1, produce a fully static export (frontend/out/)
// that Electron can load as local files. Any other value (unset, "0", etc.)
// uses the default standalone mode (output: "standalone") for Docker deployments.
const isElectronBuild = process.env.ELECTRON_BUILD === "1";

const nextConfig: NextConfig = {
  output: isElectronBuild ? "export" : "standalone",
};

export default nextConfig;
