import Image from "next/image";

const galleryImages = [
  { src: "/img/safari1.jpg", alt: "Elephants on Safari" },
  { src: "/img/safari2.jpg", alt: "Safari Jeep Adventure" },
  { src: "/img/safari3.jpg", alt: "Sunset in the Savannah" },
  { src: "/img/safari4.jpg", alt: "Lion in the Wild" },
  { src: "/img/safari5.jpg", alt: "Giraffes Grazing" },
  { src: "/img/safari6.jpg", alt: "Bird Watching" },
];

export default function GallerySection() {
  return (
    <section className="w-full py-16 bg-green-50 dark:bg-yellow-900/10 flex flex-col items-center">
      <h2 className="text-3xl font-bold mb-8 text-green-900 dark:text-yellow-200">Gallery</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 max-w-5xl w-full px-4">
        {galleryImages.map((img, idx) => (
          <div key={idx} className="overflow-hidden rounded-lg shadow-lg bg-white dark:bg-zinc-900">
            <Image src={img.src} alt={img.alt} width={400} height={250} className="object-cover w-full h-64 hover:scale-105 transition-transform duration-300" />
          </div>
        ))}
      </div>
    </section>
  );
}
