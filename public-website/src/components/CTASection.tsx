import Link from "next/link";

export default function CTASection() {
  return (
    <section className="w-full py-16 bg-gradient-to-r from-green-700 to-yellow-500 dark:from-yellow-900 dark:to-green-900 flex flex-col items-center">
      <h2 className="text-3xl font-bold mb-4 text-white">Ready for Your Adventure?</h2>
      <p className="text-lg text-white mb-6 max-w-xl text-center">
        Book your safari with Kalai Safaris today and experience the wild like never before. Our team is ready to help you plan the journey of a lifetime.
      </p>
      <Link href="/about" className="inline-block px-8 py-4 bg-white text-green-900 font-semibold rounded-full shadow-lg hover:bg-yellow-200 transition text-lg">
        Learn More
      </Link>
      <a href="mailto:bookings@kalaisafaris.com" className="mt-4 inline-block px-8 py-4 bg-green-900 text-white font-semibold rounded-full shadow-lg hover:bg-green-700 transition text-lg">
        Book Now
      </a>
    </section>
  );
}
