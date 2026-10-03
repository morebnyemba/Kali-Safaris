import Image from "next/image";
import Link from "next/link";
import { FaBinoculars, FaLeaf, FaShieldAlt, FaUsers } from "react-icons/fa";
import { SITE } from "@/lib/site";

const reasons = [
  { icon: FaBinoculars, title: "Knowledgeable guides", desc: "Local guides who know the river, its wildlife and its birds." },
  { icon: FaUsers, title: "Small, relaxed groups", desc: "A 40-seat and a 10-seat vessel, with room to move around on deck." },
  { icon: FaShieldAlt, title: "Safety first", desc: "Well-maintained vessels and experienced skippers on every trip." },
  { icon: FaLeaf, title: "Tailor-made trips", desc: "Private charters and special occasions arranged on request." },
];

export default function IntroSection() {
  return (
    <section id="about" className="scroll-mt-20 bg-white py-16 md:py-24">
      <div className="container mx-auto grid grid-cols-1 items-center gap-10 px-5 md:px-6 lg:grid-cols-2 lg:gap-16">
        <div className="relative aspect-[4/3] overflow-hidden rounded-2xl bg-gray-100">
          <Image
            src="/images/kalai_intro.jpeg"
            alt="Kalai Safaris boat cruising on the Zambezi River"
            fill
            sizes="(min-width:1024px) 50vw, 100vw"
            className="object-cover"
          />
        </div>

        <div>
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#E8600A]">About Kalai Safaris</p>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-950 md:text-4xl">
            &ldquo;Kalai&rdquo; — the cry of the fish eagle
          </h2>
          <p className="mt-4 text-gray-600 md:text-lg">
            We&apos;re a Victoria Falls boating safari company on the mighty Zambezi above the Falls. Since 2019 we&apos;ve
            been taking guests out on relaxed river cruises, and we tailor each trip to what you want from your day.
          </p>

          <ul className="mt-8 grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2">
            {reasons.map(({ icon: Icon, title, desc }) => (
              <li key={title} className="flex gap-3">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-[#E8600A]/10 text-[#E8600A]">
                  <Icon aria-hidden />
                </span>
                <div>
                  <h3 className="font-bold text-gray-950">{title}</h3>
                  <p className="mt-0.5 text-sm leading-relaxed text-gray-600">{desc}</p>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <Link href="/about" className="font-bold text-[#C8102E] underline-offset-4 hover:underline">
              More about us →
            </Link>
            {SITE.tripadvisor && (
              <a
                href={SITE.tripadvisor}
                target="_blank"
                rel="noopener noreferrer"
                className="font-bold text-gray-900 underline-offset-4 hover:underline"
              >
                Read our reviews on Tripadvisor →
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
