import Link from 'next/link';
import Image from 'next/image';
import { FaCcMastercard, FaCcVisa, FaDirections, FaEnvelope, FaFacebook, FaMapMarkerAlt, FaPhone, FaSun, FaWhatsapp } from 'react-icons/fa';
import { BsSunriseFill, BsSunsetFill } from 'react-icons/bs';
import { NAV_LINKS, SITE, whatsappLink } from '@/lib/site';

const HOURS = [
  { icon: BsSunriseFill, name: 'Sunrise cruise', time: '06:00 – 08:00' },
  { icon: FaSun, name: 'Lunch cruise', time: '12:00 – 14:00' },
  { icon: BsSunsetFill, name: 'Sunset cruise', time: '16:00 – after sunset' },
];

function Heading({ children }: { children: React.ReactNode }) {
  return <h2 className="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-[#E09A18]">{children}</h2>;
}

export default function FooterSection() {
  const year = new Date().getFullYear();

  return (
    <footer id="contact" className="relative w-full overflow-hidden bg-[#0A0A0A] text-white/80">
      <div className="pointer-events-none absolute -right-32 -top-32 size-96 rounded-full bg-[#E8600A]/10 blur-3xl" aria-hidden />

      <div className="container relative mx-auto px-6 pb-8 pt-14">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 lg:grid-cols-[1.3fr_0.8fr_1.1fr_1fr]">
          {/* Brand */}
          <div className="space-y-5">
            <Link href="/" className="inline-flex items-center gap-3" aria-label="Kalai Safaris home">
              <span className="flex size-12 items-center justify-center rounded-full bg-white p-1.5">
                <Image src="/images/kalailogo-leftmark.png" alt="" width={640} height={306} className="h-auto w-full" />
              </span>
              <span className="text-xl font-bold tracking-wide text-white">Kalai Safaris</span>
            </Link>
            <p className="max-w-xs text-sm leading-relaxed text-white/60">
              Relaxed safari cruises on the Zambezi River above Victoria Falls — wildlife, sunsets and good company since 2019.
            </p>
            <div className="flex gap-2">
              <a href={SITE.facebook} target="_blank" rel="noopener noreferrer" aria-label="Kalai Safaris on Facebook"
                className="flex size-10 items-center justify-center rounded-full border border-white/15 transition hover:border-[#1877F2] hover:bg-[#1877F2] hover:text-white">
                <FaFacebook size={18} />
              </a>
              <a href={whatsappLink()} target="_blank" rel="noopener noreferrer" aria-label="Chat on WhatsApp"
                className="flex size-10 items-center justify-center rounded-full border border-white/15 transition hover:border-[#25D366] hover:bg-[#25D366] hover:text-white">
                <FaWhatsapp size={18} />
              </a>
            </div>
          </div>

          {/* Explore */}
          <nav aria-label="Footer">
            <Heading>Explore</Heading>
            <ul className="space-y-2.5 text-sm">
              {NAV_LINKS.filter((l) => l.href !== '#contact').map(({ label, href }) => (
                <li key={href}><Link href={href} className="transition hover:text-white">{label}</Link></li>
              ))}
              <li><Link href="/booking" className="font-semibold text-[#E09A18] transition hover:text-[#F47B1A]">Book a cruise →</Link></li>
            </ul>
          </nav>

          {/* Contact */}
          <div>
            <Heading>Get in touch</Heading>
            <ul className="space-y-3.5 text-sm">
              <li>
                <a href={SITE.mapsUrl} target="_blank" rel="noopener noreferrer" className="flex items-start gap-3 transition hover:text-white">
                  <FaMapMarkerAlt className="mt-0.5 shrink-0 text-[#E09A18]" aria-hidden /> {SITE.address}
                </a>
              </li>
              <li>
                <a href={SITE.phoneHref} className="flex items-center gap-3 transition hover:text-white">
                  <FaPhone className="shrink-0 text-[#E09A18]" aria-hidden /> {SITE.phoneDisplay}
                </a>
              </li>
              <li>
                <a href={`mailto:${SITE.email}`} className="flex items-center gap-3 break-all transition hover:text-white">
                  <FaEnvelope className="shrink-0 text-[#E09A18]" aria-hidden /> {SITE.email}
                </a>
              </li>
              <li>
                <a href={SITE.mapsUrl} target="_blank" rel="noopener noreferrer"
                  className="mt-1 inline-flex items-center gap-2 rounded-full border border-white/15 px-4 py-2 text-xs font-semibold text-white transition hover:border-[#E09A18] hover:text-[#E09A18]">
                  <FaDirections aria-hidden /> Get directions
                </a>
              </li>
            </ul>
          </div>

          {/* Hours */}
          <div>
            <Heading>Cruise times</Heading>
            <ul className="divide-y divide-white/10 rounded-xl border border-white/10 bg-white/[0.03] text-sm">
              {HOURS.map(({ icon: Icon, name, time }) => (
                <li key={name} className="flex items-center gap-3 px-4 py-3">
                  <Icon className="shrink-0 text-[#E09A18]" aria-hidden />
                  <span className="flex-1 text-white">{name}</span>
                  <span className="text-xs tabular-nums text-white/55">{time}</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-white/45">All cruises depart from our riverside jetty.</p>
          </div>
        </div>

        {/* Payments */}
        <div className="mt-12 flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs uppercase tracking-[0.16em] text-white/45">Secure payments</p>
          <ul className="flex flex-wrap items-center gap-2" aria-label="Accepted payment methods">
            <li><FaCcVisa className="text-3xl text-white/80" title="Visa" aria-label="Visa" /></li>
            <li><FaCcMastercard className="text-3xl text-white/80" title="Mastercard" aria-label="Mastercard" /></li>
            {['ZimSwitch', 'EcoCash', 'Omari'].map((m) => (
              <li key={m} className="rounded-md border border-white/15 px-2 py-1 text-[11px] font-semibold tracking-wide text-white/80">{m}</li>
            ))}
          </ul>
        </div>

        <div className="mt-6 flex flex-col gap-2 text-xs text-white/45 sm:flex-row sm:items-center sm:justify-between">
          <p>© 2019–{year} Kalai Safaris. All rights reserved.</p>
          <p>
            Website by{' '}
            <a href="https://slykertech.co.zw" target="_blank" rel="noopener noreferrer" className="text-white/70 underline-offset-2 transition hover:text-white hover:underline">
              Slyker Tech Web Services
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
