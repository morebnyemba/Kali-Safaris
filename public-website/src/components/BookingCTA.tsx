import Link from "next/link";

export default function BookingCTA() {
  return (
    <section className="py-12 bg-gradient-to-r from-[#001a33] via-[#002b4d] to-[#001a33]">
      <div className="container mx-auto px-6">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-white/80 text-sm uppercase tracking-[0.3em] mb-3">
            Ready for an adventure?
          </p>
          <Link 
            href="/booking" 
            className="block w-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] hover:from-[#ff9800] hover:to-[#ff7700] text-black text-center font-bold py-4 px-8 rounded-full text-xl transition-all duration-300 shadow-lg hover:shadow-2xl hover:-translate-y-0.5"
          >
            Book Your Cruise Now!
          </Link>
        </div>
      </div>
    </section>
  );
}
