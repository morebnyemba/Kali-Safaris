import type { Metadata } from "next";
import { Outfit } from "next/font/google";

import "./globals.css";
import Header from "@/components/Header";

const outfit = Outfit({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: {
    default: "Kalai Safaris — Zambezi River Cruises | Victoria Falls",
    template: "%s | Kalai Safaris",
  },
  description: "Affordable safari cruises on the mighty Zambezi River above Victoria Falls. Sunrise, lunch & sunset cruises with breathtaking wildlife encounters.",
  keywords: ["Kalai Safaris", "Zambezi River Cruise", "Victoria Falls", "Safari Zimbabwe", "Sunset Cruise"],
  icons: {
    icon: [
      { url: "/favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    other: [
      { rel: "manifest", url: "/site.webmanifest" },
    ],
  },
  openGraph: {
    type: "website",
    siteName: "Kalai Safaris",
    title: "Kalai Safaris — Zambezi River Cruises",
    description: "Experience peaceful and adventurous cruises on the mighty Zambezi River above Victoria Falls.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Kalai Safaris — Zambezi River Cruises",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Kalai Safaris — Zambezi River Cruises",
    description: "Affordable safari cruises on the mighty Zambezi River above Victoria Falls.",
    images: ["/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={outfit.variable}>
      <body className={`${outfit.className} antialiased`}>
        <Header />
        {children}
      </body>
    </html>
  );
}
