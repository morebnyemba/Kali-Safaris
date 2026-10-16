import HeroSection from "@/components/HeroSection";
import CruiseTypesSection from "@/components/CruiseTypesSection";
import IntroSection from "@/components/IntroSection";
import PricingSection from "@/components/PricingSection";
import ReservationCTA from "@/components/ReservationCTA";
import FooterSection from "@/components/FooterSection";
import type { Metadata } from "next";
import { SITE } from "@/lib/site";
import { SITE_URL } from "@/lib/seo";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    siteName: "Kalai Safaris",
    locale: "en_GB",
    url: "/",
    title: "Kalai Safaris — Zambezi River cruises above Victoria Falls",
    description: "Sunrise, lunch and sunset cruises on the Zambezi River above Victoria Falls. Book online and pay by card or mobile money.",
  },
};

// Structured data so search engines and travel sites can read who we are,
// where we operate and how to reach us. Facts only — no ratings or reviews.
const jsonLd = {
  "@context": "https://schema.org",
  "@type": "TravelAgency",
  name: "Kalai Safaris",
  description: "Sunrise, lunch and sunset safari cruises on the Zambezi River above Victoria Falls, plus a riverside jetty venue for events.",
  url: SITE_URL,
  logo: `${SITE_URL}/images/kalailogo.png`,
  image: `${SITE_URL}/images/slider/hipo.jpg`,
  telephone: SITE.phoneHref.replace("tel:", ""),
  email: SITE.email,
  priceRange: "$$",
  foundingDate: "2019",
  address: {
    "@type": "PostalAddress",
    streetAddress: "Riverside jetty next to Palm Lodge",
    addressLocality: "Victoria Falls",
    addressCountry: "ZW",
  },
  areaServed: "Victoria Falls, Zimbabwe",
  sameAs: [SITE.facebook, SITE.tripadvisor].filter(Boolean),
};

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }} />
      <HeroSection />
      <CruiseTypesSection />
      <IntroSection />
      <PricingSection />
      <ReservationCTA />
      <FooterSection />
    </div>
  );
}
