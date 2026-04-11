import Image from "next/image";
import type { Metadata } from "next";
import FooterSection from "@/components/FooterSection";

export const metadata: Metadata = {
  title: "About Us",
  description: "Learn about Kalai Safaris — a boating safari company offering unforgettable cruise experiences on the mighty Zambezi River above Victoria Falls, Zimbabwe.",
};

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      {/* Hero Banner */}
      <section className="relative h-[40vh] md:h-[50vh] flex items-center justify-center overflow-hidden">
        <Image
          src="/images/Kalai Sunset background shot.jpeg"
          alt="Sunset on the Zambezi River"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        <div className="relative text-center text-white px-6">
          <p className="text-sm uppercase tracking-[0.3em] text-[#ffba5a] font-semibold mb-3">
            Our Story
          </p>
          <h1 className="text-4xl md:text-6xl font-black drop-shadow-lg">
            About Kalai Safaris
          </h1>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-20 bg-gradient-to-b from-white via-[#fff7ec] to-white relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-48 h-48 bg-[#ffba5a]/15 blur-3xl rounded-full" />
          <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#ff9800]/10 blur-3xl rounded-full" />
        </div>

        <div className="container mx-auto px-6 relative">
          {/* Intro Block */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center mb-20">
            <div className="bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 md:p-10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <h2 className="relative text-3xl md:text-4xl font-black text-gray-900 mb-6">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#ff9800] to-[#ffba5a]">Kalai</span> — The Cry of the Fish Eagle
              </h2>
              <p className="relative text-lg text-gray-700 leading-relaxed mb-4">
                Kalai Safaris is a boating safari company on the mighty Zambezi River, above the Victoria Falls. We are dedicated to providing unforgettable cruise experiences that combine the beauty of Africa&apos;s wildlife with the serenity of the river.
              </p>
              <p className="relative text-lg text-gray-700 leading-relaxed">
                We believe in responsible tourism, supporting local communities, and protecting the natural beauty of our destinations. Join us for an adventure that will leave you with memories to last a lifetime.
              </p>
            </div>
            <div className="rounded-3xl overflow-hidden shadow-2xl border border-white/50">
              <Image
                src="/images/kalai_intro.jpeg"
                alt="Kalai Safari cruise boat on the Zambezi"
                width={800}
                height={600}
                className="w-full h-full object-cover"
              />
            </div>
          </div>

          {/* Fleet Block */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
            <div className="order-2 lg:order-1 rounded-3xl overflow-hidden shadow-2xl border border-white/50">
              <Image
                src="/images/cruise boat.jpg"
                alt="Kalai Safaris cruise vessel"
                width={800}
                height={600}
                className="w-full h-full object-cover"
              />
            </div>
            <div className="order-1 lg:order-2 bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 md:p-10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <h2 className="relative text-3xl md:text-4xl font-black text-gray-900 mb-6">
                Our Fleet
              </h2>
              <p className="relative text-lg text-gray-700 leading-relaxed mb-4">
                We operate two purpose-built cruise vessels — a <strong>40-seater</strong> for larger groups and events, and an intimate <strong>10-seater</strong> for private charters and exclusive experiences.
              </p>
              <ul className="relative space-y-3 text-gray-700">
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#ff9800] mt-2 flex-shrink-0" />
                  Expert guides with deep knowledge of the Zambezi ecosystem
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#ff9800] mt-2 flex-shrink-0" />
                  Safety-first approach with well-maintained vessels
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#ff9800] mt-2 flex-shrink-0" />
                  Tailor-made cruises for weddings, conferences & events
                </li>
                <li className="flex items-start gap-3">
                  <span className="w-2 h-2 rounded-full bg-[#ff9800] mt-2 flex-shrink-0" />
                  Eco-friendly practices supporting conservation
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <FooterSection />
    </div>
  );
}
