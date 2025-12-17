import Image from "next/image";

const cruises = [
  {
    id: "sunrise",
    title: "Sunrise Cruise",
    description: "Get to experience the early blessings of what the mighty Zambezi river can offer while you take a relaxing and most comforting safari cruise. Experience how nature and wild animals starts their beautiful day.",
    time: "Our cruise is a 2 hour early morning cruise starting at 06:00 am to 08:00 am",
    image: "/images/sunrise.jpeg",
    bgColor: "bg-[#ffa500]",
    textColor: "text-black",
  },
  {
    id: "lunch",
    title: "Lunch Cruise",
    description: "Have a relaxing and most comforting experience on mighty zambezi river lunch time safari cruise.",
    time: "A 2 hour cruise starting at 12:00pm to 02:00pm",
    image: "/images/work_no_play.jpeg",
    bgColor: "bg-[#003]",
    textColor: "text-white",
    imageFirst: true,
  },
  {
    id: "sunset",
    title: "Sunset Cruise",
    description: "Kalai Safaris will give you an unforgettable experience along the Zambezi, as you may have an opportunity to spot a wide range of wild animals and birds interacting. Our cruise is a 2 hour late afternoon cruise starting at 16:00hrs and it ends soon after sunset",
    image: "/images/sunset.jpeg",
    image2: "/images/Kalai Sunset background shot.jpeg",
    bgColor: "bg-[#ffa500]",
    textColor: "text-black",
  },
  {
    id: "jetty",
    title: "Jetty Venue",
    description: "We can offer events hosting on our riverside jetty, conference, weddings, cocktails or any outdoor function which needs a beautiful backdrop of the mighty Zambezi River",
    image: "/images/jetty_venue.jpg",
    bgColor: "bg-[#003]",
    textColor: "text-white",
    imageFirst: true,
  },
];

export default function CruiseTypesSection() {
  return (
    <>
      {cruises.map((cruise) => (
        <section 
          key={cruise.id} 
          id={cruise.id} 
          className={`py-16 ${cruise.bgColor}`}
        >
          <div className="container mx-auto px-6">
            <div className={`grid grid-cols-1 md:grid-cols-2 gap-8 items-center ${cruise.imageFirst ? 'md:grid-flow-dense' : ''}`}>
              {/* Text Content */}
              <div className={`${cruise.imageFirst ? 'md:col-start-2' : ''}`}>
                <div className="text-center mb-8">
                  <h2 className={`text-3xl md:text-4xl font-bold ${cruise.textColor}`}>
                    {cruise.title}
                  </h2>
                </div>
                <div className="space-y-4">
                  <p className={`text-lg ${cruise.textColor}`}>
                    {cruise.description}
                  </p>
                  {cruise.time && (
                    <p className={`text-lg ${cruise.textColor}`}>
                      {cruise.time}
                    </p>
                  )}
                </div>
              </div>

              {/* Image */}
              <div className={`${cruise.imageFirst ? 'md:col-start-1' : ''}`}>
                <Image
                  src={cruise.image}
                  alt={cruise.title}
                  width={800}
                  height={600}
                  className="rounded-lg shadow-lg w-full"
                />
                {cruise.image2 && (
                  <Image
                    src={cruise.image2}
                    alt={`${cruise.title} view 2`}
                    width={800}
                    height={600}
                    className="rounded-lg shadow-lg w-full mt-4"
                  />
                )}
              </div>
            </div>
          </div>
        </section>
      ))}
    </>
  );
}
