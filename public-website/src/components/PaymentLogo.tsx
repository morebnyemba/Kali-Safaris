import Image from 'next/image';

/**
 * Official payment brand marks, served from /public/images/payments.
 * See public/images/payments/README.md for sources and usage rules.
 *
 * EcoCash, Omari, Visa and Mastercard are full-colour marks made for light
 * backgrounds, so they sit on a white chip and read the same on light and dark
 * surfaces. ZimSwitch's artwork is already a self-contained yellow badge, so it
 * is drawn as-is at the full badge height.
 * Never recolour, stretch or crop the artwork itself.
 */
export type PaymentBrand = 'ecocash' | 'omari' | 'zimswitch' | 'visa' | 'mastercard';

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
  omari: { src: '/images/payments/omari.webp', alt: 'Omari', width: 307, height: 96, backing: 'bg-white ring-1 ring-black/10' },
  zimswitch: { src: '/images/payments/zimswitch.svg', alt: 'ZimSwitch', width: 117, height: 58, backing: null },
  // Visa Blue wordmark: always on white.
  visa: { src: '/images/payments/visa.webp', alt: 'Visa', width: 296, height: 96, backing: 'bg-white ring-1 ring-black/10' },
  mastercard: { src: '/images/payments/mastercard.webp', alt: 'Mastercard', width: 154, height: 96, backing: 'bg-white ring-1 ring-black/10' },
};

/**
 * Order the client set for every list of payment methods: mobile money first,
 * then ZimSwitch, then (once live) InnBucks, then the international cards.
 */
export const PAYMENT_LOGO_ORDER: PaymentBrand[] = ['ecocash', 'omari', 'zimswitch', 'visa', 'mastercard'];

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
   * Drop the backing chip on an already white or near-white surface, where it
   * would just steal width from the mark. Ignored for ZimSwitch's own plate.
   */
  bare?: boolean;
}) {
  const mark = MARKS[brand];
  const s = SIZES[size];
  const selfPlated = mark.backing === null;
  const chip = selfPlated || bare ? '' : `${mark.backing} ${s.pad}`;
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
