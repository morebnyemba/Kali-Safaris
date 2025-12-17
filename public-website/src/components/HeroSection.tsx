"use client";

import { useState, useEffect } from "react";
import Image from "next/image";

const slides = [
  {
    image: "/images/slider/1.jpeg",
    title: "Affordable Cruise On The Zambezi River",
  },
  {
    image: "/images/slider/hipo.jpg",
    title: "Experience",
    subtitle: "Peaceful and adventurous cruise.",
  },
  {
    image: "/images/slider/sun.jpg",
    title: "Sustainable Tourism",
  },
  {
    image: "/images/slider/drink.jpg",
    title: "Zambezi River Cruise Safari",
  },
];

interface TypedTextProps {
  text: string;
  speed?: number;
  onComplete?: () => void;
}

function TypedText({ text, speed = 50, onComplete }: TypedTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (isComplete) return;

    let index = 0;
    const timer = setInterval(() => {
      if (index <= text.length) {
        setDisplayedText(text.slice(0, index));
        index++;
      } else {
        setIsComplete(true);
        clearInterval(timer);
        onComplete?.();
      }
    }, speed);

    return () => clearInterval(timer);
  }, [text, speed, isComplete, onComplete]);

  return <>{displayedText}</>;
}

export default function HeroSection() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [key, setKey] = useState(0);

  useEffect(() => {
    if (isPaused) return;
    
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
      setKey((prev) => prev + 1);
    }, 6500);
    
    return () => clearInterval(timer);
  }, [isPaused]);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
    setKey((prev) => prev + 1);
    setIsPaused(true);
    setTimeout(() => setIsPaused(false), 10000);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
    setKey((prev) => prev + 1);
    setIsPaused(true);
    setTimeout(() => setIsPaused(false), 10000);
  };

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
    setKey((prev) => prev + 1);
    setIsPaused(true);
    setTimeout(() => setIsPaused(false), 10000);
  };

  return (
    <section className="relative w-full h-screen overflow-hidden group">
      {/* Slides */}
      {slides.map((slide, index) => (
        <div
          key={index}
          className={`absolute inset-0 transition-opacity duration-1000 ${
            index === currentSlide ? "opacity-100" : "opacity-0"
          }`}
        >
          <Image
            src={slide.image}
            alt={slide.title}
            fill
            className="object-cover"
            priority={index === 0}
            loading={index === 0 ? undefined : "lazy"}
          />
          {/* Enhanced gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/30 to-black/60" />
          
          {/* Content */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white px-4 md:px-8 max-w-4xl">
              {index === currentSlide && (
                <>
                  <h1 key={key} className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black mb-6 md:mb-8 drop-shadow-lg leading-tight">
                    <TypedText 
                      text={slide.title} 
                      speed={30}
                    />
                    <span className="inline-block w-1 h-1 md:w-2 md:h-2 ml-2 mb-3 bg-gradient-to-r from-[#ffba5a] to-[#ff9800] rounded-full animate-pulse"></span>
                  </h1>
                  {slide.subtitle && (
                    <p className="text-lg md:text-2xl lg:text-3xl font-light mb-8 md:mb-12 drop-shadow-md animate-fade-in opacity-90 tracking-wide">
                      {slide.subtitle}
                    </p>
                  )}
                  <div className="flex justify-center gap-4 md:gap-6 flex-wrap">
                    <button className="bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black px-6 md:px-8 py-2 md:py-3 rounded-full font-bold transition-all duration-300 hover:shadow-xl transform hover:-translate-y-0.5 text-sm md:text-base">
                      Explore Now
                    </button>
                    <button className="bg-white/20 backdrop-blur-md border border-white/30 hover:bg-white/30 text-white px-6 md:px-8 py-2 md:py-3 rounded-full font-bold transition-all duration-300 hover:shadow-xl transform hover:-translate-y-0.5 text-sm md:text-base">
                      Learn More
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      ))}


      {/* Navigation Arrows */}
      <button
        onClick={prevSlide}
        className="absolute left-4 md:left-8 top-1/2 -translate-y-1/2 bg-gradient-to-r from-white/20 to-white/10 hover:from-white/30 hover:to-white/20 backdrop-blur-md border border-white/20 text-white p-3 md:p-4 rounded-full transition-all duration-300 z-10 hover:shadow-xl transform hover:-translate-y-0.5 group-hover:opacity-100 opacity-0 md:opacity-70"
        aria-label="Previous slide"
      >
        <svg className="w-6 h-6 md:w-8 md:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <button
        onClick={nextSlide}
        className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 bg-gradient-to-r from-white/20 to-white/10 hover:from-white/30 hover:to-white/20 backdrop-blur-md border border-white/20 text-white p-3 md:p-4 rounded-full transition-all duration-300 z-10 hover:shadow-xl transform hover:-translate-y-0.5 group-hover:opacity-100 opacity-0 md:opacity-70"
        aria-label="Next slide"
      >
        <svg className="w-6 h-6 md:w-8 md:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

      {/* Dots Indicator */}
      <div className="absolute bottom-6 md:bottom-8 left-1/2 -translate-x-1/2 flex gap-2 z-10">
        {slides.map((_, index) => (
          <button
            key={index}
            onClick={() => goToSlide(index)}
            className={`transition-all duration-300 rounded-full backdrop-blur-md ${
              index === currentSlide 
                ? "bg-gradient-to-r from-[#ffba5a] to-[#ff9800] w-8 h-3 md:w-10 md:h-3" 
                : "bg-white/40 hover:bg-white/60 w-3 h-3 md:w-3 md:h-3"
            }`}
            aria-label={`Go to slide ${index + 1}`}
          />
        ))}
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-2 md:bottom-4 left-1/2 -translate-x-1/2 animate-bounce">
        <svg className="w-6 h-6 md:w-8 md:h-8 text-white drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
}
