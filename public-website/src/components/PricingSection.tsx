const pricingOptions = [
  {
    price: "$15.00",
    description: "Per person",
    subtitle: "School Children/Learners Special Cruise package",
  },
  {
    price: "$20.00",
    description: "Per person with cash bar",
    subtitle: "",
  },
  {
    price: "$50.00",
    description: "Per person including beverages and food depending on Breakfast, lunch or sunset",
    subtitle: "",
  },
  {
    price: "$70.00",
    description: "Per person for dinner cruise",
    subtitle: "",
  },
];

export default function PricingSection() {
  return (
    <section className="py-16 bg-gray-50" id="services">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 text-gray-800">Affordable Cruises</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {pricingOptions.map((option, index) => (
            <div 
              key={index}
              className="bg-white p-6 rounded-lg shadow-lg text-center hover:shadow-xl transition"
            >
              <h3 className="text-3xl font-bold text-[#ffba5a] mb-3">
                {option.price}
              </h3>
              <p className="text-gray-700 mb-2">{option.description}</p>
              {option.subtitle && (
                <p className="text-sm font-semibold text-gray-600">{option.subtitle}</p>
              )}
            </div>
          ))}
        </div>
        
        <div className="text-center mt-8">
          <p className="text-lg italic font-semibold text-gray-700">
            <strong>(Excludes applicable Parks river usage fee)</strong>
          </p>
        </div>
      </div>
    </section>
  );
}
