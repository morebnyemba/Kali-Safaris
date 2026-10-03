'use client';

import { usePathname } from 'next/navigation';
import { FaWhatsapp } from 'react-icons/fa';
import { whatsappLink } from '@/lib/site';

/** Floating chat button. Hidden in checkout, where it would cover the pay buttons. */
export default function WhatsAppButton() {
  const pathname = usePathname();
  if (pathname.startsWith('/booking')) return null;

  return (
    <a
      href={whatsappLink()}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Chat with us on WhatsApp"
      className="group fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full bg-[#25D366] p-3.5 text-white shadow-[0_10px_30px_-8px_rgba(18,140,126,0.7)] transition hover:bg-[#1EBE5A] md:bottom-6 md:right-6"
    >
      <span className="absolute inset-0 -z-10 animate-ping rounded-full bg-[#25D366]/40 [animation-iteration-count:3]" aria-hidden />
      <FaWhatsapp size={28} aria-hidden />
      <span className="hidden max-w-0 overflow-hidden whitespace-nowrap text-sm font-semibold transition-all duration-300 group-hover:max-w-40 group-hover:pr-1 md:inline">
        Chat with us
      </span>
    </a>
  );
}
