'use client';

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchTours, tourPriceUsd, type Tour } from "@/lib/tours";

export default function PricingSection() {
  const router = useRouter();
  const [tours, setTours] = useState<Tour[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Same Tour + seasonal pricing data the booking page and the WhatsApp
  // "View Available Tours" flow read, so these tiles can never show a price
  // that's out of sync with what checkout actually charges.
  useEffect(() => {
    let isCancelled = false;

    const loadTours = async () => {
      setLoading(true);
      setError(false);
      try {
        const data = await fetchTours();
        if (!isCancelled) setTours(data);
      } catch {
        if (!isCancelled) setError(true);
      } finally {
        if (!isCancelled) setLoading(false);
      }
    };

    void loadTours();
    return () => {
      isCancelled = true;
    };
  }, []);

  // Only tour_name is sent — the booking page resolves the live price for it
  // from the Tour catalogue rather than trusting a client-supplied amount.
  const handleBookClick = (tourName: string) => {
    router.push(`/booking?tour_name=${encodeURIComponent(tourName)}`);
  };

  return (
    <section className="relative py-20 bg-gradient-to-b from-white via-[#FFF9F5] to-white overflow-hidden" id="services">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-48 h-48 bg-[#E09A18]/20 blur-3xl rounded-full" />
        <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#E8600A]/15 blur-3xl rounded-full" />
      </div>

      <div className="container mx-auto px-6 relative">
        <div className="text-center mb-14">
          <p className="text-sm uppercase tracking-[0.3em] text-[#E8600A] font-semibold mb-3">
            Pricing
          </p>
          <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900 drop-shadow-sm">
            Affordable Cruises
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Transparent packages with everything you need for a memorable Zambezi cruise.
          </p>
        </div>

        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-4" aria-label="Loading pricing">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="rounded-2xl border border-white/60 bg-white/70 shadow-lg p-6 animate-pulse">
                <div className="h-6 w-2/3 mx-auto rounded-full bg-gray-200 mb-4" />
                <div className="h-9 w-1/2 mx-auto rounded bg-gray-200 mb-4" />
                <div className="h-3 w-full rounded bg-gray-200 mb-2" />
                <div className="h-3 w-4/5 mx-auto rounded bg-gray-200 mb-6" />
                <div className="h-10 w-full rounded-full bg-gray-200" />
              </div>
            ))}
          </div>
        )}

        {!loading && (error || tours.length === 0) && (
          <div className="max-w-xl mx-auto mb-4 text-center bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl p-8">
            <p className="text-lg font-semibold text-gray-900 mb-2">
              We&apos;re updating our tour packages
            </p>
            <p className="text-gray-600">
              Please check back shortly, or reach out and one of our agents will help you book.
            </p>
          </div>
        )}

        {!loading && !error && tours.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {tours.map((tour) => {
              const price = tourPriceUsd(tour);
              return (
                <div
                  key={tour.id}
                  className="group relative bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl p-6 flex flex-col gap-4 text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl"
                >
                  <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/60 to-[#C8102E]/5 opacity-0 group-hover:opacity-100 transition duration-300" />

                  <div className="relative flex justify-center">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-[#E09A18] to-[#E8600A] text-white shadow-sm">
                      {tour.category_display}
                      <span className="w-2 h-2 rounded-full bg-white/60" />
                    </span>
                  </div>

                  <h3 className="relative text-2xl font-extrabold text-gray-900 drop-shadow-sm">
                    {tour.name}
                  </h3>

                  <p className="relative text-4xl font-extrabold text-gray-900 drop-shadow-sm">
                    ${price.toFixed(2)}
                    <span className="block text-sm font-medium text-gray-500 mt-1">Per person</span>
                  </p>

                  <p className="relative text-gray-700 leading-relaxed line-clamp-3 min-h-[48px]">
                    {tour.description}
                  </p>

                  <p className="relative text-sm font-semibold text-gray-600 bg-white/70 px-3 py-2 rounded-lg border border-white/50">
                    {tour.duration_display}
                    {tour.location ? ` · ${tour.location}` : ''}
                  </p>

                  <div className="relative flex justify-center mt-auto">
                    <button
                      onClick={() => handleBookClick(tour.name)}
                      className="w-full rounded-full bg-[#C8102E] hover:bg-[#E8173A] text-white font-bold py-2.5 transition-all duration-300 shadow-md hover:shadow-xl hover:shadow-red-600/25 hover:-translate-y-0.5"
                    >
                      Book this cruise
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="text-center mt-10">
          <p className="inline-flex items-center gap-2 text-base md:text-lg italic font-semibold text-gray-700 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-white/70">
            <span className="w-2 h-2 rounded-full bg-[#E8600A] animate-pulse" />
            <strong>(Excludes applicable Parks river usage fee)</strong>
          </p>
        </div>
      </div>
    </section>
  );
}
