import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ServiceWorkerRegistration } from "@/components/pwa/ServiceWorkerRegistration";
import { IntroGate } from "@/components/intro/IntroGate";

export const metadata: Metadata = {
  title: "O.D.I.A. — Oraculus Decimus Intellect Analyst",
  description: "Civic accountability intelligence platform for forensic analysis of legal and government documents",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    // v2.7.9 — black-translucent so iOS doesn't paint a default-colored
    // bar over the smoke chrome on the standalone PWA.
    statusBarStyle: "black-translucent",
    title: "O.D.I.A.",
  },
  icons: {
    apple: "/icons/icon-192.png",
  },
};

export const viewport: Viewport = {
  // v2.7.9 — aligned with --smoke-950 (the body background in
  // globals.css). The pre-v2.7.9 navy "#1A3652" pre-dated the gemstone
  // palette adoption and painted the Android status bar a wrong shade.
  themeColor: "#07070A",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/*
        v2.7.10 — removed the v2.7.9 server-rendered <link rel="prefetch"
        href="/intro/index.html">. Under Electron file:// the leading-slash
        form resolves to the filesystem root and silently fails; under
        Electron the asset is loaded from local disk anyway so prefetch
        gives nothing. IntroFrame computes the correct path at runtime.
      */}
      <body className="antialiased">
        <ServiceWorkerRegistration />
        <IntroGate>{children}</IntroGate>
      </body>
    </html>
  );
}
