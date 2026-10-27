'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useEffect, useRef, useState } from 'react';
import { usePathname } from 'next/navigation';
import { FaChevronDown, FaEnvelope, FaLock, FaMapMarkerAlt, FaPhone, FaSun, FaWhatsapp } from 'react-icons/fa';
import { BsSunriseFill, BsSunsetFill } from 'react-icons/bs';
import type { IconType } from 'react-icons';
import { NAV, SITE, whatsappLink, type NavLink } from '@/lib/site';

const CRUISE_ICONS: Record<string, IconType> = {
  '/#sunrise': BsSunriseFill,
  '/#lunch': FaSun,
  '/#sunset': BsSunsetFill,
};

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
  // Desktop dropdown (by group label) and the mobile accordion, both closed by navigation.
  const [dropdown, setDropdown] = useState<string | null>(null);
  const [mobileGroup, setMobileGroup] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLLIElement>(null);
  const [hash, setHash] = useState('');
  // The panel sits flush under the header, whose height changes with breakpoint
  // (64px phone, 72px tablet) — measured rather than hard-coded.
  const headerRef = useRef<HTMLElement>(null);
  const [headerBottom, setHeaderBottom] = useState(64);

  useEffect(() => {
    const el = headerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setHeaderBottom(Math.round(el.getBoundingClientRect().bottom)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

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

  // Close the desktop dropdown on outside click or Escape.
  useEffect(() => {
    if (!dropdown) return;
    const onDown = (e: PointerEvent) => {
      if (!dropdownRef.current?.contains(e.target as Node)) setDropdown(null);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setDropdown(null);
    document.addEventListener('pointerdown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('pointerdown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [dropdown]);

  // While the mobile menu is open: lock page scroll, close on Escape, and close
  // if the viewport grows to desktop (e.g. a tablet rotated) so the page isn't
  // left locked. Lock <html> only: iOS Safari ignores overflow on <body>, and
  // locking both makes <body> a scroll container, which un-sticks the header.
  useEffect(() => {
    if (!open) return;
    const html = document.documentElement;
    const previous = html.style.overflow;
    html.style.overflow = 'hidden';
    const close = () => setOpenOnPath(null);
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && close();
    const desktop = window.matchMedia('(min-width: 1024px)');
    const onDesktop = (e: MediaQueryListEvent) => e.matches && close();
    window.addEventListener('keydown', onKey);
    desktop.addEventListener('change', onDesktop);
    return () => {
      html.style.overflow = previous;
      window.removeEventListener('keydown', onKey);
      desktop.removeEventListener('change', onDesktop);
    };
  }, [open]);

  if (pathname.startsWith('/booking')) return <CheckoutHeader />;

  const isActive = (href: string) => {
    if (href.startsWith('#')) return false;
    if (href.startsWith('/#')) return pathname === '/' && hash === href.slice(1);
    return pathname === href;
  };
  const groupActive = (links: NavLink[]) => links.some(({ href }) => isActive(href));
  const linkClass =
    'relative rounded-full px-3.5 py-2 text-[15px] font-medium text-gray-700 transition hover:bg-gray-100 hover:text-gray-950 aria-[current=page]:text-[#C8102E]';

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

      <header ref={headerRef} className={`sticky top-0 z-50 border-b bg-white/95 backdrop-blur transition-shadow ${scrolled ? 'border-gray-200 shadow-[0_4px_20px_-12px_rgba(0,0,0,0.25)]' : 'border-transparent'}`}>
        <nav className="container mx-auto flex h-16 items-center justify-between gap-4 px-4 md:h-[72px] md:px-6" aria-label="Main">
          <Logo />

          <ul className="hidden items-center gap-0.5 lg:flex">
            {NAV.map((item) =>
              'children' in item ? (
                <li
                  key={item.label}
                  ref={dropdown === item.label ? dropdownRef : undefined}
                  className="relative"
                  onMouseEnter={() => setDropdown(item.label)}
                  onMouseLeave={() => setDropdown(null)}
                >
                  <button
                    type="button"
                    onClick={() => setDropdown((d) => (d === item.label ? null : item.label))}
                    aria-expanded={dropdown === item.label}
                    aria-haspopup="true"
                    aria-current={groupActive(item.children) ? 'page' : undefined}
                    className={`${linkClass} inline-flex items-center gap-1.5`}
                  >
                    {item.label}
                    <FaChevronDown size={10} className={`transition-transform ${dropdown === item.label ? 'rotate-180' : ''}`} aria-hidden />
                  </button>
                  {/* pt bridges the gap so the hover doesn't drop between trigger and panel */}
                  <div
                    className={`absolute left-1/2 top-full w-72 -translate-x-1/2 pt-2 transition duration-150 ${
                      dropdown === item.label ? 'visible translate-y-0 opacity-100' : 'invisible -translate-y-1 opacity-0'
                    }`}
                  >
                    <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-[0_18px_40px_-16px_rgba(0,0,0,0.3)]">
                      <ul className="p-2">
                        {item.children.map(({ label, href, detail }) => {
                          const Icon = CRUISE_ICONS[href];
                          return (
                            <li key={href}>
                              <Link
                                href={href}
                                onClick={() => setDropdown(null)}
                                aria-current={isActive(href) ? 'page' : undefined}
                                className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition hover:bg-[#FFF5EC]"
                              >
                                {Icon && (
                                  <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[#FFF1E2] text-[#E8600A] transition group-hover:bg-[#E8600A] group-hover:text-white">
                                    <Icon size={16} aria-hidden />
                                  </span>
                                )}
                                <span className="min-w-0">
                                  <span className="block text-sm font-semibold text-gray-900 group-aria-[current=page]:text-[#C8102E]">{label}</span>
                                  {detail && <span className="block text-xs text-gray-500">{detail}</span>}
                                </span>
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                      <Link
                        href={item.overview.href}
                        onClick={() => setDropdown(null)}
                        className="flex items-center justify-between border-t border-gray-100 bg-gray-50 px-5 py-3 text-sm font-semibold text-[#C8102E] transition hover:bg-gray-100"
                      >
                        {item.overview.label}
                        <span aria-hidden>→</span>
                      </Link>
                    </div>
                  </div>
                </li>
              ) : (
                <li key={item.href}>
                  <Link href={item.href} aria-current={isActive(item.href) ? 'page' : undefined} className={linkClass}>
                    {item.label}
                  </Link>
                </li>
              ),
            )}
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
          inert={!open}
          style={{ top: headerBottom }}
          className={`fixed inset-x-0 bottom-0 z-50 overflow-y-auto overscroll-contain border-t border-gray-100 bg-white transition-[opacity,transform,visibility] duration-200 ease-out lg:hidden ${
            open ? 'visible translate-y-0 opacity-100' : 'invisible -translate-y-2 opacity-0'
          }`}
        >
          <ul className="container mx-auto px-4 py-3">
            {NAV.map((item) =>
              'children' in item ? (
                <li key={item.label} className="border-b border-gray-100">
                  <button
                    type="button"
                    onClick={() => setMobileGroup((g) => (g === item.label ? null : item.label))}
                    aria-expanded={mobileGroup === item.label}
                    aria-controls="mobile-cruises"
                    className={`flex w-full items-center justify-between py-4 text-lg font-medium ${groupActive(item.children) ? 'text-[#C8102E]' : 'text-gray-900'}`}
                  >
                    {item.label}
                    <FaChevronDown size={14} className={`text-gray-400 transition-transform ${mobileGroup === item.label ? 'rotate-180' : ''}`} aria-hidden />
                  </button>
                  <div
                    id="mobile-cruises"
                    className={`grid transition-[grid-template-rows] duration-200 ${mobileGroup === item.label ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'}`}
                  >
                    <ul className="overflow-hidden" inert={mobileGroup !== item.label}>
                      {[...item.children, item.overview].map(({ label, href, detail }) => {
                        const Icon = CRUISE_ICONS[href];
                        return (
                          <li key={href}>
                            <Link
                              href={href}
                              onClick={() => setOpen(false)}
                              aria-current={isActive(href) ? 'page' : undefined}
                              className="flex items-center gap-3 rounded-xl px-2 py-3 text-base text-gray-800 aria-[current=page]:text-[#C8102E]"
                            >
                              <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-[#FFF1E2] text-[#E8600A]">
                                {Icon ? <Icon size={16} aria-hidden /> : <span aria-hidden>→</span>}
                              </span>
                              <span>
                                <span className="block font-semibold">{label}</span>
                                {detail && <span className="block text-xs text-gray-500">{detail}</span>}
                              </span>
                            </Link>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                </li>
              ) : (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    onClick={() => setOpen(false)}
                    aria-current={isActive(item.href) ? 'page' : undefined}
                    className="flex items-center justify-between border-b border-gray-100 py-4 text-lg font-medium text-gray-900 aria-[current=page]:text-[#C8102E]"
                  >
                    {item.label}
                    <span className="text-gray-300" aria-hidden>›</span>
                  </Link>
                </li>
              ),
            )}
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
