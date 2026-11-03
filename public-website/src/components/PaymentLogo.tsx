import Image from 'next/image';

/**
 * Official payment brand marks, served from /public/images/payments.
 * See public/images/payments/README.md for sources and usage rules.
 *
 * EcoCash and Omari sit on a fixed backing (white for EcoCash's full-colour
 * wordmark, Omari green for Omari's reversed wordmark) so they read the same
 * on light and dark surfaces. ZimSwitch's artwork is already a self-contained
 * yellow badge, so it is drawn as-is at the full badge height.
 * Never recolour, stretch or crop the artwork itself.
 */
export type PaymentBrand = 'ecocash' | 'omari' | 'zimswitch';

type Mark = {
  src: string;
  alt: string;
  width: number;
  height: number;
  /** Backing chip classes; null when the artwork carries its own plate. */
  backing: string | null;
};

const MARKS: Record<PaymentBrand, Mark> = {
  ecocash: { src: '/images/payments/ecocash.webp', alt: 'EcoCash', width: 523, height: 96, backing: 'bg-white ring-1 ring-black/10' },
  omari: { src: '/images/payments/omari-white.webp', alt: 'Omari', width: 311, height: 96, backing: 'bg-[#1A9C68]' },
  zimswitch: { src: '/images/payments/zimswitch.svg', alt: 'ZimSwitch', width: 117, height: 58, backing: null },
};

// Badge height, inner clear space and logo height per size. In a container
// narrower than the badge the logo scales down without distortion.
const SIZES = {
  sm: { height: 'h-7', pad: 'px-2.5', logo: 'h-3.5' },
  md: { height: 'h-8', pad: 'px-3', logo: 'h-4' },
} as const;

export function PaymentLogo({
  brand,
  size = 'md',
  className = '',
  decorative = false,
  bare = false,
}: {
  brand: PaymentBrand;
  size?: keyof typeof SIZES;
  className?: string;
  /** Set when an adjacent label already names the brand. */
  decorative?: boolean;
  /**
   * Drop the backing chip. Only honoured for EcoCash on an already white or
   * near-white surface, where the chip would just steal width from the wordmark.
   */
  bare?: boolean;
}) {
  const mark = MARKS[brand];
  const s = SIZES[size];
  const selfPlated = mark.backing === null;
  const chip = selfPlated || (bare && brand === 'ecocash') ? '' : `${mark.backing} ${s.pad}`;
  return (
    <span className={`inline-flex min-w-0 max-w-full items-center justify-center rounded-md ${s.height} ${chip} ${className}`}>
      <Image
        src={mark.src}
        alt={decorative ? '' : mark.alt}
        width={mark.width}
        height={mark.height}
        unoptimized
        className={`${selfPlated ? 'h-full' : s.logo} w-auto max-w-full object-contain`}
      />
    </span>
  );
}
