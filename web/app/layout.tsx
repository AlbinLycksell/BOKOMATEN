import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { QueryProvider } from "@/lib/query-client";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
  display: "swap",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Switchboard",
  description: "Svarstjänsten för hantverkare. Stockholm, Göteborg, Malmö, Skellefteå.",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="sv" className={`${geist.variable} ${geistMono.variable}`}>
      <body className="bg-bg text-text antialiased min-h-screen">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
