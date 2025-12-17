import Image from "next/image";
import Link from "next/link";

export default function IntroSection() {
  return (
    <section className="py-16 bg-gray-50">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          <div className="order-2 lg:order-1 text-center lg:text-center">
            <h2 className="text-2xl md:text-3xl font-semibold mb-6 text-gray-800">
              Kalai &quot;the cry of the fish eagle&quot;, is a boating safari company on the mighty Zambezi above the Victoria Falls. We have a 40 seater and a 10 seater cruise vessel. We tailor-make your safari cruises to meet your expectations and needs
            </h2>
            <Link 
              href="#sunrise" 
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition"
            >
              Discover More
            </Link>
          </div>
          <div className="order-1 lg:order-2">
            <Image
              src="/images/kalai_intro.jpeg"
              alt="Kalai Safari Boat"
              width={800}
              height={600}
              className="rounded-lg shadow-lg"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
