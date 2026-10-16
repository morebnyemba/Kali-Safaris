import { OG_CONTENT_TYPE, OG_SIZE, renderOgCard } from '../_og/card';

export const alt = 'About Kalai Safaris';
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default function Image() {
  return renderOgCard({
    eyebrow: 'About us',
    title: '“Kalai” — the cry of the fish eagle',
    footer: 'Boating safaris since 2019',
    photo: 'images/kalai_intro.jpeg',
    focus: '50% 90%',
  });
}
