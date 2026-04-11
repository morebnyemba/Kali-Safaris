import { FaBinoculars, FaTree, FaUserShield, FaSmileBeam } from "react-icons/fa";

const advantages = [
  {
    icon: <FaBinoculars className="text-3xl text-[#ff9800]" />,
    title: "Expert Guides",
    desc: "Our team consists of experienced guides who know the Zambezi and its wildlife intimately.",
  },
  {
    icon: <FaTree className="text-3xl text-[#ff9800]" />,
    title: "Immersive Nature",
    desc: "Get close to nature in a responsible, eco-friendly way, supporting conservation.",
  },
  {
    icon: <FaUserShield className="text-3xl text-[#ff9800]" />,
    title: "Safety First",
    desc: "Your safety is our top priority, with well-maintained vessels and strict protocols.",
  },
  {
    icon: <FaSmileBeam className="text-3xl text-[#ff9800]" />,
    title: "Memorable Experiences",
    desc: "We create moments you'll cherish forever, from sunrise to sunset.",
  },
];

export default function AdvantagesSection() {
  return (
    <section className="py-20 bg-gradient-to-b from-[#001a33] via-[#002b4d] to-[#001a33] relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute inset-0 pointer-events-none opacity-20">
        <div className="absolute top-10 left-10 w-48 h-48 bg-[#ffba5a] blur-3xl rounded-full" />
        <div className="absolute bottom-10 right-10 w-56 h-56 bg-[#ff9800] blur-3xl rounded-full" />
      </div>

      <div className="container mx-auto px-6 relative">
        <div className="text-center mb-14">
          <p className="text-sm uppercase tracking-[0.3em] text-[#ffba5a] font-semibold mb-3">
            Why Choose Us
          </p>
          <h2 className="text-4xl md:text-5xl font-black mb-4 text-white drop-shadow-sm">
            The Kalai Difference
          </h2>
          <p className="text-white/70 max-w-2xl mx-auto">
            What makes a Kalai Safaris cruise an experience unlike any other on the Zambezi.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {advantages.map((adv, idx) => (
            <div
              key={idx}
              className="group bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 text-center transition-all duration-300 hover:-translate-y-2 hover:bg-white/10 hover:shadow-xl"
            >
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#ffba5a]/15 mb-4 group-hover:bg-[#ffba5a]/25 transition-colors">
                {adv.icon}
              </div>
              <h3 className="text-xl font-bold text-white mb-2">{adv.title}</h3>
              <p className="text-white/70 text-sm leading-relaxed">{adv.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
