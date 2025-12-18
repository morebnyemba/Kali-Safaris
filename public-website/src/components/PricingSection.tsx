const pricingOptions = [
  {
    price: "$15.00",
    description: "Per person",
    subtitle: "School Children/Learners Special Cruise package",
    tag: "Best for Learners",
  },
  {
    price: "$20.00",
    description: "Per person with cash bar",
    subtitle: "",
    tag: "Value",
  },
  {
    price: "$50.00",
    description:
      "Per person including beverages and food depending on Breakfast, lunch or sunset",
    subtitle: "",
    tag: "Popular",
  },
  {
    price: "$70.00",
    description: "Per person for dinner cruise",
    subtitle: "",
    tag: "Evening Luxury",
  },
];

export default function PricingSection() {
  return (
    <section
      className="relative py-20 bg-gradient-to-b from-white via-[#fff7ec] to-white overflow-hidden"
      id="services"
    >
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-10 left-10 w-48 h-48 bg-[#ffba5a]/20 blur-3xl rounded-full" />
        <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#ff9800]/20 blur-3xl rounded-full" />
      </div>

      <div className="container mx-auto px-6 relative">
        <div className="text-center mb-14">
          <p className="text-sm uppercase tracking-[0.3em] text-[#ff9800] font-semibold mb-3">
            Pricing
          </p>
          <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900 drop-shadow-sm">
            Affordable Cruises
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Transparent packages with everything you need for a memorable Zambezi cruise.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {pricingOptions.map((option, index) => (
            <div
              key={index}
              className="group relative bg-white/80 backdrop-blur-lg border border-white/60 shadow-lg rounded-2xl p-6 flex flex-col gap-4 text-center transition-all duration-300 hover:-translate-y-2 hover:shadow-2xl"
            >
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/60 to-[#ffba5a]/10 opacity-0 group-hover:opacity-100 transition duration-300" />

              <div className="relative flex justify-center">
                <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-[#ffba5a] to-[#ff9800] text-black shadow-sm">
                  {option.tag}
                  <span className="w-2 h-2 rounded-full bg-black/60" />
                </span>
              </div>

              <h3 className="relative text-4xl font-extrabold text-gray-900 drop-shadow-sm">
                {option.price}
              </h3>

              <p className="relative text-gray-700 leading-relaxed min-h-[48px]">
                {option.description}
              </p>

              {option.subtitle && (
                <p className="relative text-sm font-semibold text-gray-600 bg-white/70 px-3 py-2 rounded-lg border border-white/50">
                  {option.subtitle}
                </p>
              )}

              <div className="relative flex justify-center mt-auto">
                <button className="w-full rounded-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] text-black font-bold py-2.5 transition-all duration-300 shadow-md hover:shadow-xl hover:-translate-y-0.5">
                  Book this cruise
                </button>
              </div>
            </div>
          ))}
        </div>
        
        <div className="text-center mt-10">
          <p className="inline-flex items-center gap-2 text-base md:text-lg italic font-semibold text-gray-700 bg-white/80 backdrop-blur-md px-4 py-2 rounded-full shadow-sm border border-white/70">
            <span className="w-2 h-2 rounded-full bg-[#ff9800] animate-pulse" />
            <strong>(Excludes applicable Parks river usage fee)</strong>
          </p>
        </div>
      </div>
    </section>
  );
}
