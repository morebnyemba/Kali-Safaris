'use client';

import Image from "next/image";
import { useState } from "react";
import BookingModal from "./BookingModal";

const cruises = [
  {
    id: "sunrise",
    title: "Sunrise Cruise",
    description:
      "Get to experience the early blessings of what the mighty Zambezi river can offer while you take a relaxing and most comforting safari cruise. Experience how nature and wild animals starts their beautiful day.",
    time: "Our cruise is a 2 hour early morning cruise starting at 06:00 am to 08:00 am",
    image: "/images/sunrise.jpeg",
    accent: "from-[#ffefc7] via-[#ffe2a8] to-white",
    pill: "bg-[#ffba5a]/20 text-[#a24c00]",
  },
  {
    id: "lunch",
    title: "Lunch Cruise",
    description:
      "Have a relaxing and most comforting experience on mighty zambezi river lunch time safari cruise.",
    time: "A 2 hour cruise starting at 12:00pm to 02:00pm",
    image: "/images/work_no_play.jpeg",
    accent: "from-[#001a33] via-[#01294d] to-[#0a4d79]",
    pill: "bg-[#6bb5ff]/20 text-[#e2f2ff]",
    imageFirst: true,
  },
  {
    id: "sunset",
    title: "Sunset Cruise",
    description:
      "Kalai Safaris will give you an unforgettable experience along the Zambezi, as you may have an opportunity to spot a wide range of wild animals and birds interacting. Our cruise is a 2 hour late afternoon cruise starting at 16:00hrs and it ends soon after sunset",
    image: "/images/sunset.jpeg",
    image2: "/images/Kalai Sunset background shot.jpeg",
    accent: "from-[#ffba5a] via-[#ff8c42] to-[#ff6f3c]",
    pill: "bg-[#ff6f3c]/15 text-[#5c1d00]",
  },
  {
    id: "jetty",
    title: "Jetty Venue",
    description:
      "We can offer events hosting on our riverside jetty, conference, weddings, cocktails or any outdoor function which needs a beautiful backdrop of the mighty Zambezi River",
    image: "/images/jetty_venue.jpg",
    accent: "from-[#001a33] via-[#032b44] to-[#0e3f5c]",
    pill: "bg-[#8ce0ff]/15 text-[#e6f7ff]",
    imageFirst: true,
  },
];

export default function CruiseTypesSection() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCruise, setSelectedCruise] = useState("");

  const handleBookClick = (cruiseTitle: string) => {
    setSelectedCruise(cruiseTitle);
    setIsModalOpen(true);
  };

  const handleAskQuestion = (cruiseTitle: string) => {
    const message = `*[Message from Kali Safaris Website]*\n\nHi, I would like to ask a question about the ${cruiseTitle}.`;
    const whatsappUrl = `https://wa.me/263712629336?text=${encodeURIComponent(message)}`;
    window.open(whatsappUrl, '_blank');
  };

  return (
    <div className="space-y-16">{cruises.map((cruise, idx) => (
        <section
          key={cruise.id}
          id={cruise.id}
          className="relative py-16"
        >
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className={`absolute -left-10 top-10 w-52 h-52 rounded-full blur-3xl bg-gradient-to-br ${cruise.accent} opacity-60`} />
            <div className={`absolute -right-10 bottom-10 w-56 h-56 rounded-full blur-3xl bg-gradient-to-tr ${cruise.accent} opacity-40`} />
          </div>

          <div
            className={`container mx-auto px-6 relative grid grid-cols-1 lg:grid-cols-2 gap-10 items-center ${
              cruise.imageFirst ? "lg:[&>*:first-child]:order-2" : ""
            }`}
          >
            {/* Text Content */}
            <div className="bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 md:p-10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <div className="relative flex flex-wrap items-center gap-3 mb-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-[0.2em] ${cruise.pill}`}
                >
                  {cruise.title}
                </span>
                {cruise.time && (
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-black/5 text-gray-700">
                    {cruise.time}
                  </span>
                )}
              </div>

              <h2 className="relative text-3xl md:text-4xl font-black text-gray-900 drop-shadow-sm mb-4">
                {cruise.title}
              </h2>

              <p className="relative text-lg text-gray-700 leading-relaxed mb-6">
                {cruise.description}
              </p>

              <div className="relative flex flex-wrap gap-3">
                <button 
                  onClick={() => handleBookClick(cruise.title)}
                  className="rounded-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] text-black font-semibold px-6 py-3 shadow-lg transition-transform duration-300 hover:-translate-y-0.5 hover:shadow-xl">
                  Book this cruise
                </button>
                <button
                  onClick={() => handleAskQuestion(cruise.title)}
                  className="rounded-full border border-black/10 bg-white/70 backdrop-blur-md text-gray-800 font-semibold px-6 py-3 shadow-sm transition duration-300 hover:border-[#ff9800]/60"
                >
                  Ask a question
                </button>
              </div>
            </div>

            {/* Images */}
            <div className="relative">
              <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-white/50 bg-white/40 backdrop-blur">
                <Image
                  src={cruise.image}
                  alt={cruise.title}
                  width={800}
                  height={600}
                  className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-[1.02]"
                  priority={idx === 0}
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-transparent" />
              </div>

              {cruise.image2 && (
                <div className="absolute -right-6 -bottom-8 w-40 sm:w-48 md:w-56 rounded-2xl overflow-hidden shadow-xl border border-white/60 bg-white/70 backdrop-blur-md rotate-3">
                  <Image
                    src={cruise.image2}
                    alt={`${cruise.title} view 2`}
                    width={400}
                    height={300}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}
            </div>
          </div>
        </section>
      ))}

      {/* Booking Modal */}
      <BookingModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        cruiseType={selectedCruise}
      />
    </div>
  );
}
