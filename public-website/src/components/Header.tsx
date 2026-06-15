'use client';

import Link from "next/link";
import Image from "next/image";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (pathname.startsWith('/booking')) return null;

  return (
    <header
      className={`w-full sticky top-0 z-50 transition-all duration-500 ${
        scrolled
          ? "bg-[#0A0A0A]/97 backdrop-blur-md shadow-xl border-b border-white/10"
          : "backdrop-blur-md bg-black/25 border-b border-white/10 shadow-lg"
      }`}
    >
      <nav className="container mx-auto relative flex items-center justify-between py-1.5 px-4 md:py-2 md:px-6">
        {/* Logo */}
        <Link href="/" className="leading-none flex-shrink-0 hover:opacity-80 transition-opacity">
          <Image
            src="/images/kalailogo.png"
            alt="Kalai Safari Logo"
            width={1176}
            height={307}
            className="block h-auto w-[120px] md:w-[160px]"
            priority
            style={{ imageRendering: 'crisp-edges' }}
          />
        </Link>

        {/* Desktop Navigation */}
        <ul className="hidden lg:flex gap-1 xl:gap-2 text-sm md:text-base font-medium items-center">
          {[
            { label: "About Us", href: "/" },
            { label: "Sunrise", href: "/#sunrise" },
            { label: "Lunch", href: "/#lunch" },
            { label: "Sunset", href: "/#sunset" },
            { label: "Contact", href: "/#contact" },
            { label: "Gallery", href: "/gallery" },
          ].map(({ label, href }) => (
            <li key={label}>
              <Link
                href={href}
                className="text-white/90 font-medium px-3 py-1.5 rounded-full transition-all duration-200 hover:bg-white/10 hover:text-white"
              >
                {label}
              </Link>
            </li>
          ))}
          <li>
            <Link
              href="/booking"
              className="bg-[#C8102E] hover:bg-[#E8173A] text-white px-4 py-2 rounded-full font-bold transition-all duration-300 shadow-lg hover:shadow-red-500/30 hover:-translate-y-0.5 transform"
            >
              Book Now!
            </Link>
          </li>
        </ul>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="lg:hidden relative w-8 h-8 flex flex-col justify-center items-center gap-1 hover:opacity-70 transition-opacity"
          aria-label="Toggle menu"
        >
          <span className={`w-6 h-0.5 bg-white rounded-full transition-all duration-300 ${isOpen ? 'rotate-45 translate-y-2' : ''}`} />
          <span className={`w-6 h-0.5 bg-white rounded-full transition-all duration-300 ${isOpen ? 'opacity-0' : ''}`} />
          <span className={`w-6 h-0.5 bg-white rounded-full transition-all duration-300 ${isOpen ? '-rotate-45 -translate-y-2' : ''}`} />
        </button>
      </nav>

      {/* Mobile Navigation */}
      <div className={`lg:hidden overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}`}>
        <div className="bg-[#0A0A0A]/97 backdrop-blur-lg border-t border-white/10">
          <ul className="container mx-auto flex flex-col gap-2 py-4 px-4">
            {[
              { label: "About Us", href: "/" },
              { label: "Sunrise Cruise", href: "/#sunrise" },
              { label: "Lunch Cruise", href: "/#lunch" },
              { label: "Sunset Cruise", href: "/#sunset" },
              { label: "Contact Us", href: "/#contact" },
              { label: "Gallery", href: "/gallery" },
            ].map(({ label, href }) => (
              <li key={label}>
                <Link
                  href={href}
                  onClick={() => setIsOpen(false)}
                  className="block text-white/90 hover:text-white hover:bg-white/10 px-4 py-3 rounded-full transition-all text-center font-medium"
                >
                  {label}
                </Link>
              </li>
            ))}
            <li>
              <Link
                href="/booking"
                onClick={() => setIsOpen(false)}
                className="block bg-[#C8102E] hover:bg-[#E8173A] text-white px-4 py-3 rounded-full transition-all text-center font-bold"
              >
                Book Now!
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </header>
  );
}
