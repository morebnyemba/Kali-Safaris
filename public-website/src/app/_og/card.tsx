import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ImageResponse } from 'next/og';

// Link-preview cards, rendered once at build time by each route's
// opengraph-image.tsx. Everything that matters sits in the centre 630px so it
// survives WhatsApp's square thumbnail crop as well as the 1.91:1 Facebook /
// X / LinkedIn / iMessage preview.

export const OG_SIZE = { width: 1200, height: 630 };
// JPEG, not next/og's PNG: a photo card is ~1.2MB as PNG, and WhatsApp drops
// preview images much over ~300KB. Converted once at build, so no runtime cost.
export const OG_CONTENT_TYPE = 'image/jpeg';

const root = process.cwd();
const asset = (...parts: string[]) => readFile(join(root, ...parts));

async function dataUri(publicPath: string) {
  const buf = await asset('public', publicPath);
  const mime = publicPath.endsWith('.png') ? 'image/png' : 'image/jpeg';
  return `data:${mime};base64,${buf.toString('base64')}`;
}

interface Card {
  eyebrow: string;
  title: string;
  footer: string;
  /** Path under /public. Use photos ≥1000px wide or they look soft when shared. */
  photo: string;
  /** CSS object-position for the photo, e.g. '50% 60%'. */
  focus?: string;
}

export async function renderOgCard({ eyebrow, title, footer, photo, focus = '50% 50%' }: Card) {
  const [bg, mark, medium, bold] = await Promise.all([
    dataUri(photo),
    dataUri('images/kalailogo-leftmark.png'),
    asset('src/app/_og/fonts/Outfit-500.ttf'),
    asset('src/app/_og/fonts/Outfit-800.ttf'),
  ]);

  const png = new ImageResponse(
    (
      <div style={{ width: '100%', height: '100%', display: 'flex', position: 'relative', fontFamily: 'Outfit', background: '#0A0A0A' }}>
        {/* eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text */}
        <img src={bg} width={1200} height={630} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', objectFit: 'cover', objectPosition: focus }} />
        <div
          style={{
            position: 'absolute',
            top: 0, left: 0, width: '100%', height: '100%',
            background: 'linear-gradient(180deg, rgba(10,10,10,0.4) 0%, rgba(10,10,10,0.12) 30%, rgba(10,10,10,0.3) 70%, rgba(10,10,10,0.8) 100%)',
          }}
        />
        {/* Extra scrim behind the headline so it reads on bright sunsets and busy photos. */}
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', background: 'radial-gradient(ellipse 560px 240px at 50% 50%, rgba(10,10,10,0.6), rgba(10,10,10,0))' }} />
        {/* Brand stripe */}
        <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 10, display: 'flex', background: 'linear-gradient(90deg, #C8102E, #E8600A, #E09A18)' }} />

        <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%', padding: '44px 0 56px' }}>
          {/* Logo lockup */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ width: 76, height: 76, borderRadius: 999, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {/* eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text */}
              <img src={mark} width={60} height={29} />
            </div>
            <div style={{ display: 'flex', fontSize: 30, fontWeight: 800, color: '#fff', letterSpacing: 4 }}>KALAI SAFARIS</div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', width: 560 }}>
            <div style={{ display: 'flex', padding: '7px 18px', borderRadius: 999, background: '#C8102E', fontSize: 19, fontWeight: 800, color: '#fff', letterSpacing: 3, textTransform: 'uppercase' }}>{eyebrow}</div>
            <div
              style={{
                display: 'flex',
                marginTop: 18,
                fontSize: 58,
                fontWeight: 800,
                lineHeight: 1.05,
                letterSpacing: -1.5,
                color: '#fff',
                textAlign: 'center',
                justifyContent: 'center',
                textShadow: '0 2px 18px rgba(0,0,0,0.75)',
              }}
            >
              {title}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 21, fontWeight: 500, color: 'rgba(255,255,255,0.9)' }}>
            <span>{footer}</span>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: '#E8600A' }} />
            <span style={{ fontWeight: 800, color: '#fff' }}>kalaisafaris.com</span>
          </div>
        </div>
      </div>
    ),
    {
      ...OG_SIZE,
      fonts: [
        { name: 'Outfit', data: medium, weight: 500, style: 'normal' },
        { name: 'Outfit', data: bold, weight: 800, style: 'normal' },
      ],
    },
  );

  const sharp = (await import('sharp')).default;
  const jpeg = await sharp(Buffer.from(await png.arrayBuffer())).jpeg({ quality: 82, mozjpeg: true }).toBuffer();
  return new Response(new Uint8Array(jpeg), {
    headers: { 'Content-Type': OG_CONTENT_TYPE },
  });
}
