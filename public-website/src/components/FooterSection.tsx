import { FaMapMarkerAlt, FaPhone, FaEnvelope, FaWhatsapp } from "react-icons/fa";

export default function FooterSection() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="w-full bg-[#003] text-white py-12" id="contact">
      <div className="container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* Location Map */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-[#ffba5a]">Our Location</h2>
            <iframe 
              src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d15186.660309634595!2d25.827891!3d-17.9011077!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x194ffbfa993efc89%3A0x4ccf5857807bae76!2sKalai%20Safari!5e0!3m2!1sen!2szw!4v1695656987970!5m2!1sen!2szw" 
              width="100%" 
              height="250" 
              style={{ border: 0 }} 
              allowFullScreen 
              loading="lazy" 
              referrerPolicy="no-referrer-when-downgrade"
              className="rounded-lg"
              title="Kalai Safari Location Map"
            />
          </div>

          {/* Contact Information */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-[#ffba5a]">Contact Us</h2>
            <div className="space-y-3">
              <p className="flex items-start gap-3">
                <FaMapMarkerAlt className="text-[#ffba5a] mt-1 flex-shrink-0" />
                <span>Kalai Safaris, riverside jetty next to Palm Lodge, Victoria Falls Zimbabwe</span>
              </p>
              <p className="flex items-center gap-3">
                <FaPhone className="text-[#ffba5a] flex-shrink-0" />
                <a href="tel:+263712629336" className="hover:text-[#ffba5a] transition">+263712629336</a>
              </p>
              <p className="flex items-center gap-3">
                <FaEnvelope className="text-[#ffba5a] flex-shrink-0" />
                <a href="mailto:reservation@kalaisafaris.com" className="hover:text-[#ffba5a] transition">reservation@kalaisafaris.com</a>
              </p>
            </div>
          </div>

          {/* Facebook Page */}
          <div>
            <h2 className="text-xl font-semibold mb-4 text-[#ffba5a]">Follow Us</h2>
            <iframe 
              src="https://www.facebook.com/plugins/page.php?href=https%3A%2F%2Fwww.facebook.com%2FKalaiSafari&tabs=timeline&width=340&height=250&small_header=false&adapt_container_width=true&hide_cover=false&show_facepile=true&appId" 
              width="100%" 
              height="250" 
              style={{ border: 'none', overflow: 'hidden' }} 
              scrolling="no" 
              frameBorder="0" 
              allowFullScreen 
              allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
              className="rounded-lg"
              title="Kalai Safari Facebook Page"
            />
          </div>
        </div>

        {/* Copyright and Attribution */}
        <div className="border-t border-gray-600 pt-6 mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-center md:text-left">
            <div className="text-sm">
              &copy; 2019 - {currentYear} Kalai Safaris. All rights reserved.
            </div>
            <div className="text-sm text-center md:text-right">
              Powered by <a href="https://slykertech.com" target="_blank" rel="noopener noreferrer" className="text-[#ffba5a] hover:underline font-semibold">Slyker Tech Web Services</a>
            </div>
          </div>
        </div>
      </div>

      {/* WhatsApp Floating Button */}
      <a
        href="https://wa.me/+263712629336?text=I'm%20interested%20in%20your%20services%20as%20advertised%20on%20your%20website.%20Please%20tell%20me%20more!"
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-4 left-4 z-50 bg-[#25D366] hover:bg-[#128C7E] text-white rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-110"
        aria-label="Chat on WhatsApp"
      >
        <FaWhatsapp size={32} />
      </a>
    </footer>
  );
}
