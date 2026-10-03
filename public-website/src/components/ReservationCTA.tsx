import Link from "next/link";
import { FaCreditCard, FaDirections, FaInfoCircle, FaSuitcase, FaWhatsapp } from "react-icons/fa";
import { SITE, whatsappLink } from "@/lib/site";

const tips = [
  {
    icon: FaDirections,
    title: "Meeting point",
    body: SITE.address + ". Please arrive a little before your departure time.",
    link: { href: SITE.mapsUrl, label: "Get directions" },
  },
  { icon: FaSuitcase, title: "What to bring", body: "Hat, sunscreen, a light jacket for evening cruises, camera and binoculars." },
  { icon: FaCreditCard, title: "Paying", body: "Book online and pay by Visa, Mastercard, ZimSwitch, EcoCash or Omari. Your booking is confirmed as soon as payment clears." },
  { icon: FaInfoCircle, title: "Park fees", body: "The National Parks river usage fee is not included in the cruise price." },
];

/** Practical "plan your visit" block + final call to action. */
export default function ReservationCTA() {
  return (
    <section id="reserve" className="scroll-mt-20 bg-[#0A0A0A] py-16 text-white md:py-24">
      <div className="container mx-auto px-5 md:px-6">
        <div className="mb-10 max-w-2xl md:mb-12">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#F4B544]">Plan your visit</p>
          <h2 className="text-3xl font-extrabold tracking-tight md:text-4xl">Good to know before you go</h2>
        </div>

        <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {tips.map(({ icon: Icon, title, body, link }) => (
            <li key={title} className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <Icon className="mb-3 text-xl text-[#F4B544]" aria-hidden />
              <h3 className="font-bold">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-white/70">{body}</p>
              {link && (
                <a href={link.href} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-sm font-semibold text-[#F4B544] underline-offset-4 hover:underline">
                  {link.label} →
                </a>
              )}
            </li>
          ))}
        </ul>

        <div className="mt-12 flex flex-col items-start justify-between gap-6 rounded-2xl bg-[#C8102E] p-6 md:flex-row md:items-center md:p-8">
          <div>
            <h3 className="text-2xl font-extrabold">Ready to get on the river?</h3>
            <p className="mt-1 text-white/85">Book online in a few minutes, or message us and we&apos;ll arrange it for you.</p>
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <Link href="/booking" className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 font-bold text-[#C8102E] transition hover:bg-white/90">
              Book a cruise
            </Link>
            <a
              href={whatsappLink()}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/40 px-6 py-3 font-bold text-white transition hover:bg-white/10"
            >
              <FaWhatsapp aria-hidden /> WhatsApp us
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
