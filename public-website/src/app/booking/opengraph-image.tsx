import { OG_CONTENT_TYPE, OG_SIZE, renderOgCard } from '../_og/card';

export const alt = 'Book a Kalai Safaris cruise online';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return renderOgCard({
    eyebrow: 'Book online',
    title: 'Reserve your Zambezi cruise',
    footer: 'Pay by card or mobile money',
    photo: 'images/Kalai Safaris interior chairs.jpeg',
    focus: '50% 55%',
  });
}
