'use client';

import Image from "next/image";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import FooterSection from "@/components/FooterSection";
import BookingModal from "@/components/BookingModal";
import { fetchTours, tourPriceUsd, type Tour } from "@/lib/tours";
import { FaWhatsapp, FaPhone, FaEnvelope, FaSun, FaMoon, FaShip, FaMapMarkerAlt } from "react-icons/fa";
import { BsSunriseFill, BsSunsetFill } from "react-icons/bs";
import { MdCelebration } from "react-icons/md";
import type { IconType } from "react-icons";

// Decorative fallback images for tours that don't have a photo uploaded on
// the backend yet. Cycled by list position, matched by name where possible.
const FALLBACK_IMAGES = [
  "/images/sunrise.jpeg",
  "/images/work_no_play.jpeg",
  "/images/sunset.jpeg",
  "/images/Kalai Sunset background shot.jpeg",
  "/images/jetty_venue.jpg",
];

function getTourImage(tour: Tour, index: number): string {
  if (tour.image_url) {
    return tour.image_url;
  }
  const name = tour.name.toLowerCase();
  if (name.includes("sunrise")) return "/images/sunrise.jpeg";
  if (name.includes("sunset")) return "/images/sunset.jpeg";
  if (name.includes("dinner") || name.includes("evening")) return "/images/Kalai Sunset background shot.jpeg";
  if (name.includes("lunch")) return "/images/work_no_play.jpeg";
  if (name.includes("jetty") || name.includes("venue")) return "/images/jetty_venue.jpg";
  return FALLBACK_IMAGES[index % FALLBACK_IMAGES.length];
}

function getTourIcon(tour: Tour): IconType {
  const name = tour.name.toLowerCase();
  if (name.includes("sunrise")) return BsSunriseFill;
  if (name.includes("sunset")) return BsSunsetFill;
  if (name.includes("dinner") || name.includes("evening")) return FaMoon;
  if (name.includes("lunch")) return FaSun;
  if (name.includes("jetty") || name.includes("venue")) return MdCelebration;
  return FaShip;
}

type PageStep = 'select' | 'booking';

function BookingPageContent() {
  const searchParams = useSearchParams();
  const [pageStep, setPageStep] = useState<PageStep>('select');
  const [tours, setTours] = useState<Tour[]>([]);
  const [toursLoading, setToursLoading] = useState(true);
  const [toursError, setToursError] = useState(false);
  const [selectedCruise, setSelectedCruise] = useState('');
  const [selectedAmountUsd, setSelectedAmountUsd] = useState(0);
  const [isPaymentScreen, setIsPaymentScreen] = useState(false);

  // Live tour catalogue — same Tour + seasonal pricing data the WhatsApp
  // "View Available Tours" flow reads, so the website never lists a trip
  // that doesn't actually exist in the backend.
  useEffect(() => {
    let isCancelled = false;

    const loadTours = async () => {
      setToursLoading(true);
      setToursError(false);
      try {
        const data = await fetchTours();
        if (isCancelled) return;
        setTours(data);
        setSelectedCruise((current) => current || (data[0]?.name ?? ''));
        setSelectedAmountUsd((current) => current || tourPriceUsd(data[0] ?? { price_per_adult: '0', base_price: '0' } as Tour));
      } catch {
        if (!isCancelled) {
          setToursError(true);
        }
      } finally {
        if (!isCancelled) {
          setToursLoading(false);
        }
      }
    };

    void loadTours();
    return () => {
      isCancelled = true;
    };
  }, []);

  const queryBookingReference = useMemo(() => searchParams.get('booking_reference') ?? '', [searchParams]);
  const queryPaymentMode = useMemo(() => (searchParams.get('payment_mode') ?? '').toLowerCase(), [searchParams]);
  const querySource = useMemo(() => (searchParams.get('source') ?? '').toLowerCase(), [searchParams]);
  const queryTourName = useMemo(() => searchParams.get('tour_name') ?? '', [searchParams]);
  const queryAmountUsd = useMemo(() => {
    const raw = searchParams.get('amount') ?? '';
    const parsed = Number(raw);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
  }, [searchParams]);

  // Deep-links from WhatsApp or from cruise cards on other pages skip straight to booking form
  useEffect(() => {
    const isDeepLink = Boolean(queryBookingReference) || queryPaymentMode === 'card' || Boolean(queryTourName) || querySource === 'whatsapp';
    if (!isDeepLink) return;

    const id = window.setTimeout(() => {
      if (queryTourName) {
        setSelectedCruise(queryTourName);
      } else if (querySource === 'whatsapp') {
        setSelectedCruise('WhatsApp Booking');
      }
      if (queryAmountUsd !== null) {
        setSelectedAmountUsd(queryAmountUsd);
      }
      setPageStep('booking');
    }, 0);

    return () => window.clearTimeout(id);
  }, [queryAmountUsd, queryBookingReference, queryPaymentMode, querySource, queryTourName]);

  const handleBookClick = (cruiseTitle: string, amountUsd: number) => {
    setSelectedCruise(cruiseTitle);
    setSelectedAmountUsd(amountUsd);
    setPageStep('booking');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToSelect = () => {
    setPageStep('select');
    setIsPaymentScreen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // ── Step 1: Cruise Selection ──────────────────────────────────────────────
  if (pageStep === 'select') {
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
            <p className="text-sm uppercase tracking-[0.3em] text-[#E09A18] font-semibold mb-3">
              Step 1 of 3
            </p>
            <h1 className="text-4xl md:text-6xl font-black drop-shadow-lg mb-4">
              Choose Your Cruise
            </h1>
            <p className="text-lg md:text-xl text-white/80 max-w-2xl mx-auto">
              Pick your perfect Zambezi experience to get started
            </p>
          </div>
        </section>

        {/* Step indicator */}
        <div className="bg-white border-b border-gray-100 sticky top-0 z-10">
          <div className="container mx-auto px-6 py-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
            <span className="rounded-full bg-[#C8102E] text-white px-3 py-1">1. Choose Cruise</span>
            <span className="text-gray-300">›</span>
            <span className="rounded-full bg-gray-100 text-gray-400 px-3 py-1">2. Your Details</span>
            <span className="text-gray-300">›</span>
            <span className="rounded-full bg-gray-100 text-gray-400 px-3 py-1">3. Payment</span>
          </div>
        </div>

        {/* Cruise Selection Cards */}
        <section className="py-16 bg-gradient-to-b from-white via-[#FFF9F5] to-white relative overflow-hidden">
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-10 left-10 w-48 h-48 bg-[#E09A18]/15 blur-3xl rounded-full" />
            <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#E8600A]/10 blur-3xl rounded-full" />
          </div>

          <div className="container mx-auto px-6 relative">
            {toursLoading && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12" aria-label="Loading tours">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="rounded-2xl border border-white/60 bg-white/70 shadow-lg overflow-hidden animate-pulse">
                    <div className="h-48 bg-gray-200" />
                    <div className="p-5 space-y-3">
                      <div className="h-5 w-2/3 rounded bg-gray-200" />
                      <div className="h-3 w-1/3 rounded bg-gray-200" />
                      <div className="h-3 w-full rounded bg-gray-200" />
                      <div className="h-3 w-4/5 rounded bg-gray-200" />
                      <div className="h-10 w-full rounded-full bg-gray-200 mt-4" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {!toursLoading && (toursError || tours.length === 0) && (
              <div className="max-w-xl mx-auto mb-12 text-center bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl p-8">
                <p className="text-lg font-semibold text-gray-900 mb-2">
                  We&apos;re updating our tour packages
                </p>
                <p className="text-gray-600">
                  Please check back shortly, or reach out below and one of our agents will help you book a custom tour.
                </p>
              </div>
            )}

            {!toursLoading && !toursError && tours.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
                {tours.map((tour, index) => {
                  const Icon = getTourIcon(tour);
                  const price = tourPriceUsd(tour);
                  return (
                    <div
                      key={tour.id}
                      className="group relative bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl overflow-hidden transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl"
                    >
                      <div className="relative h-48 overflow-hidden">
                        <Image
                          src={getTourImage(tour, index)}
                          alt={tour.name}
                          fill
                          className="object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                        <div className="absolute bottom-3 left-3">
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r from-[#C8102E] to-[#E8600A] text-white shadow-sm">
                            <Icon size={12} /> From ${price.toFixed(0)}
                          </span>
                        </div>
                      </div>

                      <div className="p-5">
                        <h3 className="text-xl font-bold text-gray-900 mb-1">{tour.name}</h3>
                        <p className="text-sm text-[#E8600A] font-medium mb-3 flex items-center gap-2 flex-wrap">
                          <span>{tour.duration_display}</span>
                          {tour.location && (
                            <span className="inline-flex items-center gap-1 text-gray-500 font-normal">
                              <FaMapMarkerAlt size={11} /> {tour.location}
                            </span>
                          )}
                        </p>
                        <p className="text-gray-600 text-sm leading-relaxed mb-4 line-clamp-3">{tour.description}</p>
                        <button
                          onClick={() => handleBookClick(tour.name, price)}
                          className="w-full rounded-full bg-gradient-to-r from-[#C8102E] to-[#E8600A] hover:from-[#E8173A] hover:to-[#F47B1A] text-white font-bold py-2.5 transition-all duration-300 shadow-md hover:shadow-xl hover:-translate-y-0.5"
                        >
                          Book This Cruise →
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Contact Methods */}
            <div className="max-w-3xl mx-auto">
              <div className="bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
                <h3 className="relative text-xl font-bold text-gray-900 mb-5 text-center">
                  Prefer to book directly?
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
                    className="flex items-center justify-center gap-3 p-4 rounded-xl bg-[#E8600A]/10 border border-[#E8600A]/20 hover:bg-[#E8600A] hover:text-black text-[#E8600A] transition-all duration-300 font-semibold"
                  >
                    <FaPhone size={18} />
                    +263 712 629 336
                  </a>
                  <a
                    href="mailto:reservation@kalaisafaris.com"
                    className="flex items-center justify-center gap-3 p-4 rounded-xl bg-[#0A0A0A]/10 border border-[#0A0A0A]/20 hover:bg-[#0A0A0A] hover:text-white text-[#0A0A0A] transition-all duration-300 font-semibold"
                  >
                    <FaEnvelope size={18} />
                    Email Us
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        <FooterSection />
      </div>
    );
  }

  // ── Step 2 + 3: Booking Form (details → payment) ──────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#FFF9F5] via-white to-[#FFF9F5]">
      {/* Step indicator */}
      {!isPaymentScreen && (
        <div className="bg-white border-b border-gray-100 sticky top-0 z-10">
          <div className="container mx-auto px-6 py-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em]">
            <button
              onClick={handleBackToSelect}
              className="rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 px-3 py-1 transition"
            >
              ← 1. Choose Cruise
            </button>
            <span className="text-gray-300">›</span>
            <span className="rounded-full bg-[#C8102E] text-white px-3 py-1">2. Your Details</span>
            <span className="text-gray-300">›</span>
            <span className="rounded-full bg-gray-100 text-gray-400 px-3 py-1">3. Payment</span>
          </div>
        </div>
      )}

      <section className={`${isPaymentScreen ? 'fixed inset-0 z-[120] overflow-y-auto bg-white py-6' : 'py-10 relative overflow-hidden'}`}>
        <div className="container mx-auto px-6 relative">
          <BookingModal
            key={`${selectedCruise}-${selectedAmountUsd}-${queryBookingReference}-${queryPaymentMode}`}
            isOpen={true}
            onClose={handleBackToSelect}
            cruiseType={selectedCruise}
            amountUsd={selectedAmountUsd}
            initialPaymentMode={queryPaymentMode === 'card' ? 'card' : undefined}
            initialBookingReference={queryBookingReference || undefined}
            fixedAmountUsd={queryAmountUsd ?? undefined}
            launchedFromWhatsApp={querySource === 'whatsapp'}
            presentation="page"
            onCheckoutStepChange={(step) => setIsPaymentScreen(step === 'payment')}
          />
        </div>
      </section>

      {!isPaymentScreen && <FooterSection />}
    </div>
  );
}

export default function BookingPage() {
  return (
    <Suspense fallback={null}>
      <BookingPageContent />
    </Suspense>
  );
}
