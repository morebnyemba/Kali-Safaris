import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FaBinoculars, FaTree, FaUserShield, FaSmileBeam } from "react-icons/fa";

const advantages = [
  {
    icon: <FaBinoculars className="text-3xl text-green-700 dark:text-yellow-300" />,
    title: "Expert Guides",
    desc: "Our team consists of experienced guides who know the land and wildlife intimately."
  },
  {
    icon: <FaTree className="text-3xl text-green-700 dark:text-yellow-300" />,
    title: "Immersive Nature",
    desc: "Get close to nature in a responsible, eco-friendly way, supporting conservation."
  },
  {
    icon: <FaUserShield className="text-3xl text-green-700 dark:text-yellow-300" />,
    title: "Safety First",
    desc: "Your safety is our top priority, with well-maintained vehicles and protocols."
  },
  {
    icon: <FaSmileBeam className="text-3xl text-green-700 dark:text-yellow-300" />,
    title: "Memorable Experiences",
    desc: "We create moments youll cherish forever, from sunrise to sunset."
  }
];

export default function AdvantagesSection() {
  return (
    <section className="w-full py-16 bg-white dark:bg-black flex flex-col items-center">
      <h2 className="text-3xl font-bold mb-8 text-green-900 dark:text-yellow-200">Why Choose Kalai Safaris?</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl w-full">
        {advantages.map((adv, idx) => (
          <Card key={idx} className="p-6 flex flex-col items-center shadow-md bg-green-50 dark:bg-yellow-900/30">
            <CardHeader className="flex flex-col items-center">
              {adv.icon}
              <CardTitle className="mt-2 text-xl text-green-900 dark:text-yellow-200">{adv.title}</CardTitle>
            </CardHeader>
            <CardContent className="text-gray-700 dark:text-gray-200 text-center">
              {adv.desc}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
