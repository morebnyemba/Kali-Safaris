import Link from "next/link";

export default function ReservationCTA() {
  return (
    <section
      className="py-20 bg-cover bg-center relative"
      style={{ backgroundImage: "url('/images/counter-bg2.jpg')" }}
      id="reserve"
    >
      <div className="absolute inset-0 bg-black/60" />
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div className="text-center md:text-left">
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              For a Best Holiday Experience.
            </h2>
          </div>
          <div className="text-center md:text-right">
            <Link
              href="/booking"
              className="inline-block bg-[#C8102E] hover:bg-[#E8173A] text-white font-bold py-3 px-8 rounded-full transition-all duration-300 shadow-lg hover:shadow-2xl hover:shadow-red-600/30 hover:-translate-y-0.5"
            >
              Make Reservation Now
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
