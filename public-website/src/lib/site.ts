// Single source for contact details shown in the header, footer and checkout.
export const SITE = {
  phoneDisplay: '+263 712 629 336',
  phoneHref: 'tel:+263712629336',
  email: 'reservation@kalaisafaris.com',
  whatsappNumber: '263712629336',
  address: 'Riverside jetty next to Palm Lodge, Victoria Falls, Zimbabwe',
  mapsUrl: 'https://maps.google.com/?q=Kalai+Safaris+Victoria+Falls',
  facebook: 'https://www.facebook.com/KalaiSafari',
  // Set NEXT_PUBLIC_TRIPADVISOR_URL to the listing URL to show review links; hidden when empty.
  tripadvisor: process.env.NEXT_PUBLIC_TRIPADVISOR_URL || '',
};

export function whatsappLink(message = "Hi, I'm interested in a Zambezi cruise. Please tell me more!") {
  return `https://wa.me/${SITE.whatsappNumber}?text=${encodeURIComponent(`*[Message from Kalai Safaris Website]*\n\n${message}`)}`;
}

export type NavLink = { label: string; href: string; detail?: string };
export type NavItem = NavLink | { label: string; children: NavLink[]; overview: NavLink };

// The three river cruises, grouped under one "Cruises" menu in the header.
export const CRUISE_LINKS: NavLink[] = [
  { label: 'Sunrise cruise', href: '/#sunrise', detail: '06:00 – 08:00' },
  { label: 'Lunch cruise', href: '/#lunch', detail: '12:00 – 14:00' },
  { label: 'Sunset cruise', href: '/#sunset', detail: '16:00 – after sunset' },
];

export const NAV: NavItem[] = [
  { label: 'About', href: '/about' },
  { label: 'Cruises', children: CRUISE_LINKS, overview: { label: 'Compare all cruises', href: '/#cruises' } },
  { label: 'Jetty venue', href: '/#jetty' },
  { label: 'Gallery', href: '/gallery' },
  { label: 'Contact', href: '#contact' },
];

/** Flat list of every nav destination, for places without dropdowns (e.g. the footer). */
export const NAV_LINKS: NavLink[] = NAV.flatMap((item) => ('children' in item ? item.children : [item]));
