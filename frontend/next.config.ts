import type { NextConfig } from "next";

// When ELECTRON_BUILD=1, produce a fully static export (frontend/out/) that
// Electron can load via file://.  Three things are required to make asset
// loading work under file:// on all platforms:
//
//   1.  output: "export"              — emit pure HTML/JS/CSS, no server.
//   2.  trailingSlash: true           — every route becomes /route/index.html
//                                       so relative `./` links resolve.
//   3.  assetPrefix: "./"             — rewrites <link href="/_next/...">
//                                       to <link href="./_next/..."> so the
//                                       browser does not treat the leading
//                                       slash as the filesystem root
//                                       (which on Windows would resolve to
//                                       C:\_next\... and 404 every asset).
//
// Any other value of ELECTRON_BUILD (unset, "0", etc.) uses the default
// standalone mode (output: "standalone") for Docker deployments.
const isElectronBuild = process.env.ELECTRON_BUILD === "1";

const nextConfig: NextConfig = isElectronBuild
  ? {
      output: "export",
      trailingSlash: true,
      assetPrefix: "./",
      images: { unoptimized: true },
      eslint: { ignoreDuringBuilds: true },
      // assetPrefix "./" makes the initial <script> tags in each page's
      // index.html resolve via relative paths, which is correct.  But
      // webpack's *runtime* publicPath is independently derived from the
      // same value, yielding "./_next/" — which the browser resolves
      // relative to the CURRENT document.  On a nested route like
      // /results/, that turns into .../results/_next/..., which does not
      // exist (chunks live at the export root, not beneath each route),
      // so every lazy-loaded chunk 404s under file://.  Setting webpack's
      // publicPath to "auto" makes it compute the value at runtime from
      // the webpack runtime script's own URL, which is always at the
      // export root, so dynamic imports resolve correctly at any depth.
      webpack: (config) => {
        config.output = { ...config.output, publicPath: "auto" };
        return config;
      },
    }
  : {
      output: "standalone",
      eslint: { ignoreDuringBuilds: true },
    };

export default nextConfig;
