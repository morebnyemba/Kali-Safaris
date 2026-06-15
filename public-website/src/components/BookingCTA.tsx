import Link from "next/link";

export default function BookingCTA() {
  return (
    <section className="py-12 bg-[#0A0A0A]">
      <div className="container mx-auto px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-white/70 text-sm uppercase tracking-[0.3em] mb-3">
            Ready for an adventure?
          </p>
          <Link
            href="/booking"
            className="block w-full bg-[#C8102E] hover:bg-[#E8173A] text-white text-center font-bold py-4 px-8 rounded-full text-xl transition-all duration-300 shadow-lg hover:shadow-2xl hover:shadow-red-600/30 hover:-translate-y-0.5"
          >
            Book Your Cruise Now!
          </Link>
        </div>
      </div>
    </section>
  );
}
