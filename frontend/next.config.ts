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
      // Images from next/image can't be optimised by a static export, and
      // any <Image> component in the app would break under file:// without
      // this flag.  We aren't heavy users of next/image but it's cheap
      // insurance.
      images: { unoptimized: true },
    }
  : {
      output: "standalone",
    };

export default nextConfig;
