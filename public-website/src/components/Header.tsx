import Link from "next/link";

export default function Header() {
  return (
    <header className="w-full bg-green-900 dark:bg-yellow-900 text-white dark:text-yellow-100 shadow-md sticky top-0 z-50">
      <nav className="container mx-auto flex items-center justify-between py-4 px-6">
        <Link href="/">
          <span className="text-2xl font-bold tracking-tight">Kalai Safaris</span>
        </Link>
        <ul className="flex gap-8 text-lg font-medium">
          <li><Link href="/" className="hover:text-yellow-300 transition">Home</Link></li>
          <li><Link href="/about" className="hover:text-yellow-300 transition">About</Link></li>
        </ul>
      </nav>
    </header>
  );
}
