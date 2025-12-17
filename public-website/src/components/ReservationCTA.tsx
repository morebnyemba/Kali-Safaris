import Link from "next/link";

export default function ReservationCTA() {
  return (
    <section 
      className="py-20 bg-cover bg-center relative" 
      style={{ backgroundImage: "url('/images/counter-bg2.jpg')" }}
      id="reserve"
    >
      <div className="absolute inset-0 bg-black/50" />
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
          <div className="text-center md:text-left">
            <h2 className="text-3xl md:text-4xl font-bold text-white">
              For A Best Holiday Experience.
            </h2>
          </div>
          <div className="text-center md:text-right">
            <Link 
              href="/booking" 
              className="inline-block border-2 border-white text-white hover:bg-white hover:text-gray-900 font-bold py-3 px-8 rounded-lg transition"
            >
              Make Reservation Now
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
