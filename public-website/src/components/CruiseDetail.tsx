'use client';

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { FaArrowRight, FaClock, FaMapMarkerAlt, FaWhatsapp } from "react-icons/fa";
import { fetchGallery, type GalleryImage } from "@/lib/gallery";
import { fetchToursOnce, tourPriceUsd, type TimeSlot, type Tour } from "@/lib/tours";
import { CRUISES, PREMIUM_TOUR_NAME, bookingHref, cruisePath, type Cruise } from "@/lib/cruises";
import { SITE, whatsappLink } from "@/lib/site";

const slotRange = (slot: TimeSlot) => (slot.end ? `${slot.start} – ${slot.end}` : `${slot.start} onwards`);
const sameName = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

/**
 * One cruise, nothing else: its photo, live departure times and price, its own
 * gallery photos and a button straight into the booking form for it.
 */
export default function CruiseDetail({ cruise }: { cruise: Cruise }) {
  const [tours, setTours] = useState<Tour[] | null>(null);
  const [toursFailed, setToursFailed] = useState(false);
  const [photos, setPhotos] = useState<GalleryImage[]>([]);

  useEffect(() => {
    let cancelled = false;
    fetchToursOnce().then((t) => !cancelled && setTours(t), () => !cancelled && setToursFailed(true));
    fetchGallery()
      .then((images) => !cancelled && setPhotos(images.filter((img) => img.category === cruise.galleryCategory)))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [cruise.galleryCategory]);

  const tour = tours?.find((t) => sameName(t.name, cruise.tourName));
  const premium = tours?.find((t) => sameName(t.name, PREMIUM_TOUR_NAME));
  // The premium package's departure that matches this cruise (e.g. its 06:00 "Breakfast" slot).
  const premiumSlot = premium?.time_slots.find((s) => tour?.time_slots.some((own) => own.start === s.start));
  const price = tour ? tourPriceUsd(tour) : null;
  const others = CRUISES.filter((c) => c.slug !== cruise.slug);

  return (
    <>
      <section className="relative isolate flex min-h-[46svh] items-end overflow-hidden bg-[#0A0A0A] md:min-h-[54svh]">
        <Image src={cruise.image} alt={cruise.alt} fill priority sizes="100vw" className="-z-10 object-cover" />
        <div className="absolute inset-0 -z-10 bg-gradient-to-t from-black/85 via-black/40 to-black/10" aria-hidden />
        <div className="container mx-auto px-5 pb-10 pt-24 text-white md:px-6 md:pb-14">
          {cruise.badge && (
            <span className="mb-3 inline-block rounded-full bg-white px-3 py-1 text-xs font-bold text-[#C8102E]">{cruise.badge}</span>
          )}
          <h1 className="text-4xl font-extrabold tracking-tight md:text-6xl">{cruise.title}</h1>
          <p className="mt-2 text-lg text-white/85 md:text-xl">{cruise.tagline}</p>
        </div>
      </section>

      <section className="bg-white py-10 md:py-16">
        {/* Phones: description → booking card → photos. Desktop: photos under the description, card alongside. */}
        <div className="container mx-auto grid grid-cols-1 gap-10 px-5 md:px-6 lg:grid-cols-[1fr_380px]">
          <div className="lg:col-start-1 lg:row-start-1">
            <p className="text-lg leading-relaxed text-gray-700">{cruise.description}</p>

            <h2 className="mt-8 text-sm font-bold uppercase tracking-[0.16em] text-[#E8600A]">Departures</h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {tour?.time_slots.length
                ? tour.time_slots.map((slot) => (
                    <li key={slot.id} className="inline-flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 text-sm font-semibold tabular-nums text-gray-900">
                      <FaClock className="text-[#E8600A]" aria-hidden /> {slotRange(slot)}
                    </li>
                  ))
                : <li className="text-sm text-gray-500">{tours === null && !toursFailed ? 'Loading times…' : 'Daily — times confirmed when you book.'}</li>}
            </ul>
            <p className="mt-4 inline-flex items-start gap-2 text-sm text-gray-600">
              <FaMapMarkerAlt className="mt-0.5 shrink-0 text-[#E8600A]" aria-hidden /> Departs from our riverside jetty — {SITE.address}.
            </p>

          </div>

          {/* Booking card: sticky on desktop, right under the description on phones. */}
          <aside className="lg:sticky lg:top-24 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:self-start">
            <div className="rounded-2xl border border-gray-200 p-6 shadow-[0_18px_40px_-24px_rgba(0,0,0,0.35)]">
              <p className="text-sm text-gray-500">
                {price !== null
                  ? <>From <span className="text-3xl font-extrabold text-gray-950">${price.toFixed(0)}</span> per person</>
                  : toursFailed ? 'Price shown when you book' : <span className="inline-block h-8 w-28 animate-pulse rounded bg-gray-200 align-middle" />}
              </p>
              <p className="mt-1 text-xs text-gray-500">Excludes the National Parks river usage fee.</p>
              <Link
                href={bookingHref(cruise.tourName)}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-full bg-[#C8102E] py-3.5 font-bold text-white transition hover:bg-[#A00D24]"
              >
                Book this cruise <FaArrowRight aria-hidden />
              </Link>
              <p className="mt-3 text-center text-xs text-gray-500">Pay by EcoCash, Omari, ZimSwitch or card. Confirmed as soon as payment clears.</p>

              {premium && premiumSlot && (
                <div className="mt-6 rounded-xl bg-[#FFF5EC] p-4">
                  <p className="text-sm font-bold text-gray-950">
                    Upgrade: {premiumSlot.label || 'Premium'} package · ${tourPriceUsd(premium).toFixed(0)} pp
                  </p>
                  <p className="mt-1 text-sm text-gray-600">{premium.description}</p>
                  <Link href={bookingHref(premium.name, premiumSlot.start)} className="mt-2 inline-block text-sm font-bold text-[#C8102E] hover:underline">
                    Book the premium {cruise.title.toLowerCase()} →
                  </Link>
                </div>
              )}

              <a
                href={whatsappLink(`Hi, I have a question about the ${cruise.title}.`)}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-5 flex items-center justify-center gap-2 text-sm font-semibold text-gray-700 hover:text-[#128C7E]"
              >
                <FaWhatsapp className="text-[#25D366]" aria-hidden /> Questions? WhatsApp us
              </a>
            </div>
          </aside>

            {photos.length > 0 && (
              <div className="lg:col-start-1 lg:row-start-2">
                <div className="flex items-end justify-between gap-4">
                  <h2 className="text-2xl font-extrabold text-gray-950">Photos from the {cruise.title.toLowerCase()}</h2>
                  <Link href={`/gallery?category=${cruise.galleryCategory}`} className="shrink-0 text-sm font-bold text-[#C8102E] hover:underline">
                    See all →
                  </Link>
                </div>
                <ul className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3">
                  {photos.slice(0, 6).map((photo) => (
                    <li key={photo.id} className="relative aspect-[4/3] overflow-hidden rounded-xl bg-gray-100">
                      <Image src={photo.url} alt={photo.caption || cruise.title} fill sizes="(min-width:768px) 22vw, 45vw" className="object-cover" />
                    </li>
                  ))}
                </ul>
              </div>
            )}
        </div>
      </section>

      <section className="border-t border-gray-100 bg-[#FFF9F5] py-10">
        <div className="container mx-auto px-5 md:px-6">
          <h2 className="text-sm font-bold uppercase tracking-[0.16em] text-[#E8600A]">Other cruises</h2>
          <ul className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {others.map((other) => (
              <li key={other.slug}>
                <Link href={cruisePath(other.slug)} className="flex items-center gap-4 rounded-2xl border border-gray-200 bg-white p-3 transition hover:border-gray-400">
                  <span className="relative size-16 shrink-0 overflow-hidden rounded-xl">
                    <Image src={other.image} alt="" fill sizes="64px" className="object-cover" />
                  </span>
                  <span>
                    <span className="block font-bold text-gray-950">{other.title}</span>
                    <span className="block text-sm text-gray-500">{other.tagline}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
