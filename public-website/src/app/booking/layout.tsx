import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata(
  'Book a cruise',
  'Book a sunrise, lunch or sunset cruise on the Zambezi above Victoria Falls. Pay securely online by card or mobile money.',
  '/booking',
);

export default function BookingLayout({ children }: { children: React.ReactNode }) {
  return children;
}
