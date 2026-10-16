import type { Metadata } from "next";
import { Outfit } from "next/font/google";

import "./globals.css";
import Header from "@/components/Header";
import { SITE_URL } from "@/lib/seo";
import WhatsAppButton from "@/components/WhatsAppButton";

const outfit = Outfit({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
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
      { url: "/favicon-48x48.png", sizes: "48x48", type: "image/png" },
      { url: "/favicon.ico", sizes: "any" },
    ],
    shortcut: [
      { url: "/favicon.ico" },
    ],
    apple: [
      { url: "/apple-touch-icon-152x152.png", sizes: "152x152", type: "image/png" },
      { url: "/apple-touch-icon-167x167.png", sizes: "167x167", type: "image/png" },
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    other: [
      { rel: "manifest", url: "/site.webmanifest" },
    ],
  },
  // Preview image: app/opengraph-image.tsx (and one per route). Don't add
  // `images` here — a static file would override the generated cards.
  openGraph: {
    type: "website",
    siteName: "Kalai Safaris",
    locale: "en_GB",
    title: "Kalai Safaris — Zambezi River cruises above Victoria Falls",
    description: "Sunrise, lunch and sunset cruises on the Zambezi River above Victoria Falls. Book online and pay by card or mobile money.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Kalai Safaris — Zambezi River cruises above Victoria Falls",
    description: "Sunrise, lunch and sunset cruises on the Zambezi River above Victoria Falls. Book online and pay by card or mobile money.",
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
        <WhatsAppButton />
      </body>
    </html>
  );
}
