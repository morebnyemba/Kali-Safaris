import { OG_CONTENT_TYPE, OG_SIZE, renderOgCard } from './_og/card';

export const alt = 'Kalai Safaris — Zambezi River cruises above Victoria Falls';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return renderOgCard({
    eyebrow: 'Victoria Falls · Zimbabwe',
    title: 'Zambezi River cruises above Victoria Falls',
    footer: 'Sunrise · Lunch · Sunset cruises',
    photo: 'images/Kalai Sunset background shot.jpeg',
    focus: '50% 55%',
  });
}
