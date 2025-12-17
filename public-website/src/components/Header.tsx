'use client';

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";

export default function Header() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="w-full sticky top-0 z-50 backdrop-blur-md bg-gradient-to-b from-white/20 via-white/10 to-transparent border-b border-white/10 shadow-lg">
      {/* Glassmorphism background effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-white/5 backdrop-blur-xl"></div>
      </div>

      <nav className="container mx-auto relative flex items-center justify-between py-3 px-4 md:py-4 md:px-6">
        {/* Logo */}
        <Link href="/" className="flex-shrink-0 hover:opacity-80 transition-opacity">
          <Image 
            src="/images/kalai_safari_logo.PNG" 
            alt="Kalai Safari Logo" 
            width={80} 
            height={80}
            className="rounded-2xl md:w-[100px] md:h-[100px] w-[80px] h-[80px]"
          />
        </Link>

        {/* Desktop Navigation */}
        <ul className="hidden lg:flex gap-2 xl:gap-4 text-sm md:text-base font-medium items-center">
          <li>
            <Link href="/" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              About Us
            </Link>
          </li>
          <li>
            <Link href="/#sunrise" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              Sunrise
            </Link>
          </li>
          <li>
            <Link href="/#lunch" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              Lunch
            </Link>
          </li>
          <li>
            <Link href="/#sunset" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              Sunset
            </Link>
          </li>
          <li>
            <Link href="/#contact" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              Contact
            </Link>
          </li>
          <li>
            <Link href="/gallery" className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5">
              Gallery
            </Link>
          </li>
          <li>
            <Link href="/booking" className="bg-gradient-to-r from-[#ff6b35] to-[#ff5722] hover:from-[#ff5722] hover:to-[#e64a19] text-white px-3 md:px-4 py-2 rounded-full transition-all duration-300 hover:shadow-lg transform hover:-translate-y-0.5 font-bold">
              Book Now!
            </Link>
          </li>
        </ul>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="lg:hidden relative w-8 h-8 flex flex-col justify-center items-center gap-1 hover:opacity-70 transition-opacity"
        >
          <span className={`w-6 h-0.5 bg-black rounded-full transition-all duration-300 ${isOpen ? 'rotate-45 translate-y-2' : ''}`}></span>
          <span className={`w-6 h-0.5 bg-black rounded-full transition-all duration-300 ${isOpen ? 'opacity-0' : ''}`}></span>
          <span className={`w-6 h-0.5 bg-black rounded-full transition-all duration-300 ${isOpen ? '-rotate-45 -translate-y-2' : ''}`}></span>
        </button>
      </nav>

      {/* Mobile Navigation */}
      {isOpen && (
        <div className="lg:hidden bg-white/30 backdrop-blur-lg border-t border-white/10">
          <ul className="container mx-auto flex flex-col gap-2 py-4 px-4">
            <li>
              <Link href="/" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                About Us
              </Link>
            </li>
            <li>
              <Link href="/#sunrise" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                Sunrise Cruise
              </Link>
            </li>
            <li>
              <Link href="/#lunch" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                Lunch Cruise
              </Link>
            </li>
            <li>
              <Link href="/#sunset" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                Sunset Cruise
              </Link>
            </li>
            <li>
              <Link href="/#contact" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                Contact Us
              </Link>
            </li>
            <li>
              <Link href="/gallery" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-4 py-3 rounded-full transition-all duration-300 text-center font-medium">
                Gallery
              </Link>
            </li>
            <li>
              <Link href="/booking" onClick={() => setIsOpen(false)} className="block bg-gradient-to-r from-[#ff6b35] to-[#ff5722] hover:from-[#ff5722] hover:to-[#e64a19] text-white px-4 py-3 rounded-full transition-all duration-300 text-center font-bold">
                Book Now!
              </Link>
            </li>
          </ul>
        </div>
      )}
    </header>
  );
}
