'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { FaEnvelope, FaLock, FaMapMarkerAlt, FaPhone, FaWhatsapp } from 'react-icons/fa';
import { NAV_LINKS, SITE, whatsappLink } from '@/lib/site';

function Logo({ className = 'w-[132px] md:w-[150px]' }: { className?: string }) {
  return (
    <Link href="/" className="block shrink-0" aria-label="Kalai Safaris home">
      <Image src="/images/kalailogo.png" alt="Kalai Safaris" width={1176} height={307} priority className={`h-auto ${className}`} />
    </Link>
  );
}

/** Minimal header for the booking/payment flow: brand, reassurance, help — no exits into the site. */
function CheckoutHeader() {
  return (
    <header className="sticky top-0 z-50 h-14 border-b border-gray-200 bg-white/95 backdrop-blur">
      <div className="container mx-auto flex h-full items-center justify-between gap-3 px-4 md:px-6">
        <Logo className="w-[112px] md:w-[128px]" />
        <div className="flex items-center gap-2 text-xs font-semibold text-gray-600 sm:gap-4">
          <span className="hidden items-center gap-1.5 sm:inline-flex">
            <FaLock className="text-emerald-600" aria-hidden /> Secure checkout
          </span>
          <a
            href={whatsappLink("Hi, I need help with my booking.")}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 px-3 py-1.5 transition hover:border-[#25D366] hover:text-[#128C7E]"
          >
            <FaWhatsapp className="text-[#25D366]" aria-hidden /> Need help?
          </a>
        </div>
      </div>
    </header>
  );
}

export default function Header() {
  const pathname = usePathname();
  // The menu is open only for the path it was opened on, so navigating closes it.
  const [openOnPath, setOpenOnPath] = useState<string | null>(null);
  const open = openOnPath === pathname;
  const setOpen = (value: boolean | ((v: boolean) => boolean)) =>
    setOpenOnPath((typeof value === 'function' ? value(open) : value) ? pathname : null);
  const [scrolled, setScrolled] = useState(false);
  const [hash, setHash] = useState('');

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    const onHash = () => setHash(window.location.hash);
    onScroll();
    onHash();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('hashchange', onHash);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  // Lock page scroll while the mobile menu is open; close it on Escape.
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpenOnPath(null);
    window.addEventListener('keydown', onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener('keydown', onKey);
    };
  }, [open]);

  if (pathname.startsWith('/booking')) return <CheckoutHeader />;

  const isActive = (href: string) => {
    if (href.startsWith('#')) return false;
    if (href.startsWith('/#')) return pathname === '/' && hash === href.slice(1);
    return pathname === href;
  };

  return (
    <>
      {/* Contact strip — desktop only, scrolls away */}
      <div className="hidden bg-[#0A0A0A] text-white/75 lg:block">
        <div className="container mx-auto flex items-center justify-between px-6 py-2 text-xs">
          <a href={SITE.mapsUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 hover:text-white">
            <FaMapMarkerAlt className="text-[#E09A18]" aria-hidden /> {SITE.address}
          </a>
          <div className="flex items-center gap-5">
            <a href={SITE.phoneHref} className="inline-flex items-center gap-2 hover:text-white">
              <FaPhone className="text-[#E09A18]" aria-hidden /> {SITE.phoneDisplay}
            </a>
            <a href={`mailto:${SITE.email}`} className="inline-flex items-center gap-2 hover:text-white">
              <FaEnvelope className="text-[#E09A18]" aria-hidden /> {SITE.email}
            </a>
          </div>
        </div>
      </div>

      <header className={`sticky top-0 z-50 border-b bg-white/95 backdrop-blur transition-shadow ${scrolled ? 'border-gray-200 shadow-[0_4px_20px_-12px_rgba(0,0,0,0.25)]' : 'border-transparent'}`}>
        <nav className="container mx-auto flex h-16 items-center justify-between gap-4 px-4 md:h-[72px] md:px-6" aria-label="Main">
          <Logo />

          <ul className="hidden items-center gap-1 lg:flex">
            {NAV_LINKS.map(({ label, href }) => (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={isActive(href) ? 'page' : undefined}
                  className="relative rounded-full px-3 py-2 text-[15px] font-medium text-gray-700 transition hover:bg-gray-100 hover:text-gray-950 aria-[current=page]:text-[#C8102E]"
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-2">
            <a
              href={whatsappLink()}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden size-10 items-center justify-center rounded-full text-[#128C7E] transition hover:bg-[#25D366]/10 sm:inline-flex"
              aria-label="Chat with us on WhatsApp"
            >
              <FaWhatsapp size={22} />
            </a>
            <Link
              href="/booking"
              className="hidden rounded-full bg-[#C8102E] px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-[#A00D24] sm:inline-flex"
            >
              Book a cruise
            </Link>
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              className="inline-flex size-10 items-center justify-center rounded-full text-gray-900 transition hover:bg-gray-100 lg:hidden"
              aria-label={open ? 'Close menu' : 'Open menu'}
              aria-expanded={open}
              aria-controls="mobile-menu"
            >
              <span className="relative block h-3.5 w-5" aria-hidden>
                <span className={`absolute left-0 top-0 h-0.5 w-5 rounded bg-current transition ${open ? 'translate-y-1.5 rotate-45' : ''}`} />
                <span className={`absolute left-0 top-1.5 h-0.5 w-5 rounded bg-current transition ${open ? 'opacity-0' : ''}`} />
                <span className={`absolute left-0 top-3 h-0.5 w-5 rounded bg-current transition ${open ? '-translate-y-1.5 -rotate-45' : ''}`} />
              </span>
            </button>
          </div>
        </nav>

      </header>

      {/* Mobile menu */}
        <div
          id="mobile-menu"
          hidden={!open}
          className="fixed inset-x-0 bottom-0 top-16 z-50 overflow-y-auto border-t border-gray-100 bg-white lg:hidden"
        >
          <ul className="container mx-auto px-4 py-3">
            {NAV_LINKS.map(({ label, href }) => (
              <li key={href}>
                <Link
                  href={href}
                  onClick={() => setOpen(false)}
                  aria-current={isActive(href) ? 'page' : undefined}
                  className="flex items-center justify-between border-b border-gray-100 py-4 text-lg font-medium text-gray-900 aria-[current=page]:text-[#C8102E]"
                >
                  {label}
                  <span className="text-gray-300" aria-hidden>›</span>
                </Link>
              </li>
            ))}
          </ul>
          <div className="container mx-auto space-y-3 px-4 pb-8 pt-2">
            <Link href="/booking" onClick={() => setOpen(false)} className="block rounded-full bg-[#C8102E] py-3.5 text-center font-bold text-white">
              Book a cruise
            </Link>
            <div className="grid grid-cols-2 gap-3">
              <a href={SITE.phoneHref} className="flex items-center justify-center gap-2 rounded-full border border-gray-200 py-3 text-sm font-semibold text-gray-800">
                <FaPhone className="text-[#E8600A]" aria-hidden /> Call us
              </a>
              <a href={whatsappLink()} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 rounded-full border border-gray-200 py-3 text-sm font-semibold text-gray-800">
                <FaWhatsapp className="text-[#25D366]" aria-hidden /> WhatsApp
              </a>
            </div>
          </div>
        </div>
    </>
  );
}
