import Image from "next/image";
import Link from "next/link";
import { FaClock, FaMapMarkerAlt, FaShip, FaWhatsapp } from "react-icons/fa";
import { SITE, whatsappLink } from "@/lib/site";

const FACTS = [
  { icon: FaClock, label: "Daily departures", value: "Sunrise · Lunch · Sunset" },
  { icon: FaShip, label: "Our vessels", value: "40-seat & 10-seat boats" },
  { icon: FaMapMarkerAlt, label: "Departs from", value: "Riverside jetty, Victoria Falls" },
];

/**
 * Static hero: one sharp photo, a clear promise, two actions and the facts a
 * traveller checks before booking. hipo.jpg is the only 2000px-wide photo we
 * have, so it's the only one that stays crisp full-bleed on desktop.
 */
export default function HeroSection() {
  return (
    <section className="relative isolate flex min-h-[calc(100svh-64px)] w-full flex-col overflow-hidden bg-[#0A0A0A] md:min-h-[calc(100svh-72px)] lg:min-h-[min(calc(100svh-104px),820px)]">
      <Image
        src="/images/slider/hipo.jpg"
        alt="Hippos in the Zambezi River above Victoria Falls"
        fill
        priority
        sizes="100vw"
        className="-z-10 object-cover object-[60%_30%] md:object-[70%_center]"
      />
      {/* Darken the text side only, so the photo still reads on the right. */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-t from-black/85 via-black/40 to-black/5 md:bg-gradient-to-r md:from-black/80 md:via-black/50 md:to-black/10" aria-hidden />

      <div className="container mx-auto flex flex-1 flex-col justify-center px-5 pb-10 pt-16 md:px-6 md:pt-20">
        <div className="max-w-2xl text-white">
          <p className="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[#F4B544] ring-1 ring-white/20 backdrop-blur">
            Victoria Falls · Zimbabwe
          </p>
          <h1 className="text-4xl font-extrabold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl">
            Zambezi River cruises above Victoria Falls
          </h1>
          <p className="mt-5 max-w-xl text-base leading-relaxed text-white/85 sm:text-lg">
            Relaxed sunrise, lunch and sunset cruises on the upper Zambezi — hippos, crocodiles, rich birdlife and
            unforgettable African sunsets from our riverside jetty.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/booking"
              className="inline-flex items-center justify-center rounded-full bg-[#C8102E] px-7 py-3.5 text-base font-bold text-white shadow-lg shadow-black/20 transition hover:bg-[#A00D24]"
            >
              Book a cruise
            </Link>
            <Link
              href="/#cruises"
              className="inline-flex items-center justify-center rounded-full bg-white px-7 py-3.5 text-base font-bold text-gray-900 transition hover:bg-white/90"
            >
              See cruises &amp; prices
            </Link>
          </div>

          <a
            href={whatsappLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-white/80 underline-offset-4 transition hover:text-white hover:underline"
          >
            <FaWhatsapp className="text-[#25D366]" aria-hidden /> Questions? WhatsApp us on {SITE.phoneDisplay}
          </a>
        </div>
      </div>

      {/* Quick facts — inside the hero, so nothing overlaps the next section. */}
      <div className="border-t border-white/15 bg-black/45 backdrop-blur-md">
        <dl className="container mx-auto grid grid-cols-1 divide-y divide-white/10 px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 md:px-6">
          {FACTS.map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center gap-3 py-3.5 sm:px-5 sm:py-5 sm:first:pl-0">
              <Icon className="shrink-0 text-lg text-[#F4B544]" aria-hidden />
              <div className="min-w-0">
                <dt className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/55">{label}</dt>
                <dd className="truncate text-sm font-semibold text-white">{value}</dd>
              </div>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
