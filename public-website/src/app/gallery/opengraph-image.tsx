import { OG_CONTENT_TYPE, OG_SIZE, renderOgCard } from '../_og/card';

export const alt = 'Kalai Safaris photo gallery';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return renderOgCard({
    eyebrow: 'Gallery',
    title: 'Life on the Zambezi',
    footer: 'Wildlife, sunsets and our boats',
    photo: 'images/slider/hipo.jpg',
    focus: '60% 40%',
  });
}
