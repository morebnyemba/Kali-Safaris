'use client';

import Image from "next/image";
import { useState } from "react";
import FooterSection from "@/components/FooterSection";
import BookingModal from "@/components/BookingModal";
import { FaWhatsapp, FaPhone, FaEnvelope } from "react-icons/fa";

const cruises = [
  {
    title: "Sunrise Cruise",
    time: "06:00 AM — 08:00 AM",
    price: "From $20",
    image: "/images/sunrise.jpeg",
    description: "Start your day with the peaceful sounds of the Zambezi as hippos yawn and fish eagles call.",
    emoji: "🌅",
  },
  {
    title: "Lunch Cruise",
    time: "12:00 PM — 02:00 PM",
    price: "From $20",
    image: "/images/work_no_play.jpeg",
    description: "A relaxing midday cruise along the river with stunning views and refreshing breezes.",
    emoji: "☀️",
  },
  {
    title: "Sunset Cruise",
    time: "04:00 PM — After Sunset",
    price: "From $20",
    image: "/images/sunset.jpeg",
    description: "The most popular cruise — watch the African sun set over the Zambezi in golden splendour.",
    emoji: "🌇",
  },
  {
    title: "Dinner Cruise",
    time: "Evening (by arrangement)",
    price: "From $70",
    image: "/images/Kalai Sunset background shot.jpeg",
    description: "An exclusive evening on the river, complete with a gourmet dinner under the stars.",
    emoji: "🌙",
  },
  {
    title: "Jetty Venue Hire",
    time: "Flexible",
    price: "Contact us",
    image: "/images/jetty_venue.jpg",
    description: "Host your wedding, conference, or cocktail event at our beautiful riverside jetty.",
    emoji: "🎉",
  },
];

export default function BookingPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCruise, setSelectedCruise] = useState("");

  const handleBookClick = (cruiseTitle: string) => {
    setSelectedCruise(cruiseTitle);
    setIsModalOpen(true);
  };

  return (
    <div className="min-h-screen">
      {/* Hero Banner */}
      <section className="relative h-[40vh] md:h-[50vh] flex items-center justify-center overflow-hidden">
        <Image
          src="/images/slider/1.jpeg"
          alt="Zambezi River Cruise"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        <div className="relative text-center text-white px-6">
          <p className="text-sm uppercase tracking-[0.3em] text-[#ffba5a] font-semibold mb-3">
            Reservations
          </p>
          <h1 className="text-4xl md:text-6xl font-black drop-shadow-lg mb-4">
            Book Your Safari Cruise
          </h1>
          <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto">
            Choose your perfect Zambezi experience and we&apos;ll handle the rest
          </p>
        </div>
      </section>

      {/* Cruise Selection Cards */}
      <section className="py-20 bg-gradient-to-b from-white via-[#fff7ec] to-white relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 left-10 w-48 h-48 bg-[#ffba5a]/15 blur-3xl rounded-full" />
          <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#ff9800]/10 blur-3xl rounded-full" />
        </div>

        <div className="container mx-auto px-6 relative">
          <div className="text-center mb-14">
            <p className="text-sm uppercase tracking-[0.3em] text-[#ff9800] font-semibold mb-3">
              Choose Your Cruise
            </p>
            <h2 className="text-3xl md:text-4xl font-black text-gray-900 mb-4">
              Select a Cruise to Book
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto">
              Pick your preferred cruise type and time. We&apos;ll confirm availability on WhatsApp.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {cruises.map((cruise, index) => (
              <div
                key={index}
                className="group relative bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl overflow-hidden transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl"
              >
                {/* Cruise Image */}
                <div className="relative h-48 overflow-hidden">
                  <Image
                    src={cruise.image}
                    alt={cruise.title}
                    fill
                    className="object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                  <div className="absolute bottom-3 left-3">
                    <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-[#ffba5a] to-[#ff9800] text-black shadow-sm">
                      {cruise.emoji} {cruise.price}
                    </span>
                  </div>
                </div>

                {/* Card Content */}
                <div className="p-5">
                  <h3 className="text-xl font-bold text-gray-900 mb-1">{cruise.title}</h3>
                  <p className="text-sm text-[#ff9800] font-medium mb-3">{cruise.time}</p>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">{cruise.description}</p>
                  <button
                    onClick={() => handleBookClick(cruise.title)}
                    className="w-full rounded-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black font-bold py-2.5 transition-all duration-300 shadow-md hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Book This Cruise
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Contact Methods */}
          <div className="max-w-3xl mx-auto">
            <div className="bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <h3 className="relative text-2xl font-bold text-gray-900 mb-6 text-center">
                Or Contact Us Directly
              </h3>
              <div className="relative grid grid-cols-1 md:grid-cols-3 gap-4">
                <a
                  href="https://wa.me/263712629336?text=*[Message from Kalai Safaris Website]*%0A%0AHi, I'd like to book a cruise. Please help!"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-3 p-4 rounded-xl bg-[#25D366]/10 border border-[#25D366]/20 hover:bg-[#25D366] hover:text-white text-[#25D366] transition-all duration-300 font-semibold"
                >
                  <FaWhatsapp size={22} />
                  WhatsApp
                </a>
                <a
                  href="tel:+263712629336"
                  className="flex items-center justify-center gap-3 p-4 rounded-xl bg-[#ff9800]/10 border border-[#ff9800]/20 hover:bg-[#ff9800] hover:text-black text-[#ff9800] transition-all duration-300 font-semibold"
                >
                  <FaPhone size={18} />
                  +263 712 629 336
                </a>
                <a
                  href="mailto:reservation@kalaisafaris.com"
                  className="flex items-center justify-center gap-3 p-4 rounded-xl bg-[#001a33]/10 border border-[#001a33]/20 hover:bg-[#001a33] hover:text-white text-[#001a33] transition-all duration-300 font-semibold"
                >
                  <FaEnvelope size={18} />
                  Email Us
                </a>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Booking Modal */}
      <BookingModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        cruiseType={selectedCruise}
      />

      <FooterSection />
    </div>
  );
}
