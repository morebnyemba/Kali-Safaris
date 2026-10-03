'use client';

import Link from "next/link";
import { useEffect, useState } from "react";
import { FaClock, FaMapMarkerAlt } from "react-icons/fa";
import { fetchToursOnce, tourPriceUsd, type Tour } from "@/lib/tours";

const INITIAL_COUNT = 6;

export default function PricingSection() {
  const [tours, setTours] = useState<Tour[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [showAll, setShowAll] = useState(false);

  // Same Tour + seasonal pricing data the booking page and the WhatsApp
  // "View Available Tours" flow read, so prices here can never drift from
  // what checkout actually charges.
  useEffect(() => {
    let cancelled = false;
    fetchToursOnce()
      .then((data) => !cancelled && setTours(data))
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const visible = showAll ? tours : tours.slice(0, INITIAL_COUNT);

  return (
    <section id="prices" className="scroll-mt-20 bg-[#FFF9F5] py-16 md:py-24">
      {/* Legacy anchor for old "/#services" links. */}
      <span id="services" className="block scroll-mt-20" aria-hidden />
      <div className="container mx-auto px-5 md:px-6">
        <div className="mb-10 flex flex-col gap-3 md:mb-12 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#E8600A]">Prices</p>
            <h2 className="text-3xl font-extrabold tracking-tight text-gray-950 md:text-4xl">Packages &amp; prices</h2>
            <p className="mt-3 text-gray-600 md:text-lg">Per-person prices in US dollars. Pay securely online by card or mobile money.</p>
          </div>
          <p className="text-sm text-gray-500">Excludes the applicable National Parks river usage fee.</p>
        </div>

        {loading && (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2" aria-label="Loading prices">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="h-[132px] animate-pulse rounded-2xl border border-gray-200 bg-white" />
            ))}
          </div>
        )}

        {!loading && (error || tours.length === 0) && (
          <div className="mx-auto max-w-xl rounded-2xl border border-gray-200 bg-white p-8 text-center">
            <p className="mb-2 text-lg font-semibold text-gray-900">We&apos;re updating our packages</p>
            <p className="text-gray-600">Please check back shortly, or message us and an agent will help you book.</p>
          </div>
        )}

        {!loading && !error && tours.length > 0 && (
          <>
            <ul className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {visible.map((tour) => {
                const price = tourPriceUsd(tour);
                return (
                  <li
                    key={tour.id}
                    className="flex gap-4 rounded-2xl border border-gray-200 bg-white p-5 transition hover:border-gray-300 hover:shadow-[0_12px_32px_-18px_rgba(0,0,0,0.3)]"
                  >
                    <div className="min-w-0 flex-1">
                      <h3 className="text-lg font-bold leading-snug text-gray-950">{tour.name}</h3>
                      <p className="mt-1 line-clamp-2 text-sm leading-relaxed text-gray-600">{tour.description}</p>
                      <p className="mt-2.5 flex flex-wrap gap-x-4 gap-y-1 text-xs font-medium text-gray-500">
                        <span className="inline-flex items-center gap-1.5">
                          <FaClock className="text-[#E8600A]" aria-hidden /> {tour.duration_display}
                        </span>
                        {tour.location && (
                          <span className="inline-flex items-center gap-1.5">
                            <FaMapMarkerAlt className="text-[#E8600A]" aria-hidden /> {tour.location}
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="flex shrink-0 flex-col items-end justify-between gap-3 text-right">
                      <p className="leading-none">
                        <span className="text-2xl font-extrabold text-gray-950">${price.toFixed(0)}</span>
                        <span className="mt-1 block text-xs text-gray-500">per person</span>
                      </p>
                      <Link
                        href={`/booking?tour_name=${encodeURIComponent(tour.name)}`}
                        className="rounded-full bg-[#C8102E] px-4 py-2 text-sm font-bold text-white transition hover:bg-[#A00D24]"
                        aria-label={`Book ${tour.name}`}
                      >
                        Book
                      </Link>
                    </div>
                  </li>
                );
              })}
            </ul>

            {tours.length > INITIAL_COUNT && (
              <div className="mt-8 text-center">
                <button
                  type="button"
                  onClick={() => setShowAll((v) => !v)}
                  aria-expanded={showAll}
                  className="rounded-full border border-gray-300 bg-white px-6 py-2.5 text-sm font-bold text-gray-900 transition hover:border-gray-900"
                >
                  {showAll ? 'Show fewer' : `Show all ${tours.length} packages`}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </section>
  );
}
