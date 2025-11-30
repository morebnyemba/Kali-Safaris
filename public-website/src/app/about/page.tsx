import Image from "next/image";

export default function AboutPage() {
  return (
    <main className="flex flex-col items-center min-h-screen bg-zinc-50 dark:bg-black py-16 px-4">
      <div className="max-w-3xl w-full bg-white dark:bg-zinc-900 rounded-xl shadow-lg p-8 flex flex-col items-center">
        <Image src="/img/safari-group.jpg" alt="Safari Group" width={600} height={300} className="rounded-lg mb-6 object-cover" />
        <h1 className="text-4xl font-bold mb-4 text-green-900 dark:text-yellow-200">About Kalai Safaris</h1>
        <p className="text-lg text-gray-700 dark:text-gray-200 mb-4 text-center">
          Kalai Safaris is dedicated to providing unforgettable safari experiences across Africa. Our expert guides, eco-friendly practices, and passion for wildlife ensure every journey is safe, educational, and inspiring.
        </p>
        <p className="text-lg text-gray-700 dark:text-gray-200 mb-4 text-center">
          We believe in responsible tourism, supporting local communities, and protecting the natural beauty of our destinations. Join us for an adventure that will leave you with memories to last a lifetime.
        </p>
        <Image src="/img/jeep-safari.jpg" alt="Jeep Safari" width={600} height={300} className="rounded-lg mt-4 object-cover" />
      </div>
    </main>
  );
}
