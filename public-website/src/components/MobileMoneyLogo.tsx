import Image from 'next/image';

/**
 * Official mobile money operator marks, served from /public/images/payments.
 * See public/images/payments/README.md for sources and usage rules.
 *
 * Each mark sits on a fixed backing (white for EcoCash's full-colour wordmark,
 * Omari green for Omari's reversed wordmark) so it reads the same on light and
 * dark surfaces. Never recolour, stretch or crop the artwork itself.
 */
export type MobileMoneyOperator = 'ecocash' | 'omari';

const MARKS: Record<MobileMoneyOperator, { src: string; alt: string; width: number; height: number; backing: string }> = {
  ecocash: { src: '/images/payments/ecocash.webp', alt: 'EcoCash', width: 523, height: 96, backing: 'bg-white ring-1 ring-black/10' },
  omari: { src: '/images/payments/omari-white.webp', alt: 'Omari', width: 311, height: 96, backing: 'bg-[#1A9C68]' },
};

// Badge height, inner clear space and logo height per size. In a container
// narrower than the badge the logo scales down without distortion.
const SIZES = {
  sm: { height: 'h-7', pad: 'px-2.5', logo: 'h-3.5' },
  md: { height: 'h-8', pad: 'px-3', logo: 'h-4' },
} as const;

export function MobileMoneyLogo({
  operator,
  size = 'md',
  className = '',
  decorative = false,
  bare = false,
}: {
  operator: MobileMoneyOperator;
  size?: keyof typeof SIZES;
  className?: string;
  /** Set when an adjacent label already names the operator. */
  decorative?: boolean;
  /**
   * Drop the backing chip. Only valid for EcoCash on an already white/near-white
   * surface, where the chip would just steal width from the wordmark.
   */
  bare?: boolean;
}) {
  const mark = MARKS[operator];
  const s = SIZES[size];
  const chip = bare && operator === 'ecocash' ? '' : `${mark.backing} ${s.pad}`;
  return (
    <span className={`inline-flex min-w-0 max-w-full items-center justify-center rounded-md ${s.height} ${chip} ${className}`}>
      <Image
        src={mark.src}
        alt={decorative ? '' : mark.alt}
        width={mark.width}
        height={mark.height}
        unoptimized
        className={`${s.logo} w-auto max-w-full object-contain`}
      />
    </span>
  );
}
