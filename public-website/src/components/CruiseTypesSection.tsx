'use client';

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { FaClock, FaWhatsapp } from "react-icons/fa";
import { fetchToursOnce, tourPriceUsd, type Tour } from "@/lib/tours";
import { whatsappLink } from "@/lib/site";

const experiences = [
  {
    id: "sunrise",
    title: "Sunrise Cruise",
    tourName: "Sunrise Cruise",
    time: "06:00 – 08:00",
    description:
      "Watch the river wake up — hippos surfacing, fish eagles calling and game coming down to drink in the cool morning light.",
    image: "/images/sunrise.jpeg",
    alt: "Breakfast table set on the deck overlooking the Zambezi at sunrise",
  },
  {
    id: "lunch",
    title: "Lunch Cruise",
    tourName: "Lunch Cruise",
    time: "12:00 – 14:00",
    description:
      "A relaxed midday cruise with a river breeze, great views and time to unwind between Victoria Falls activities.",
    image: "/images/work_no_play.jpeg",
    alt: "Guests enjoying a meal on the deck during a lunch cruise",
  },
  {
    id: "sunset",
    title: "Sunset Cruise",
    tourName: "Sunset Cruise",
    time: "16:00 – after sunset",
    badge: "Most popular",
    description:
      "Our most-loved cruise. Spot wildlife along the banks, then watch the sun go down in gold and red over the Zambezi.",
    image: "/images/Kalai Sunset background shot.jpeg",
    alt: "Sunset over the Zambezi River seen from a Kalai Safaris cruise",
  },
  {
    id: "jetty",
    title: "Jetty Venue",
    tourName: "Jetty Venue Hire",
    time: "By arrangement",
    description:
      "Host a wedding, conference, cocktail party or private function on our riverside jetty, with the Zambezi as your backdrop.",
    image: "/images/jetty_venue.jpg",
    alt: "Kalai Safaris riverside jetty event venue",
    isVenue: true,
  },
];

export default function CruiseTypesSection() {
  const [prices, setPrices] = useState<Record<string, number>>({});

  // Prices come from the live Tour catalogue (same source as checkout); a card
  // just hides its price until/unless a tour with the same name exists.
  useEffect(() => {
    let cancelled = false;
    fetchToursOnce()
      .then((tours: Tour[]) => {
        if (cancelled) return;
        setPrices(Object.fromEntries(tours.map((t) => [t.name.toLowerCase(), tourPriceUsd(t)])));
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section id="cruises" className="scroll-mt-20 bg-white py-16 md:py-24">
      <div className="container mx-auto px-5 md:px-6">
        <div className="mb-10 max-w-2xl md:mb-12">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#E8600A]">Our cruises</p>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-950 md:text-4xl">
            Choose your time on the river
          </h2>
          <p className="mt-3 text-gray-600 md:text-lg">
            Every cruise departs from our private jetty and lasts about two hours. Small groups, experienced
            guides and plenty of wildlife.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {experiences.map((x) => {
            const price = prices[x.tourName.toLowerCase()];
            const bookHref = `/booking?tour_name=${encodeURIComponent(x.tourName)}`;
            return (
              <article
                key={x.id}
                id={x.id}
                className="group flex scroll-mt-24 flex-col overflow-hidden rounded-2xl border border-gray-200 bg-white transition hover:border-gray-300 hover:shadow-[0_12px_32px_-16px_rgba(0,0,0,0.3)]"
              >
                <div className="relative aspect-[4/3] overflow-hidden bg-gray-100">
                  <Image
                    src={x.image}
                    alt={x.alt}
                    fill
                    sizes="(min-width:1024px) 25vw, (min-width:640px) 50vw, 100vw"
                    className="object-cover transition duration-500 group-hover:scale-[1.03]"
                  />
                  {x.badge && (
                    <span className="absolute left-3 top-3 rounded-full bg-white px-3 py-1 text-xs font-bold text-[#C8102E] shadow-sm">
                      {x.badge}
                    </span>
                  )}
                </div>

                <div className="flex flex-1 flex-col p-5">
                  <h3 className="text-xl font-bold text-gray-950">{x.title}</h3>
                  <p className="mt-1.5 inline-flex items-center gap-1.5 text-sm font-medium text-gray-600">
                    <FaClock className="text-[#E8600A]" aria-hidden /> {x.time}
                  </p>
                  <p className="mt-3 flex-1 text-[15px] leading-relaxed text-gray-600">{x.description}</p>

                  <div className="mt-5 flex items-end justify-between gap-3 border-t border-gray-100 pt-4">
                    <p className="text-sm text-gray-500">
                      {price ? (
                        <>
                          from <span className="text-xl font-extrabold text-gray-950">${price.toFixed(0)}</span>
                          {x.isVenue ? '' : ' pp'}
                        </>
                      ) : (
                        <span className="text-gray-400">&nbsp;</span>
                      )}
                    </p>
                    {x.isVenue ? (
                      <a
                        href={whatsappLink(`Hi, I'd like to enquire about hiring the jetty venue for an event.`)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-full border border-gray-300 px-4 py-2 text-sm font-bold text-gray-900 transition hover:border-[#25D366] hover:text-[#128C7E]"
                      >
                        <FaWhatsapp className="text-[#25D366]" aria-hidden /> Enquire
                      </a>
                    ) : (
                      <Link
                        href={bookHref}
                        className="rounded-full bg-[#C8102E] px-4 py-2 text-sm font-bold text-white transition hover:bg-[#A00D24]"
                      >
                        Book
                      </Link>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
