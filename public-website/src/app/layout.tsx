import type { Metadata } from "next";

import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Home | Kalai Safaris On The Zambezi",
  description: "Kalai Safaris - Affordable cruise on the Zambezi River. Experience peaceful and adventurous cruises above Victoria Falls with sunrise, lunch, and sunset cruise options.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <Header />
        {children}
      </body>
    </html>
  );
}
