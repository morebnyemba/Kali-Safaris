import FooterSection from "@/components/FooterSection";

export default function BookingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <section className="py-16">
        <div className="container mx-auto px-6">
          <div className="max-w-2xl mx-auto">
            <h1 className="text-4xl md:text-5xl font-bold text-center mb-8 text-gray-800">
              Book Your Safari Cruise
            </h1>
            
            <div className="bg-white rounded-lg shadow-lg p-8">
              <p className="text-lg text-gray-700 mb-6 text-center">
                To make a reservation, please contact us directly:
              </p>
              
              <div className="space-y-4 text-center">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Phone</h3>
                  <a href="tel:+263712629336" className="text-blue-600 hover:text-blue-800 text-lg">
                    +263712629336
                  </a>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-800 mb-2">Email</h3>
                  <a href="mailto:reservation@kalaisafaris.com" className="text-blue-600 hover:text-blue-800 text-lg">
                    reservation@kalaisafaris.com
                  </a>
                </div>
                
                <div className="pt-6">
                  <a 
                    href="https://wa.me/+263712629336?text=I'm%20interested%20in%20booking%20a%20cruise.%20Please%20tell%20me%20more!"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block bg-[#25D366] hover:bg-[#128C7E] text-white font-bold py-3 px-8 rounded-lg transition"
                  >
                    Chat on WhatsApp
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
      
      <FooterSection />
    </div>
  );
}
