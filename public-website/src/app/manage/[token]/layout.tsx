import type { Metadata } from 'next';

// Private, per-booking page: never indexed, and the token in the URL is never
// sent onward as a Referer.
export const metadata: Metadata = {
  title: 'Manage your booking | Kalai Safaris',
  description: 'Upload traveller IDs and pay your balance securely.',
  robots: { index: false, follow: false, nocache: true },
  referrer: 'no-referrer',
};

export default function ManageLayout({ children }: { children: React.ReactNode }) {
  return children;
}
