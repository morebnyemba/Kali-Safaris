import Link from "next/link";

export default function BookingCTA() {
  return (
    <section className="py-12 bg-[#003]">
      <div className="container mx-auto px-6">
        <div className="max-w-4xl mx-auto">
          <Link 
            href="/booking" 
            className="block w-full bg-blue-600 hover:bg-blue-700 text-white text-center font-bold py-4 px-8 rounded-lg text-xl transition shadow-lg"
          >
            Book Now!
          </Link>
        </div>
      </div>
    </section>
  );
}
