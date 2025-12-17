import HeroSection from "@/components/HeroSection";
import BookingCTA from "@/components/BookingCTA";
import IntroSection from "@/components/IntroSection";
import CruiseTypesSection from "@/components/CruiseTypesSection";
import PricingSection from "@/components/PricingSection";
import ReservationCTA from "@/components/ReservationCTA";
import FooterSection from "@/components/FooterSection";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <HeroSection />
      <BookingCTA />
      <IntroSection />
      <CruiseTypesSection />
      <PricingSection />
      <ReservationCTA />
      <FooterSection />
    </div>
  );
}
