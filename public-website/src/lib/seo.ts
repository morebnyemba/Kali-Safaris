import type { Metadata } from 'next';

export const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://kalaisafaris.com';

/**
 * Per-page title/description for search results AND link previews. A child
 * `openGraph` object replaces the parent's rather than merging, so siteName,
 * type and locale are repeated here. The preview image comes from the route's
 * opengraph-image.tsx, which Next adds on top of this.
 */
export function pageMetadata(title: string, description: string, path: string): Metadata {
  const shareTitle = `${title} | Kalai Safaris`;
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: { type: 'website', siteName: 'Kalai Safaris', locale: 'en_GB', url: path, title: shareTitle, description },
    twitter: { card: 'summary_large_image', title: shareTitle, description },
  };
}
