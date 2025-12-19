import { FaMapMarkerAlt, FaPhone, FaEnvelope, FaWhatsapp, FaFacebook, FaInstagram, FaTwitter } from "react-icons/fa";

export default function FooterSection() {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="relative w-full bg-gradient-to-b from-[#001a33] via-[#003] to-[#000d1a] text-white overflow-hidden" id="contact">
      {/* Decorative background elements */}
      <div className="absolute inset-0 pointer-events-none opacity-10">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#ffba5a] rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-[#ff9800] rounded-full blur-3xl" />
      </div>

      <div className="container mx-auto px-6 py-12 relative">
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {/* Location Map */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-[#ffba5a] to-[#ff9800]">Our Location</h2>
            <div className="rounded-2xl overflow-hidden shadow-2xl border border-white/10">
              <iframe 
                src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d15186.660309634595!2d25.827891!3d-17.9011077!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x194ffbfa993efc89%3A0x4ccf5857807bae76!2sKalai%20Safari!5e0!3m2!1sen!2szw!4v1695656987970!5m2!1sen!2szw" 
                width="100%" 
                height="250" 
                style={{ border: 0 }} 
                allowFullScreen 
                loading="lazy" 
                referrerPolicy="no-referrer-when-downgrade"
                title="Kalai Safari Location Map"
              />
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-[#ffba5a] to-[#ff9800]">Contact Us</h2>
            <div className="space-y-4">
              <a 
                href="https://maps.google.com/?q=Kalai+Safaris+Victoria+Falls" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-start gap-3 group hover:translate-x-1 transition-transform"
              >
                <FaMapMarkerAlt className="text-[#ffba5a] mt-1 flex-shrink-0 group-hover:scale-110 transition-transform" />
                <span className="group-hover:text-[#ffba5a] transition">Kalai Safaris, riverside jetty next to Palm Lodge, Victoria Falls Zimbabwe</span>
              </a>
              <a 
                href="tel:+263712629336" 
                className="flex items-center gap-3 group hover:translate-x-1 transition-transform"
              >
                <FaPhone className="text-[#ffba5a] flex-shrink-0 group-hover:scale-110 transition-transform" />
                <span className="group-hover:text-[#ffba5a] transition">+263 712 629 336</span>
              </a>
              <a 
                href="mailto:reservation@kalaisafaris.com" 
                className="flex items-center gap-3 group hover:translate-x-1 transition-transform"
              >
                <FaEnvelope className="text-[#ffba5a] flex-shrink-0 group-hover:scale-110 transition-transform" />
                <span className="group-hover:text-[#ffba5a] transition break-all">reservation@kalaisafaris.com</span>
              </a>
            </div>

            {/* Social Media Links */}
            <div className="pt-4">
              <h3 className="text-lg font-semibold mb-3 text-white/90">Follow Us</h3>
              <div className="flex gap-3">
                <a 
                  href="https://www.facebook.com/KalaiSafari" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center hover:bg-[#ffba5a] hover:scale-110 transition-all duration-300"
                  aria-label="Facebook"
                >
                  <FaFacebook size={20} />
                </a>
                <a 
                  href="https://wa.me/263712629336" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center hover:bg-[#25D366] hover:scale-110 transition-all duration-300"
                  aria-label="WhatsApp"
                >
                  <FaWhatsapp size={20} />
                </a>
              </div>
            </div>
          </div>

          {/* Facebook Page Preview */}
          <div className="space-y-4">
            <h2 className="text-2xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-[#ffba5a] to-[#ff9800]">Stay Connected</h2>
            <div className="rounded-2xl overflow-hidden shadow-2xl border border-white/10">
              <iframe 
                src="https://www.facebook.com/plugins/page.php?href=https%3A%2F%2Fwww.facebook.com%2FKalaiSafari&tabs=timeline&width=340&height=250&small_header=false&adapt_container_width=true&hide_cover=false&show_facepile=true&appId" 
                width="100%" 
                height="250" 
                style={{ border: 'none', overflow: 'hidden' }} 
                scrolling="no" 
                frameBorder="0" 
                allowFullScreen 
                allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
                title="Kalai Safari Facebook Page"
              />
            </div>
          </div>
        </div>

        {/* Copyright and Attribution */}
        <div className="border-t border-white/10 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-white/70">
              &copy; 2019 - {currentYear} <span className="font-semibold text-white">Kalai Safaris</span>. All rights reserved.
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-white/70">Powered by</span>
              <a 
                href="https://slykertech.co.zw" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-[#ffba5a] to-[#ff9800] text-black font-bold text-sm hover:shadow-xl hover:-translate-y-0.5 transition-all duration-300"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
                </svg>
                Slyker Tech Web Services
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* WhatsApp Floating Button */}
      <a
        href="https://wa.me/263712629336?text=*[Message from Kalai Safaris Website]*%0A%0AI'm%20interested%20in%20your%20services%20as%20advertised%20on%20your%20website.%20Please%20tell%20me%20more!"
        target="_blank"
        rel="noopener noreferrer"
        className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-[#25D366] to-[#128C7E] hover:from-[#128C7E] hover:to-[#075E54] text-white rounded-full p-4 shadow-2xl transition-all duration-300 hover:scale-110 animate-pulse hover:animate-none"
        aria-label="Chat on WhatsApp"
      >
        <FaWhatsapp size={32} />
      </a>
    </footer>
  );
}
