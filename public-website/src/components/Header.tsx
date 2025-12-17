import Link from "next/link";
import Image from "next/image";

export default function Header() {
  return (
    <header className="w-full bg-white shadow-md sticky top-0 z-50">
      <nav className="container mx-auto flex items-center justify-between py-4 px-6">
        <Link href="/">
          <Image 
            src="/images/kalai_safari_logo.PNG" 
            alt="Kalai Safari Logo" 
            width={100} 
            height={100}
            className="rounded-2xl"
          />
        </Link>
        <ul className="hidden md:flex gap-4 text-base font-medium">
          <li>
            <Link href="/" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              About Us
            </Link>
          </li>
          <li>
            <Link href="/#sunrise" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Sunrise Cruise
            </Link>
          </li>
          <li>
            <Link href="/#lunch" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Lunch Cruise
            </Link>
          </li>
          <li>
            <Link href="/#sunset" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Sunset Cruise
            </Link>
          </li>
          <li>
            <Link href="/#contact" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Contact Us
            </Link>
          </li>
          <li>
            <Link href="/gallery" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Gallery
            </Link>
          </li>
          <li>
            <Link href="/booking" className="bg-[#ffba5a] hover:bg-[#ff9800] text-black px-4 py-2 rounded-full transition">
              Book Now!
            </Link>
          </li>
        </ul>
      </nav>
    </header>
  );
}
