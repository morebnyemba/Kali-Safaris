'use client';

import Image from "next/image";
import { useState } from "react";
import type { IconType } from "react-icons";
import { FaShip, FaAnchor, FaTimes } from "react-icons/fa";
import { BsSunriseFill, BsSunsetFill } from "react-icons/bs";
import FooterSection from "@/components/FooterSection";

const galleryImages = [
  { src: "/images/kalai_intro.jpeg", alt: "Kalai Safari Enigma Boat", category: "boat" },
  { src: "/images/sunrise.jpeg", alt: "Sunrise on the Zambezi", category: "sunrise" },
  { src: "/images/sunset.jpeg", alt: "Sunset Cruise", category: "sunset" },
  { src: "/images/Kalai Sunset background shot.jpeg", alt: "Golden Sunset on the Zambezi", category: "sunset" },
  { src: "/images/work_no_play.jpeg", alt: "Lunch Cruise Experience", category: "boat" },
  { src: "/images/jetty_venue.jpg", alt: "Jetty Venue", category: "jetty" },
  { src: "/images/Kalai Safaris interior chairs.jpeg", alt: "Boat Interior Setup", category: "boat" },
  { src: "/images/Kalai Safaris jetty site.jpeg", alt: "Jetty Site View", category: "jetty" },
  { src: "/images/cruise boat.jpg", alt: "Cruise Boat on Water", category: "boat" },
  { src: "/images/Boats .jpg", alt: "Safari Boats Docked", category: "boat" },
  { src: "/images/jetty site 2.jpg", alt: "Riverside Jetty", category: "jetty" },
  { src: "/images/jetty 3.jpg", alt: "Jetty Evening View", category: "jetty" },
  { src: "/images/Kalai Safaris Rendezvous.jpeg", alt: "Rendezvous Vessel", category: "boat" },
  { src: "/images/Kalai Safaris On the River.jpeg", alt: "Cruising on the Zambezi", category: "boat" },
  { src: "/images/cruise with palms.jpg", alt: "Cruise with Palm Trees", category: "boat" },
  { src: "/images/boat entry.jpg", alt: "Boarding the Boat", category: "boat" },
];

const categories: { key: string; label: string; icon?: IconType }[] = [
  { key: "all", label: "All" },
  { key: "boat", label: "Boats & Cruises", icon: FaShip },
  { key: "sunset", label: "Sunset", icon: BsSunsetFill },
  { key: "sunrise", label: "Sunrise", icon: BsSunriseFill },
  { key: "jetty", label: "Jetty Venue", icon: FaAnchor },
];

export default function GalleryPage() {
  const [activeCategory, setActiveCategory] = useState("all");
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  const filtered = activeCategory === "all"
    ? galleryImages
    : galleryImages.filter((img) => img.category === activeCategory);

  return (
    <div className="min-h-screen">
      {/* Hero Banner */}
      <section className="relative h-[35vh] md:h-[45vh] flex items-center justify-center overflow-hidden">
        <Image
          src="/images/Kalai Safaris Enigma.jpeg"
          alt="Kalai Safaris Gallery"
          fill
          className="object-cover"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/70" />
        <div className="relative text-center text-white px-6">
          <p className="text-sm uppercase tracking-[0.3em] text-[#E09A18] font-semibold mb-3">
            Explore
          </p>
          <h1 className="text-4xl md:text-6xl font-black drop-shadow-lg">
            Gallery
          </h1>
        </div>
      </section>

      {/* Gallery Grid */}
      <section className="py-16 bg-gradient-to-b from-white via-[#FFF9F5] to-white relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 right-10 w-48 h-48 bg-[#E09A18]/15 blur-3xl rounded-full" />
          <div className="absolute bottom-10 left-10 w-56 h-56 bg-[#E8600A]/10 blur-3xl rounded-full" />
        </div>

        <div className="container mx-auto px-6 relative">
          {/* Category Filters */}
          <div className="flex flex-wrap justify-center gap-2 mb-10">
            {categories.map((cat) => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`px-4 py-2 rounded-full text-sm font-semibold transition-all duration-300 ${
                  activeCategory === cat.key
                    ? "bg-gradient-to-r from-[#E09A18] to-[#E8600A] text-black shadow-lg"
                    : "bg-white/60 backdrop-blur-md border border-white/50 text-gray-700 hover:border-[#E8600A]/50"
                }`}
              >
                {cat.icon && <cat.icon size={14} className="inline mr-1" />}{cat.label}
              </button>
            ))}
          </div>

          {/* Image Grid */}
          <div className="columns-1 sm:columns-2 lg:columns-3 gap-4 space-y-4">
            {filtered.map((image, index) => (
              <div
                key={index}
                className="relative break-inside-avoid overflow-hidden rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 group cursor-pointer"
                onClick={() => setLightboxImage(image.src)}
              >
                <Image
                  src={image.src}
                  alt={image.alt}
                  width={600}
                  height={400}
                  className="w-full h-auto object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
                  <p className="text-white text-sm font-medium drop-shadow-md">{image.alt}</p>
                </div>
              </div>
            ))}
          </div>

          {filtered.length === 0 && (
            <p className="text-center text-gray-500 py-12">No images in this category yet.</p>
          )}
        </div>
      </section>

      {/* Lightbox */}
      {lightboxImage && (
        <div
          className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in"
          onClick={() => setLightboxImage(null)}
        >
          <button
            className="absolute top-6 right-6 text-white/80 hover:text-white transition text-3xl font-bold z-10"
            onClick={() => setLightboxImage(null)}
            aria-label="Close lightbox"
          >
            <FaTimes size={24} />
          </button>
          <div className="relative max-w-5xl max-h-[85vh] w-full" onClick={(e) => e.stopPropagation()}>
            <Image
              src={lightboxImage}
              alt="Gallery image full view"
              width={1200}
              height={800}
              className="w-full h-auto max-h-[85vh] object-contain rounded-lg"
            />
          </div>
        </div>
      )}

      <FooterSection />
    </div>
  );
}
