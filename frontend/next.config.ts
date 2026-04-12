import type { NextConfig } from "next";

// When ELECTRON_BUILD=1, produce a fully static export (frontend/out/)
// that Electron can load as local files. Docker deployments use the default
// standalone mode (output: "standalone").
const isElectronBuild = process.env.ELECTRON_BUILD === "1";

const nextConfig: NextConfig = {
  output: isElectronBuild ? "export" : "standalone",
};

export default nextConfig;
