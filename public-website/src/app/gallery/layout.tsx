import { pageMetadata } from '@/lib/seo';

export const metadata = pageMetadata(
  'Gallery',
  'Photos from our Zambezi River cruises above Victoria Falls — wildlife, sunsets, our boats and the riverside jetty.',
  '/gallery',
);

export default function GalleryLayout({ children }: { children: React.ReactNode }) {
  return children;
}
