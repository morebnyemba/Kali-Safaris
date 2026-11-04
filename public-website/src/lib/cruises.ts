// The cruises and venue shown on the homepage cards, the header "Cruises" menu
// and the /cruises/[slug] pages. One list, so they can't drift apart.
//
// Times and prices are NOT kept here: they come live from the backend tour
// (matched by `tourName`), so what the site shows is what checkout charges.

export interface Cruise {
  slug: string;
  title: string;
  /** Backend Tour.name this page books. */
  tourName: string;
  /** Short line for menus and cards. */
  tagline: string;
  description: string;
  image: string;
  alt: string;
  /** Gallery category whose photos appear on this cruise's page. */
  galleryCategory: string;
  badge?: string;
  /** Venue hire is enquired about, not booked online. */
  isVenue?: boolean;
}

export const CRUISES: Cruise[] = [
  {
    slug: 'sunrise',
    title: 'Sunrise Cruise',
    tourName: 'Sunrise Cruise',
    tagline: 'Watch the river wake up',
    description:
      'Watch the river wake up — hippos surfacing, fish eagles calling and game coming down to drink in the cool morning light.',
    image: '/images/sunrise.jpeg',
    alt: 'Breakfast table set on the deck overlooking the Zambezi at sunrise',
    galleryCategory: 'sunrise',
  },
  {
    slug: 'lunch',
    title: 'Lunch Cruise',
    tourName: 'Lunch Cruise',
    tagline: 'A relaxed midday on the Zambezi',
    description:
      'A relaxed midday cruise with a river breeze, great views and time to unwind between Victoria Falls activities.',
    image: '/images/work_no_play.jpeg',
    alt: 'Guests enjoying a meal on the deck during a lunch cruise',
    galleryCategory: 'lunch',
  },
  {
    slug: 'sunset',
    title: 'Sunset Cruise',
    tourName: 'Sunset Cruise',
    tagline: 'Our most popular cruise',
    badge: 'Most popular',
    description:
      'Our most-loved cruise. Spot wildlife along the banks, then watch the sun go down in gold and red over the Zambezi.',
    image: '/images/Kalai Sunset background shot.jpeg',
    alt: 'Sunset over the Zambezi River seen from a Kalai Safaris cruise',
    galleryCategory: 'sunset',
  },
];

export const VENUE: Cruise = {
  slug: 'jetty',
  title: 'Jetty Venue',
  tourName: 'Jetty Venue Hire',
  tagline: 'Weddings, conferences and functions',
  description:
    'Host a wedding, conference, cocktail party or private function on our riverside jetty, with the Zambezi as your backdrop.',
  image: '/images/jetty_venue.jpg',
  alt: 'Kalai Safaris riverside jetty event venue',
  galleryCategory: 'jetty',
  isVenue: true,
};

/** The food-and-drinks upgrade offered on every cruise page, when that tour is active. */
export const PREMIUM_TOUR_NAME = 'Premium River Cruise (Breakfast, Lunch or Sunset)';

export const cruisePath = (slug: string) => `/cruises/${slug}`;

/** Straight into the booking form for a tour, optionally with a departure already chosen. */
export function bookingHref(tourName: string, departure?: string) {
  const params = new URLSearchParams({ tour_name: tourName });
  if (departure) params.set('departure', departure);
  return `/booking?${params.toString()}`;
}
