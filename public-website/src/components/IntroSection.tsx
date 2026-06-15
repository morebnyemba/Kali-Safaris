import Image from "next/image";
import Link from "next/link";

export default function IntroSection() {
  return (
    <section className="py-20 bg-gradient-to-b from-white via-[#FFF9F5] to-white relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#E09A18]/15 blur-3xl rounded-full" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-[#E8600A]/10 blur-3xl rounded-full" />
      </div>

      <div className="container mx-auto px-6 relative">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
          <div className="order-2 lg:order-1">
            <div className="bg-white/75 backdrop-blur-lg border border-white/60 shadow-xl rounded-2xl p-8 md:p-10 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-white/60 via-transparent to-white/30" />
              <p className="relative text-sm uppercase tracking-[0.3em] text-[#E8600A] font-semibold mb-4">
                About Kalai Safaris
              </p>
              <h2 className="relative text-2xl md:text-3xl font-bold mb-6 text-gray-900 leading-relaxed">
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#C8102E] to-[#E8600A]">Kalai</span> &quot;the cry of the fish eagle&quot;, is a boating safari company on the mighty Zambezi above the Victoria Falls.
              </h2>
              <p className="relative text-lg text-gray-600 mb-6 leading-relaxed">
                We have a 40 seater and a 10 seater cruise vessel. We tailor-make your safari cruises to meet your expectations and needs.
              </p>
              <Link
                href="#sunrise"
                className="relative inline-block bg-[#C8102E] hover:bg-[#E8173A] text-white font-bold py-3 px-8 rounded-full transition-all duration-300 hover:shadow-xl hover:shadow-red-600/25 hover:-translate-y-0.5"
              >
                Discover Our Cruises
              </Link>
            </div>
          </div>
          <div className="order-1 lg:order-2">
            <div className="rounded-3xl overflow-hidden shadow-2xl border border-white/50">
              <Image
                src="/images/kalai_intro.jpeg"
                alt="Kalai Safari Boat on the Zambezi River"
                width={800}
                height={600}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
