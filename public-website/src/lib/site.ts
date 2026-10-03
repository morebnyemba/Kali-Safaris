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

export const NAV_LINKS = [
  { label: 'About', href: '/about' },
  { label: 'Prices', href: '/#prices' },
  { label: 'Sunrise', href: '/#sunrise' },
  { label: 'Lunch', href: '/#lunch' },
  { label: 'Sunset', href: '/#sunset' },
  { label: 'Jetty venue', href: '/#jetty' },
  { label: 'Gallery', href: '/gallery' },
  { label: 'Contact', href: '#contact' },
];
