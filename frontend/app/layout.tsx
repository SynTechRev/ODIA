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
      <head>
        {/*
          v2.7.9 B5 — prefetch the intro asset so the IntroFrame iframe
          has it ready the moment IntroGate decides to render. No visible
          loading gap on first paint. Cheap for returning users (the SW
          will already have it cached as part of the v3 shell).
        */}
        <link rel="prefetch" href="/intro/index.html" as="document" />
      </head>
      <body className="antialiased">
        <ServiceWorkerRegistration />
        <IntroGate>{children}</IntroGate>
      </body>
    </html>
  );
}
