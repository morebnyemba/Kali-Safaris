import { Card } from "@/components/ui/card";
import { FaSafari } from "react-icons/fa";

export default function HeroSection() {
  return (
    <section className="w-full py-16 flex flex-col items-center bg-gradient-to-br from-yellow-100 to-green-100 dark:from-yellow-900 dark:to-green-900">
      <Card className="p-8 max-w-2xl text-center shadow-xl bg-white/80 dark:bg-black/60">
        <div className="flex justify-center mb-4">
          <FaSafari className="text-6xl text-green-700 dark:text-yellow-300" />
        </div>
        <h1 className="text-4xl font-bold mb-4 text-green-900 dark:text-yellow-200">Welcome to Kalai Safaris</h1>
        <p className="text-lg text-gray-700 dark:text-gray-200 mb-6">
          Experience the adventure of a lifetime with Kalai Safaris. Explore Africas wild beauty, guided by experts, in comfort and safety.
        </p>
        <span className="inline-block rounded-full bg-green-200 dark:bg-yellow-700 px-4 py-2 text-green-900 dark:text-yellow-100 font-semibold">
          Unforgettable Journeys Await
        </span>
      </Card>
    </section>
  );
}
