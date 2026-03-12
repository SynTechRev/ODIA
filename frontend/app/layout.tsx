import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Oraculus DI Auditor",
  description: "Comprehensive legal document ingestion, analysis, and anomaly detection platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
