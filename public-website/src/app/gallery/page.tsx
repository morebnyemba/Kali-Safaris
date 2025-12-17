import Image from "next/image";
import FooterSection from "@/components/FooterSection";

const galleryImages = [
  { src: "/images/kalai_intro.jpeg", alt: "Kalai Safari Boat" },
  { src: "/images/sunrise.jpeg", alt: "Sunrise Cruise" },
  { src: "/images/sunset.jpeg", alt: "Sunset Cruise" },
  { src: "/images/Kalai Sunset background shot.jpeg", alt: "Sunset Background" },
  { src: "/images/work_no_play.jpeg", alt: "Lunch Time Cruise" },
  { src: "/images/jetty_venue.jpg", alt: "Jetty Venue" },
  { src: "/images/Kalai Safaris interior chairs.jpeg", alt: "Interior Chairs" },
  { src: "/images/Kalai Safaris jetty site.jpeg", alt: "Jetty Site" },
  { src: "/images/cruise boat.jpg", alt: "Cruise Boat" },
  { src: "/images/Boats .jpg", alt: "Boats" },
  { src: "/images/jetty site 2.jpg", alt: "Jetty Site 2" },
  { src: "/images/jetty 3.jpg", alt: "Jetty 3" },
];

export default function GalleryPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <section className="py-16">
        <div className="container mx-auto px-6">
          <h1 className="text-4xl md:text-5xl font-bold text-center mb-12 text-gray-800">
            Gallery
          </h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {galleryImages.map((image, index) => (
              <div 
                key={index}
                className="relative aspect-square overflow-hidden rounded-lg shadow-lg hover:shadow-xl transition group"
              >
                <Image
                  src={image.src}
                  alt={image.alt}
                  fill
                  className="object-cover group-hover:scale-110 transition duration-500"
                />
              </div>
            ))}
          </div>
        </div>
      </section>
      
      <FooterSection />
    </div>
  );
}
