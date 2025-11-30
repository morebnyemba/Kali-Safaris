import { FaFacebook, FaInstagram, FaTwitter } from "react-icons/fa";

export default function FooterSection() {
  return (
    <footer className="w-full py-8 bg-green-900 dark:bg-yellow-900 text-white dark:text-yellow-100 flex flex-col items-center mt-16">
      <div className="flex gap-6 mb-4">
        <a href="#" aria-label="Facebook" className="hover:text-yellow-300"><FaFacebook size={28} /></a>
        <a href="#" aria-label="Instagram" className="hover:text-yellow-300"><FaInstagram size={28} /></a>
        <a href="#" aria-label="Twitter" className="hover:text-yellow-300"><FaTwitter size={28} /></a>
      </div>
      <div className="text-sm">&copy; {new Date().getFullYear()} Kalai Safaris. All rights reserved.</div>
    </footer>
  );
}
