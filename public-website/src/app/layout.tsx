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
  openGraph: {
    type: "website",
    siteName: "Kalai Safaris",
    title: "Kalai Safaris — Zambezi River Cruises",
    description: "Experience peaceful and adventurous cruises on the mighty Zambezi River above Victoria Falls.",
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
