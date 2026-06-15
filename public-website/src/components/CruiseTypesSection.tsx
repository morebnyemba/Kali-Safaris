'use client';

import Image from "next/image";
import { useRouter } from "next/navigation";

const cruises = [
  {
    id: "sunrise",
    title: "Sunrise Cruise",
    amountUsd: 25,
    description:
      "Get to experience the early blessings of what the mighty Zambezi river can offer while you take a relaxing and most comforting safari cruise. Experience how nature and wild animals starts their beautiful day.",
    time: "Our cruise is a 2 hour early morning cruise starting at 06:00 am to 08:00 am",
    image: "/images/sunrise.jpeg",
    pill: "bg-[#E09A18]/20 text-[#7a3d00]",
  },
  {
    id: "lunch",
    title: "Lunch Cruise",
    amountUsd: 25,
    description:
      "Have a relaxing and most comforting experience on mighty zambezi river lunch time safari cruise.",
    time: "A 2 hour cruise starting at 12:00pm to 02:00pm",
    image: "/images/work_no_play.jpeg",
    pill: "bg-[#0A0A0A]/10 text-[#1A1A1A]",
    imageFirst: true,
  },
  {
    id: "sunset",
    title: "Sunset Cruise",
    amountUsd: 25,
    description:
      "Kalai Safaris will give you an unforgettable experience along the Zambezi, as you may have an opportunity to spot a wide range of wild animals and birds interacting. Our cruise is a 2 hour late afternoon cruise starting at 16:00hrs and it ends soon after sunset",
    image: "/images/sunset.jpeg",
    image2: "/images/Kalai Sunset background shot.jpeg",
    pill: "bg-[#C8102E]/10 text-[#7a0016]",
  },
  {
    id: "jetty",
    title: "Jetty Venue",
    amountUsd: 70,
    description:
      "We can offer events hosting on our riverside jetty, conference, weddings, cocktails or any outdoor function which needs a beautiful backdrop of the mighty Zambezi River",
    image: "/images/jetty_venue.jpg",
    pill: "bg-[#0A0A0A]/10 text-[#1A1A1A]",
    imageFirst: true,
  },
];

export default function CruiseTypesSection() {
  const router = useRouter();

  const handleBookClick = (cruiseTitle: string, amountUsd: number) => {
    router.push(`/booking?tour_name=${encodeURIComponent(cruiseTitle)}&amount=${amountUsd}`);
  };

  const handleAskQuestion = (cruiseTitle: string) => {
    const message = `*[Message from Kalai Safaris Website]*\n\nHi, I would like to ask a question about the ${cruiseTitle}.`;
    window.open(`https://wa.me/263712629336?text=${encodeURIComponent(message)}`, '_blank');
  };

  return (
    <div className="space-y-16">
      {cruises.map((cruise) => (
        <section key={cruise.id} id={cruise.id} className="relative py-16 bg-[#FFF9F5]">
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute -left-10 top-10 w-52 h-52 rounded-full blur-3xl bg-[#E09A18]/20 opacity-60" />
            <div className="absolute -right-10 bottom-10 w-56 h-56 rounded-full blur-3xl bg-[#E8600A]/15 opacity-40" />
          </div>

          <div
            className={`container mx-auto px-6 relative grid grid-cols-1 lg:grid-cols-2 gap-10 items-center ${
              cruise.imageFirst ? "lg:[&>*:first-child]:order-2" : ""
            }`}
          >
            {/* Text Content */}
            <div className="bg-white/90 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 md:p-10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <div className="relative flex flex-wrap items-center gap-3 mb-4">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-[0.2em] ${cruise.pill}`}>
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
                  onClick={() => handleBookClick(cruise.title, cruise.amountUsd)}
                  className="rounded-full bg-[#C8102E] hover:bg-[#E8173A] text-white font-semibold px-6 py-3 shadow-lg transition-all duration-300 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-red-600/25"
                >
                  Book this cruise
                </button>
                <button
                  onClick={() => handleAskQuestion(cruise.title)}
                  className="rounded-full border border-black/10 bg-white/70 backdrop-blur-md text-gray-800 font-semibold px-6 py-3 shadow-sm transition duration-300 hover:border-[#E8600A]/60 hover:text-[#E8600A]"
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
                  className="w-full h-full object-cover transition-transform duration-700 hover:scale-[1.02]"
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
    </div>
  );
}
