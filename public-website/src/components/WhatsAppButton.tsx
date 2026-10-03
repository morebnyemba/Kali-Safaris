'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { FaWhatsapp } from 'react-icons/fa';
import { whatsappLink } from '@/lib/site';

/**
 * Desktop: floating chat button. Phones: a slim bottom action bar instead —
 * a floating bubble on a 390px screen sits on top of right-aligned buttons.
 * The bar reserves its own height at the end of the page so it never hides
 * the footer. Hidden in checkout, where it would cover the pay buttons.
 */
export default function WhatsAppButton() {
  const pathname = usePathname();
  const [pastHero, setPastHero] = useState(false);

  useEffect(() => {
    // The hero already shows both actions; only bring the bar in after it.
    const onScroll = () => setPastHero(window.scrollY > window.innerHeight * 0.6);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  if (pathname.startsWith('/booking')) return null;

  return (
    <>
      <a
        href={whatsappLink()}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Chat with us on WhatsApp"
        className="group fixed bottom-6 right-6 z-40 hidden items-center gap-2 rounded-full bg-[#25D366] p-3.5 text-white shadow-[0_10px_30px_-8px_rgba(18,140,126,0.7)] transition hover:bg-[#1EBE5A] md:flex"
      >
        <span className="absolute inset-0 -z-10 animate-ping rounded-full bg-[#25D366]/40 [animation-iteration-count:3]" aria-hidden />
        <FaWhatsapp size={28} aria-hidden />
        <span className="max-w-0 overflow-hidden whitespace-nowrap text-sm font-semibold transition-all duration-300 group-hover:max-w-40 group-hover:pr-1">
          Chat with us
        </span>
      </a>

      <div className="h-[72px] bg-[#0A0A0A] md:hidden" aria-hidden />
      <div
        className={`fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white/95 px-4 pb-[calc(env(safe-area-inset-bottom)+12px)] pt-3 backdrop-blur transition-transform duration-300 md:hidden ${
          pastHero ? 'translate-y-0' : 'translate-y-full'
        }`}
        inert={!pastHero}
      >
        <div className="flex gap-3">
          <Link href="/booking" className="flex flex-1 items-center justify-center rounded-full bg-[#C8102E] py-3 text-sm font-bold text-white">
            Book a cruise
          </Link>
          <a
            href={whatsappLink()}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 rounded-full border border-gray-300 px-5 py-3 text-sm font-bold text-gray-900"
          >
            <FaWhatsapp className="text-lg text-[#25D366]" aria-hidden /> WhatsApp
          </a>
        </div>
      </div>
    </>
  );
}
